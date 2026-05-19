import json
import os
import tempfile
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

load_dotenv(Path(__file__).parent / ".env")

from agent.tools import read_dynamic_config, transcribe_audio_with_speechmatics
from agent.wallet import get_or_create_wallet
from agent.workflow import build_reflection_workflow, build_workflow

app = FastAPI(title="xRegime Oracle API")

# ---------- shared in-memory state ----------
_state = {
    "trade_log": [],
    "regime_score": 50.0,
    "last_flight_log": [],
}


def _build_initial(text: str) -> dict:
    return {
        "input_text": text,
        "documents": [],
        "extracted_signals": {},
        "analysis_results": {},
        "backtest_results": {},
        "execution_plan": None,
        "execution_output": None,
        "execution_ok": None,
        "status": "init",
        "trade_log": _state["trade_log"],
        "regime_score": _state["regime_score"],
        "proposed_rule_changes": [],
        "active_rules": read_dynamic_config(),
        "flight_log": [],
    }


# ---------- routes ----------
@app.get("/api/state")
def get_state():
    trade_log = _state["trade_log"]
    wins = sum(1 for t in trade_log if float(t.get("pnl", 0) or 0) > 0)
    win_rate = round(wins / len(trade_log) * 100, 1) if trade_log else 0
    return {
        "regime_score": _state["regime_score"],
        "win_rate": win_rate,
        "trade_count": len(trade_log),
        "trade_log": trade_log[-20:],
        "flight_log": _state["last_flight_log"],
        "active_rules": read_dynamic_config(),
        "identity": get_or_create_wallet(),
    }


@app.post("/api/execute")
async def execute(text: str = Form("")):
    def stream():
        workflow = build_workflow()
        try:
            for event in workflow.stream(_build_initial(text)):
                for _, value in event.items():
                    _state["trade_log"] = value.get("trade_log", _state["trade_log"])
                    _state["last_flight_log"] = value.get("flight_log", _state["last_flight_log"])
                    payload = json.dumps({"status": value.get("status", ""), "value": value})
                    yield f"data: {payload}\n\n"
                    time.sleep(0.05)
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    suffix = Path(audio.filename).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name
    try:
        text = transcribe_audio_with_speechmatics(tmp_path)
        return {"transcript": text}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        os.unlink(tmp_path)


@app.post("/api/reflect")
def reflect():
    workflow = build_reflection_workflow()
    for event in workflow.stream(_build_initial("")):
        for _, value in event.items():
            if value.get("status") == "regime_calculated":
                _state["regime_score"] = value.get("regime_score", _state["regime_score"])
            _state["last_flight_log"] = value.get("flight_log", _state["last_flight_log"])
    return {"ok": True, "regime_score": _state["regime_score"]}


# ---------- static (must come last) ----------
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
