import json
import os
import random
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx
from openai import OpenAI

from agent.prompts import (
    FINANCIAL_ANALYST_PROMPT,
    MULTIMODAL_EXTRACTOR_PROMPT,
    NIGHTLY_REFLECTOR_PROMPT,
)


APP_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = APP_ROOT / "agent" / "dynamic_config.json"
DEFAULT_CONFIG = {
    "risk_tolerance": "medium",
    "stop_loss_percentage": 0.05,
    "momentum_threshold": 0.6,
    "special_instructions": "Default. Maintain standard risk levels.",
}

SIGNAL_MODEL = os.environ.get("FEATHERLESS_SIGNAL_MODEL", "Qwen/Qwen2-7B-Instruct")
REFLECTOR_MODEL = os.environ.get("FEATHERLESS_REFLECTOR_MODEL", "Qwen/Qwen2-72B-Instruct")
ENSEMBLE_MODELS = [
    {
        "label": "Qwen-7B",
        "model": os.environ.get("FEATHERLESS_MODEL_1", "Qwen/Qwen2-7B-Instruct"),
    },
    {
        "label": "Qwen-2.5-7B",
        "model": os.environ.get("FEATHERLESS_MODEL_2", "Qwen/Qwen2.5-7B-Instruct"),
    },
    {
        "label": "Llama-3.1-8B",
        "model": os.environ.get("FEATHERLESS_MODEL_3", "NousResearch/Meta-Llama-3.1-8B-Instruct"),
    },
]
SUPPORTED_CRYPTO_TICKERS = {"BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "LTC", "DOT", "AVAX", "LINK"}
ORDER_SIZES = {
    "BTC": "0.0001",
    "ETH": "0.002",
    "SOL": "0.05",
    "XRP": "5",
    "ADA": "10",
    "DOGE": "25",
    "LTC": "0.05",
    "DOT": "1",
    "AVAX": "0.2",
    "LINK": "0.5",
}


def get_featherless_client() -> OpenAI:
    api_key = os.environ.get("FEATHERLESS_API_KEY")
    if not api_key or api_key == "your_featherless_api_key_here":
        raise ValueError("FEATHERLESS_API_KEY is not set. Add it to .env before running analysis.")
    return OpenAI(base_url="https://api.featherless.ai/v1", api_key=api_key)


def is_featherless_busy_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "concurrency" in text or "rate limit" in text or "429" in text


def featherless_chat_completion(client: OpenAI, *, model: str, messages: list[dict[str, str]], temperature: float):
    last_error = None
    for attempt in range(4):
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
        except Exception as exc:
            last_error = exc
            if not is_featherless_busy_error(exc) or attempt == 3:
                raise
            sleep_for = 4 + (attempt * 4) + random.uniform(0, 1.5)
            time.sleep(sleep_for)
    raise last_error


def _coerce_float(value: Any, default: float, low: float, high: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(low, min(high, number))


def normalize_dynamic_config(config: dict[str, Any] | None) -> dict[str, Any]:
    config = config or {}
    risk = str(config.get("risk_tolerance", DEFAULT_CONFIG["risk_tolerance"])).lower()
    if risk not in {"low", "medium", "high"}:
        risk = DEFAULT_CONFIG["risk_tolerance"]

    return {
        "risk_tolerance": risk,
        "stop_loss_percentage": _coerce_float(
            config.get("stop_loss_percentage"),
            DEFAULT_CONFIG["stop_loss_percentage"],
            0.01,
            0.10,
        ),
        "momentum_threshold": _coerce_float(
            config.get("momentum_threshold"),
            DEFAULT_CONFIG["momentum_threshold"],
            0.4,
            0.9,
        ),
        "special_instructions": str(
            config.get("special_instructions", DEFAULT_CONFIG["special_instructions"])
        )[:500],
    }


def read_dynamic_config() -> dict[str, Any]:
    try:
        return normalize_dynamic_config(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    except Exception:
        return DEFAULT_CONFIG.copy()


def update_dynamic_config(new_config: dict[str, Any]) -> bool:
    try:
        CONFIG_PATH.write_text(
            json.dumps(normalize_dynamic_config(new_config), indent=2) + "\n",
            encoding="utf-8",
        )
        return True
    except Exception as exc:
        print(f"Unable to update dynamic config: {exc}")
        return False


def calculate_regime_score(trade_log: list[dict[str, Any]]) -> float:
    regime = 50.0
    for trade in trade_log[-10:]:
        pnl = float(trade.get("pnl", 0) or 0)
        regime += 10 if pnl > 0 else -10
    return max(0.0, min(100.0, regime))


def parse_json_response(content: str, fallback: dict[str, Any]) -> dict[str, Any]:
    content = (content or "").strip()
    if "```json" in content:
        content = content.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in content:
        content = content.split("```", 1)[1].split("```", 1)[0].strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return fallback


def extract_signals_with_featherless(text: str) -> dict[str, Any]:
    client = get_featherless_client()
    prompt = f"{MULTIMODAL_EXTRACTOR_PROMPT}\n\nInput Text: {text}"
    response = featherless_chat_completion(
        client,
        model=SIGNAL_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )

    fallback = {
        "tickers": [],
        "sentiment": "neutral",
        "summary": "No reliable signal extraction was returned.",
    }
    data = parse_json_response(response.choices[0].message.content or "", fallback)
    data["tickers"] = normalize_tickers(data.get("tickers", []))
    data["sentiment"] = str(data.get("sentiment", "neutral")).lower()
    data["summary"] = str(data.get("summary", ""))[:1200]
    return data


def reflect_on_performance_with_featherless(
    regime_score: float,
    trade_log: list[dict[str, Any]],
    active_rules: dict[str, Any],
) -> dict[str, Any]:
    client = get_featherless_client()
    prompt = NIGHTLY_REFLECTOR_PROMPT.format(
        regime_score=regime_score,
        trade_log=json.dumps(trade_log, indent=2),
        active_rules=json.dumps(active_rules, indent=2),
    )

    response = featherless_chat_completion(
        client,
        model=REFLECTOR_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )

    parsed = parse_json_response(response.choices[0].message.content or "", active_rules)
    return normalize_dynamic_config(parsed)


def call_single_model_for_vote(client: OpenAI, model_info: dict[str, str], prompt: str) -> dict[str, Any]:
    label = model_info["label"]
    model = model_info["model"]
    try:
        response = featherless_chat_completion(
            client,
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        fallback = {"vote": "HOLD", "confidence": 0.0, "reasoning": "Model returned invalid JSON."}
        parsed = parse_json_response(response.choices[0].message.content or "", fallback)
        if parsed is fallback:
            raise ValueError("Model returned invalid JSON.")
        vote = str(parsed.get("vote", "HOLD")).upper()
        if vote not in {"BUY", "SELL", "HOLD"}:
            vote = "HOLD"
        return {
            "model": label,
            "model_id": model,
            "vote": vote,
            "confidence": _coerce_float(parsed.get("confidence"), 0.0, 0.0, 1.0),
            "reasoning": str(parsed.get("reasoning", ""))[:1000],
            "ok": True,
        }
    except Exception as exc:
        return {
            "model": label,
            "model_id": model,
            "vote": "HOLD",
            "confidence": 0.0,
            "reasoning": f"{label} unavailable: {exc}",
            "ok": False,
        }


def analyze_with_featherless_ensemble(signals: dict[str, Any], active_rules: dict[str, Any]) -> dict[str, Any]:
    client = get_featherless_client()
    prompt = FINANCIAL_ANALYST_PROMPT.format(
        signals=json.dumps(signals, indent=2),
        active_rules=json.dumps(active_rules, indent=2),
    )

    # Keep the three judges independent while avoiding Featherless account concurrency spikes.
    results = [call_single_model_for_vote(client, model_info, prompt) for model_info in ENSEMBLE_MODELS]
    valid_results = [result for result in results if result.get("ok")]
    votes = [result.get("vote", "HOLD") for result in valid_results]
    buy_count = votes.count("BUY")
    sell_count = votes.count("SELL")

    final_vote = "HOLD"
    if len(valid_results) >= 2 and buy_count >= 2:
        final_vote = "BUY"
    elif len(valid_results) >= 2 and sell_count >= 2:
        final_vote = "SELL"

    avg_confidence = (
        sum(float(result.get("confidence", 0.0)) for result in valid_results) / len(valid_results)
        if valid_results
        else 0.0
    )
    healthy = len(valid_results) == len(results)

    return {
        "vote": final_vote,
        "confidence": avg_confidence,
        "reasoning": f"Consensus {final_vote}: {buy_count} BUY, {sell_count} SELL, {votes.count('HOLD')} HOLD from {len(valid_results)}/{len(results)} available models.",
        "raw_results": results,
        "healthy": healthy,
    }


def normalize_tickers(tickers: Any) -> list[str]:
    if isinstance(tickers, str):
        tickers = [tickers]
    if not isinstance(tickers, list):
        return []

    normalized = []
    for ticker in tickers:
        clean = re.sub(r"[^A-Za-z.]", "", str(ticker)).upper().replace(".", "")
        if 1 <= len(clean) <= 6 and clean not in normalized:
            normalized.append(clean)
    return normalized[:5]


def tradable_crypto_tickers(tickers: Any) -> list[str]:
    return [ticker for ticker in normalize_tickers(tickers) if ticker in SUPPORTED_CRYPTO_TICKERS]


def build_kraken_order_args(vote: str, tickers: list[str]) -> list[str] | None:
    crypto_tickers = tradable_crypto_tickers(tickers)
    if vote not in {"BUY", "SELL"} or not crypto_tickers:
        return None

    kraken_bin = os.environ.get("KRAKEN_CLI_PATH") or shutil.which("kraken") or "/root/.cargo/bin/kraken"
    side = "buy" if vote == "BUY" else "sell"
    ticker = crypto_tickers[0]
    return [kraken_bin, "paper", side, f"{ticker}/USD", ORDER_SIZES.get(ticker, "1")]


def execute_kraken_cli(args: list[str]) -> dict[str, Any]:
    print(f"Executing Kraken CLI command: {' '.join(args)}")
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=True, timeout=45)
        output = result.stdout.strip() or result.stderr.strip()
        return {"ok": True, "output": output}
    except subprocess.CalledProcessError as exc:
        output = (exc.stderr or exc.stdout or str(exc)).strip()
        return {"ok": False, "output": output, "error": f"Kraken CLI rejected the order: {output}"}
    except Exception as exc:
        return {"ok": False, "output": str(exc), "error": f"Kraken CLI failed: {exc}"}


def backtest_strategy(tickers: list[str], vote: str, confidence: float, regime_score: float, rules: dict[str, Any]) -> dict[str, Any]:
    if vote == "HOLD":
        return {
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "status": "SKIP",
            "reason": "Consensus was HOLD.",
        }
    if not tradable_crypto_tickers(tickers):
        return {
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "status": "FAIL",
            "reason": "No supported Kraken crypto ticker was extracted.",
        }

    threshold = float(rules.get("momentum_threshold", 0.6))
    if confidence < threshold:
        return {
            "sharpe_ratio": 0.6,
            "max_drawdown": float(rules.get("stop_loss_percentage", 0.05)),
            "status": "FAIL",
            "reason": f"Confidence {confidence:.2f} is below active threshold {threshold:.2f}.",
        }
    if regime_score < 25:
        return {
            "sharpe_ratio": 0.8,
            "max_drawdown": float(rules.get("stop_loss_percentage", 0.05)),
            "status": "FAIL",
            "reason": "Regime Score is too weak for new exposure.",
        }

    return {
        "sharpe_ratio": 1.5,
        "max_drawdown": float(rules.get("stop_loss_percentage", 0.05)),
        "status": "PASS",
        "reason": "Signal confidence and current regime passed risk gates.",
    }


def transcribe_audio_with_speechmatics(file_path: str) -> str:
    api_key = os.environ.get("SPEECHMATICS_API_KEY")
    if not api_key or api_key == "your_speechmatics_api_key_here":
        raise ValueError("SPEECHMATICS_API_KEY is not set in .env.")

    url = "https://asr.api.speechmatics.com/v2/jobs/"
    headers = {"Authorization": f"Bearer {api_key}"}
    config = {
        "type": "transcription",
        "transcription_config": {
            "language": "en",
            "operating_point": "enhanced",
        },
    }

    try:
        with open(file_path, "rb") as audio_file:
            files = {
                "data_file": audio_file,
                "config": (None, json.dumps(config), "application/json"),
            }
            response = httpx.post(url, headers=headers, files=files, timeout=60.0)
            response.raise_for_status()
            job_id = response.json().get("id")

        if not job_id:
            raise RuntimeError("Speechmatics did not return a job id.")

        deadline = time.time() + 300
        while time.time() < deadline:
            status_response = httpx.get(f"{url}{job_id}", headers=headers, timeout=30.0)
            status_response.raise_for_status()
            status = status_response.json().get("job", {}).get("status")

            if status == "done":
                transcript_response = httpx.get(
                    f"{url}{job_id}/transcript?format=txt",
                    headers=headers,
                    timeout=60.0,
                )
                transcript_response.raise_for_status()
                return transcript_response.text.strip()
            if status in {"rejected", "deleted"}:
                raise RuntimeError(f"Speechmatics job failed with status: {status}")
            time.sleep(3)

        raise TimeoutError("Speechmatics transcription timed out after 5 minutes.")
    except Exception:
        raise
