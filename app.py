import hashlib
import html
import os
import tempfile
import time
from pathlib import Path

import pandas as pd
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from dotenv import load_dotenv

from agent.tools import read_dynamic_config, transcribe_audio_with_speechmatics
from agent.wallet import get_or_create_wallet
from agent.workflow import build_reflection_workflow, build_workflow


APP_ROOT = Path(__file__).resolve().parent
load_dotenv(APP_ROOT / ".env")

st.set_page_config(page_title="xRegime Oracle", page_icon=":chart_with_upwards_trend:", layout="wide", initial_sidebar_state="collapsed")

CRYPTO_SAMPLE = (
    "BTC broke above a key resistance level after ETF inflows accelerated. "
    "Momentum remains positive, volatility is elevated, and traders are watching "
    "whether spot demand can hold into the next session."
)


def init_session() -> None:
    defaults = {
        "trade_log": [],
        "regime_score": 50.0,
        "last_flight_log": [],
        "last_result": "No analysis has run yet.",
        "chat_messages": [],
        "market_brief": "",
        "last_voice_transcript": "",
        "last_processed_recorded_voice": "",
        "last_processed_uploaded_voice": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if "Error code: 429" in str(st.session_state.last_result) or "concurrency_limit_exceeded" in str(st.session_state.last_result):
        st.session_state.last_result = "Featherless was busy on the previous run. Wait a few seconds and run the brief again."


def render_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                linear-gradient(rgba(255,255,255,.018) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,.018) 1px, transparent 1px),
                radial-gradient(circle at 12% 0%, rgba(20, 184, 166, .18), transparent 28rem),
                radial-gradient(circle at 88% 10%, rgba(245, 158, 11, .12), transparent 26rem),
                linear-gradient(180deg, #0a0d12 0%, #111827 48%, #0a0d12 100%);
            background-size: auto, 28px 28px, auto, auto, auto;
        }
        h1, h2, h3 { letter-spacing: 0; }
        div[data-testid="stSidebar"] { background: #0d1117; }
        .hero {
            border: 1px solid rgba(148,163,184,.20);
            border-radius: 8px;
            padding: 22px 24px;
            background:
                linear-gradient(135deg, rgba(20,184,166,.14), transparent 38%),
                rgba(10,13,18,.90);
            margin-bottom: 14px;
            box-shadow: 0 18px 60px rgba(0,0,0,.30);
        }
        .hero-title {
            font-size: 2.25rem;
            font-weight: 780;
            line-height: 1.05;
            margin: 0 0 8px 0;
            color: #f8fafc;
        }
        .hero-subtitle {
            color: #cbd5e1;
            max-width: 980px;
            margin: 0;
            font-size: 1rem;
        }
        .pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 14px;
        }
        .pill {
            border-radius: 999px;
            padding: 5px 11px;
            border: 1px solid rgba(148,163,184,.25);
            background: rgba(31,41,55,.72);
            color: #e5e7eb;
            font-size: .82rem;
        }
        .metric-card {
            min-height: 110px;
            border-radius: 8px;
            border: 1px solid rgba(148,163,184,.18);
            border-left: 4px solid var(--accent);
            background: rgba(17,24,39,.84);
            padding: 14px 16px;
        }
        .metric-label { color: #9ca3af; font-size: .78rem; text-transform: uppercase; }
        .metric-value { color: #f9fafb; font-size: 1.55rem; font-weight: 750; margin-top: 8px; overflow-wrap: anywhere; }
        .metric-detail { color: #d1d5db; font-size: .86rem; margin-top: 6px; overflow-wrap: anywhere; }
        .section-note { color: #9ca3af; font-size: .9rem; margin-top: -8px; }
        .command-heading {
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: 16px;
            margin-top: 18px;
        }
        .command-heading h3 {
            margin-bottom: 4px;
        }
        .pilot-rail {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 10px;
            margin: 14px 0 18px;
        }
        .pilot-step {
            border: 1px solid rgba(148,163,184,.18);
            border-radius: 8px;
            padding: 12px 14px;
            background: rgba(17,24,39,.78);
        }
        .pilot-step b {
            display: block;
            color: #f8fafc;
            margin-bottom: 4px;
        }
        .pilot-step span {
            color: #a7f3d0;
            font-size: .82rem;
            text-transform: uppercase;
            letter-spacing: .04em;
        }
        .control-shell {
            border: 1px solid rgba(148,163,184,.22);
            border-radius: 8px;
            padding: 16px 18px 18px;
            background:
                linear-gradient(180deg, rgba(15,23,42,.86), rgba(15,23,42,.70));
            box-shadow: inset 0 1px 0 rgba(255,255,255,.05);
        }
        .panel-kicker {
            color: #5eead4;
            font-size: .76rem;
            text-transform: uppercase;
            letter-spacing: .08em;
            margin-bottom: 6px;
        }
        .panel-title {
            color: #f8fafc;
            font-weight: 750;
            font-size: 1.15rem;
            margin-bottom: 8px;
        }
        .result-card {
            border-radius: 8px;
            border: 1px solid rgba(148,163,184,.22);
            padding: 16px 18px;
            min-height: 260px;
            background: rgba(10,13,18,.88);
        }
        .result-card.executed { border-color: rgba(34,197,94,.55); box-shadow: 0 0 0 1px rgba(34,197,94,.08), 0 18px 60px rgba(34,197,94,.08); }
        .result-card.hold { border-color: rgba(245,158,11,.50); }
        .result-card.error { border-color: rgba(239,68,68,.55); }
        .verdict {
            font-size: 1.75rem;
            line-height: 1.1;
            font-weight: 800;
            margin: 6px 0 10px;
            color: #f8fafc;
        }
        .verdict-detail { color: #cbd5e1; line-height: 1.5; overflow-wrap: anywhere; }
        .asset-row {
            display: flex;
            gap: 7px;
            flex-wrap: wrap;
            margin-top: 8px;
        }
        .asset-chip {
            border-radius: 6px;
            border: 1px solid rgba(148,163,184,.20);
            color: #e5e7eb;
            background: rgba(31,41,55,.70);
            padding: 4px 8px;
            font-size: .82rem;
        }
        .quick-action {
            border: 1px solid rgba(94,234,212,.24);
            border-radius: 8px;
            padding: 12px 14px;
            background: rgba(15,23,42,.74);
            margin: 10px 0 14px;
        }
        .quick-action strong {
            display: block;
            color: #f8fafc;
            margin-bottom: 3px;
        }
        .quick-action span {
            color: #cbd5e1;
            font-size: .9rem;
        }
        .stButton > button {
            min-height: 2.8rem;
            border-radius: 8px;
            font-weight: 700;
        }
        .stTextArea textarea {
            border-radius: 8px;
        }
        @media (max-width: 900px) {
            .pilot-rail { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .hero-title { font-size: 1.75rem; }
            .command-heading { display: block; }
        }
        div[data-testid="stChatMessage"] {
            border-radius: 8px;
            border: 1px solid rgba(148,163,184,.14);
            background: rgba(17,24,39,.76);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def build_initial_state(text: str) -> dict:
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
        "trade_log": st.session_state.trade_log,
        "regime_score": st.session_state.regime_score,
        "proposed_rule_changes": [],
        "active_rules": read_dynamic_config(),
        "flight_log": [],
    }


def uploaded_file_to_text(uploaded_file) -> str:
    if uploaded_file is None:
        return ""

    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".txt":
        return uploaded_file.getvalue().decode("utf-8", errors="replace")
    if suffix in {".wav", ".mp3"}:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        try:
            with st.spinner("Transcribing audio with Speechmatics..."):
                return transcribe_audio_with_speechmatics(tmp_path)
        finally:
            os.unlink(tmp_path)

    return ""


def transcribe_audio_bytes(audio_bytes: bytes, suffix: str) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        with st.spinner("Transcribing voice with Speechmatics..."):
            return transcribe_audio_with_speechmatics(tmp_path)
    finally:
        os.unlink(tmp_path)


def run_agent(text: str, compact: bool = False) -> str:
    workflow = build_workflow()
    final_execution = "NO_ACTION"
    final_execution_ok = True
    final_reasoning = ""
    final_output = ""

    with st.status("Running xRegime Oracle", expanded=not compact) as status:
        try:
            for event in workflow.stream(build_initial_state(text)):
                for _, value in event.items():
                    step_status = value.get("status", "")
                    if step_status == "ingested":
                        st.write("Input captured.")
                    elif step_status == "reasoned":
                        st.write("Crypto signals extracted.")
                        if not compact:
                            st.json(value.get("extracted_signals", {}), expanded=False)
                    elif step_status == "analyzed":
                        analysis = value.get("analysis_results", {})
                        final_reasoning = analysis.get("reasoning", "")
                        health = "3/3 models online" if analysis.get("healthy") else "degraded"
                        st.write(f"Model courtroom complete: {health}.")
                    elif step_status == "backtested":
                        st.write(f"Risk judge: {value.get('backtest_results', {}).get('status', 'UNKNOWN')}.")
                    elif step_status == "executed":
                        final_execution = value.get("execution_plan") or "NO_ACTION"
                        final_execution_ok = bool(value.get("execution_ok", True))
                        final_output = value.get("execution_output") or ""
                        st.session_state.trade_log = value.get("trade_log", st.session_state.trade_log)
                        st.session_state.last_flight_log = value.get("flight_log", [])
                        st.write("Execution step complete.")
                    time.sleep(0.12)
            status.update(label="Run complete", state="complete", expanded=False)
        except Exception as exc:
            status.update(label="Run failed", state="error", expanded=True)
            error_text = str(exc)
            if "concurrency" in error_text.lower() or "429" in error_text:
                st.session_state.last_result = (
                    "Featherless is busy right now. Wait about 20 seconds and run it again. "
                    "The app now retries automatically before showing this message."
                )
            else:
                st.session_state.last_result = f"Error: {error_text[:500]}"
            return st.session_state.last_result

    if final_execution != "NO_ACTION" and final_execution_ok:
        message = f"Executed Kraken paper command: `{final_execution}`"
        if final_output:
            message += f"\n\n```text\n{final_output}\n```"
    elif final_execution != "NO_ACTION":
        message = f"Kraken rejected the paper command: `{final_execution}`"
        if final_output:
            message += f"\n\n```text\n{final_output}\n```"
    else:
        message = "No trade executed. The agent stayed in HOLD / blocked mode."

    if final_reasoning:
        message += f"\n\n{final_reasoning}"
    st.session_state.last_result = message
    return message


def run_reflector() -> None:
    workflow = build_reflection_workflow()
    with st.status("Running Nightly Reflector", expanded=True) as status:
        try:
            for event in workflow.stream(build_initial_state("")):
                for _, value in event.items():
                    step_status = value.get("status", "")
                    if step_status == "regime_calculated":
                        st.session_state.regime_score = value.get("regime_score", st.session_state.regime_score)
                        st.write(f"Regime Score: {st.session_state.regime_score:.1f}.")
                    elif step_status == "reflected":
                        st.write("Reflector proposed updated rules.")
                        st.json(value.get("proposed_rule_changes", [{}])[0], expanded=False)
                        st.session_state.last_flight_log = value.get("flight_log", [])
                    elif step_status == "evolved":
                        st.success("Dynamic rules updated.")
                    elif step_status == "evolution_failed":
                        st.error("Dynamic rules could not be written.")
            status.update(label="Reflection complete", state="complete", expanded=False)
        except Exception as exc:
            status.update(label=f"Reflection failed: {exc}", state="error", expanded=True)


def metric_card(label: str, value: str, detail: str, accent: str) -> str:
    return f"""
    <div class="metric-card" style="--accent:{accent}">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}</div>
      <div class="metric-detail">{detail}</div>
    </div>
    """


def render_pilot_rail() -> None:
    st.markdown(
        """
        <div class="pilot-rail">
          <div class="pilot-step"><span>01 Input</span><b>Speak or paste</b><div class="metric-detail">Voice, upload, or market brief</div></div>
          <div class="pilot-step"><span>02 Courtroom</span><b>3 model vote</b><div class="metric-detail">Consensus before action</div></div>
          <div class="pilot-step"><span>03 Risk Gate</span><b>Regime check</b><div class="metric-detail">Rules approve or block</div></div>
          <div class="pilot-step"><span>04 Kraken</span><b>Paper execution</b><div class="metric-detail">Tiny crypto orders only</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_supported_markets() -> None:
    chips = "".join(
        f'<span class="asset-chip">{symbol}</span>'
        for symbol in ("BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "LTC", "DOT", "AVAX", "LINK")
    )
    st.markdown(
        f"""
        <div class="asset-row">
          <span class="panel-kicker" style="margin: 4px 4px 0 0;">Tradable Markets</span>
          {chips}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result_card() -> None:
    result = str(st.session_state.last_result)
    card_class = "hold"
    title = "Awaiting Signal"
    kicker = "Live Verdict"
    detail = result

    if result.startswith("Executed Kraken paper command"):
        card_class = "executed"
        title = "Trade Executed"
        command = result.split("`")[1] if "`" in result else "Kraken paper order"
        consensus = "Consensus" + result.split("Consensus", 1)[1].split("\n", 1)[0] if "Consensus" in result else "Risk gates approved."
        detail = f"{command}<br>{consensus}"
    elif result.startswith("No trade executed"):
        title = "Trade Blocked"
        detail = "The models or risk rules did not approve a Kraken order."
    elif result.startswith("Featherless") or result.startswith("Error") or result.startswith("Kraken rejected"):
        card_class = "error"
        title = "Action Needed"
        detail = result[:500]

    st.markdown(
        f"""
        <div class="result-card {card_class}">
          <div class="panel-kicker">{kicker}</div>
          <div class="verdict">{title}</div>
          <div class="verdict-detail">{html.escape(detail).replace('&lt;br&gt;', '<br>')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics() -> None:
    trade_log = st.session_state.trade_log
    wins = sum(1 for trade in trade_log if float(trade.get("pnl", 0) or 0) > 0)
    win_rate = f"{wins / len(trade_log) * 100:.0f}%" if trade_log else "N/A"

    last_action = ""
    execution_events = [event for event in st.session_state.last_flight_log if event.get("type") == "execution"]
    if execution_events:
        event = execution_events[-1]
        if event.get("command") != "NO_ACTION" and not event.get("execution_ok", True):
            last_action = "REJECTED"
        else:
            last_action = event.get("command", "NO_ACTION")

    last_value = "Ready" if not last_action or last_action == "NO_ACTION" else ("Rejected" if last_action == "REJECTED" else "Command")
    last_detail = "No trade sent" if not last_action or last_action == "NO_ACTION" else ("Kraken blocked order" if last_action == "REJECTED" else last_action)

    cols = st.columns(4)
    cols[0].markdown(metric_card("Regime Score", f"{st.session_state.regime_score:.1f}/100", "risk posture", "#14b8a6"), unsafe_allow_html=True)
    cols[1].markdown(metric_card("Win Rate", win_rate, f"{len(trade_log)} logged app trades", "#22c55e"), unsafe_allow_html=True)
    cols[2].markdown(metric_card("Execution", "Crypto Paper", "Kraken spot sandbox", "#f59e0b"), unsafe_allow_html=True)
    cols[3].markdown(metric_card("Last Action", last_value, last_detail, "#ef4444"), unsafe_allow_html=True)


def render_equity_curve() -> None:
    balance = 10000.0
    points = [balance]
    for trade in st.session_state.trade_log:
        balance += float(trade.get("pnl", 0.0) or 0.0)
        points.append(balance)
    st.area_chart(pd.DataFrame({"Portfolio Value": points}), color="#14b8a6")


def render_flight_recorder() -> None:
    if not st.session_state.last_flight_log:
        st.info("Run an analysis to generate the decision timeline.")
        return

    for index, event in enumerate(st.session_state.last_flight_log, start=1):
        with st.container(border=True):
            st.markdown(f"#### {index}. {event.get('icon', '-')} {event.get('title', 'Event')}")
            event_type = event.get("type", "")
            if event_type == "ingested":
                st.write(event.get("content", ""))
            elif event_type == "signals":
                tickers = event.get("tickers") or []
                st.write(f"Tickers: `{', '.join(tickers) if tickers else 'none'}`")
                st.write(f"Sentiment: `{event.get('sentiment', 'neutral').upper()}`")
                st.write(event.get("summary", ""))
            elif event_type == "courtroom":
                st.write(event.get("reasoning", ""))
                votes = event.get("votes", [])
                cols = st.columns(max(1, len(votes)))
                for col, vote in zip(cols, votes):
                    with col:
                        status = "online" if vote.get("ok") else "error"
                        st.markdown(f"**{vote.get('model')}**")
                        st.caption(status)
                        st.metric(vote.get("vote", "HOLD"), f"{float(vote.get('confidence', 0.0)):.2f}")
                        st.write(vote.get("reasoning", ""))
                st.write(f"Final consensus: `{event.get('final_vote', 'HOLD')}`")
            elif event_type == "risk_judge":
                backtest = event.get("backtest", {})
                st.write(f"Verdict: `{event.get('verdict', 'BLOCKED')}`")
                st.write(backtest.get("reason", ""))
                st.json(event.get("rules", {}), expanded=False)
            elif event_type == "execution":
                command = event.get("command", "NO_ACTION")
                if command == "NO_ACTION":
                    st.warning("No Kraken order was sent.")
                elif not event.get("execution_ok", True):
                    st.code(command, language="bash")
                    if event.get("output"):
                        st.code(event["output"], language="text")
                    st.error("Kraken rejected the paper order.")
                else:
                    st.code(command, language="bash")
                    if event.get("output"):
                        st.code(event["output"], language="text")
                    st.success(f"Simulated PnL: {event.get('pnl', 'N/A')} USD")
            elif event_type == "evolution":
                st.write(event.get("narrative", ""))
                st.json(event.get("proposed_rules", {}), expanded=False)
            st.caption(event.get("ts", ""))


def render_sidebar(active_rules: dict) -> None:
    with st.sidebar:
        st.header("System")
        st.write("Mode: Kraken crypto paper")
        st.write("Supported: BTC, ETH, SOL, XRP, ADA, DOGE, LTC, DOT, AVAX, LINK")
        st.divider()
        with st.expander("Active Rules", expanded=False):
            st.json(active_rules)
        st.divider()
        st.subheader("Agent Identity")
        identity = get_or_create_wallet()
        st.code(identity["agentAddress"])
        st.link_button("Basescan", f"https://sepolia.basescan.org/address/{identity['agentAddress']}")


def render_operations(active_rules: dict) -> None:
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Portfolio Curve")
        render_equity_curve()
    with right:
        st.subheader("Trade Log")
        if st.session_state.trade_log:
            st.dataframe(st.session_state.trade_log, width="stretch")
        else:
            st.write("No app-tracked trades yet.")
    with st.expander("Current Dynamic Rules"):
        st.json(active_rules)


def run_voice_analysis(transcribed_text: str, source_label: str) -> None:
    st.session_state.market_brief = transcribed_text
    st.session_state.last_voice_transcript = transcribed_text
    st.session_state.chat_messages.append(
        {"role": "user", "content": f"{source_label}: {transcribed_text}"}
    )
    response = run_agent(transcribed_text, compact=True)
    st.session_state.chat_messages.append({"role": "assistant", "content": response})
    st.rerun()


def render_voice_tools() -> None:
    st.markdown(
        """
        <div class="quick-action">
          <strong>Voice Chat</strong>
          <span>Record or upload audio. The agent transcribes it and runs automatically.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    voice_col1, voice_col2 = st.columns([1, 1])
    with voice_col1:
        recorded_audio = audio_recorder(
            text="Record voice brief",
            recording_color="#ef4444",
            neutral_color="#14b8a6",
            icon_size="2x",
        )
    with voice_col2:
        uploaded_voice = st.file_uploader(
            "Upload voice brief",
            type=["wav", "mp3"],
            key="voice_chat_upload",
        )

    if recorded_audio is not None:
        audio_hash = hashlib.md5(recorded_audio).hexdigest()
        if st.session_state.last_processed_recorded_voice != audio_hash:
            try:
                transcribed_text = transcribe_audio_bytes(recorded_audio, ".wav")
                st.session_state.last_processed_recorded_voice = audio_hash
                st.success("Voice transcribed. Running agent now.")
                run_voice_analysis(transcribed_text, "Voice brief")
            except Exception as exc:
                st.error(f"Voice processing failed: {exc}")

    if uploaded_voice is not None:
        upload_bytes = uploaded_voice.getvalue()
        upload_hash = hashlib.md5(upload_bytes).hexdigest()
        if st.session_state.last_processed_uploaded_voice != upload_hash:
            try:
                suffix = Path(uploaded_voice.name).suffix.lower() or ".wav"
                transcribed_text = transcribe_audio_bytes(upload_bytes, suffix)
                st.session_state.last_processed_uploaded_voice = upload_hash
                st.success("Voice file transcribed. Running agent now.")
                run_voice_analysis(transcribed_text, f"Uploaded voice brief ({uploaded_voice.name})")
            except Exception as exc:
                st.error(f"Voice upload failed: {exc}")

    if st.session_state.last_voice_transcript:
        with st.expander("Last transcript", expanded=False):
            st.write(st.session_state.last_voice_transcript)


init_session()
render_styles()
active_rules = read_dynamic_config()
render_sidebar(active_rules)

st.markdown(
    """
    <div class="hero">
      <div class="hero-title">xRegime Oracle</div>
      <p class="hero-subtitle">Crypto-first autonomous trading console: type, upload, or speak a market brief; the agent votes, applies risk gates, and sends safe Kraken paper orders.</p>
      <div class="pill-row">
        <span class="pill">Kraken crypto paper mode</span>
        <span class="pill">3-model Featherless courtroom</span>
        <span class="pill">Speechmatics voice ingestion</span>
        <span class="pill">Replayable audit timeline</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

render_metrics()
render_pilot_rail()

st.markdown(
    """
    <div class="command-heading">
      <div>
        <h3>Command Center</h3>
        <p class="section-note">Speak, paste, or upload a crypto market brief. xRegime only trades supported Kraken paper pairs.</p>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
render_supported_markets()

command_col, result_col = st.columns([1.25, 1])
with command_col:
    with st.container(border=True):
        st.markdown('<div class="panel-kicker">01 Input</div><div class="panel-title">Start with voice or a market brief</div>', unsafe_allow_html=True)
        render_voice_tools()
        st.divider()
        if st.button("Load BTC sample", width="stretch"):
            st.session_state.market_brief = CRYPTO_SAMPLE
        market_brief = st.text_area(
            "Market brief",
            key="market_brief",
            height=190,
            placeholder="Example: BTC broke resistance after ETF inflows accelerated...",
        )
        uploaded_file = st.file_uploader("Upload transcript or audio for manual analysis", type=["txt", "wav", "mp3"])
        button_col1, button_col2 = st.columns([1, 1])
        analyze = button_col1.button("Analyze & Execute", type="primary", width="stretch")
        reflect = button_col2.button("Run Nightly Reflector", width="stretch")

if analyze:
    try:
        text_to_process = uploaded_file_to_text(uploaded_file) if uploaded_file else market_brief
        if not text_to_process.strip():
            st.warning("Add a crypto market brief or upload a file first.")
        else:
            run_agent(text_to_process)
            st.rerun()
    except Exception as exc:
        st.error(f"Input processing failed: {exc}")

if reflect:
    run_reflector()
    st.rerun()

with result_col:
    render_result_card()

timeline_tab, portfolio_tab, chat_tab = st.tabs(["Audit Trail", "Portfolio", "Chat"])

with timeline_tab:
    render_flight_recorder()

with portfolio_tab:
    render_operations(active_rules)

with chat_tab:
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("Ask xRegime Oracle to analyze a crypto market update..."):
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        response = run_agent(prompt, compact=True)
        st.markdown(response)
    st.session_state.chat_messages.append({"role": "assistant", "content": response})
