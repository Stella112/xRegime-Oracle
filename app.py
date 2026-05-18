import streamlit as st
import time
import json
import pandas as pd
from dotenv import load_dotenv
from agent.workflow import build_workflow, build_reflection_workflow
from agent.tools import read_dynamic_config
from agent.wallet import get_or_create_wallet

load_dotenv()

def run_full_agent_analysis(text_to_process: str) -> str:
    active_rules = read_dynamic_config()
    initial_state = {
        "input_text": text_to_process, "documents": [], "extracted_signals": {},
        "analysis_results": {}, "backtest_results": {}, "execution_plan": None,
        "status": "init", "trade_log": st.session_state.trade_log, "regime_score": st.session_state.regime_score,
        "proposed_rule_changes": [], "active_rules": active_rules
    }
    final_execution = "No action taken."
    final_reasoning = ""
    workflow = build_workflow()
    with st.status("Agent Progress", expanded=True) as status:
        try:
            for event in workflow.stream(initial_state):
                for key, value in event.items():
                    step_status = value.get("status", "")
                    if step_status == "reasoned":
                        st.write("🧠 **Textual Extraction:** Signals acquired.")
                    elif step_status == "analyzed":
                        st.write("📊 **Financial Analysis:** Evaluated by ensemble.")
                        final_reasoning = value.get("analysis_results", {}).get("reasoning", "")
                    elif step_status == "backtested":
                        st.write("🛡️ **Backtest Simulation:** Passed.")
                    elif step_status == "executed":
                        st.write("⚡ **Execution:** Complete.")
                        plan = value.get("execution_plan")
                        if plan and plan != "NO_ACTION":
                            final_execution = f"✅ Executed Command: `{plan}`"
                        else:
                            final_execution = "⚠️ No trading action taken."
                        if "trade_log" in value:
                            st.session_state.trade_log = value["trade_log"]
                        if "flight_log" in value:
                            st.session_state.last_flight_log = value["flight_log"]
            status.update(label="Workflow Complete", state="complete", expanded=False)
        except Exception as e:
            status.update(label=f"Workflow Error: {e}", state="error", expanded=True)
            return f"Error: {e}"
    return f"{final_execution}\n\n**Agent Reasoning:** {final_reasoning}"

st.set_page_config(page_title="xRegime Oracle", page_icon="♾️", layout="wide")

if "trade_log" not in st.session_state:
    st.session_state.trade_log = []
if "regime_score" not in st.session_state:
    st.session_state.regime_score = 50.0
if "flight_log" not in st.session_state:
    st.session_state.flight_log = []
if "last_flight_log" not in st.session_state:
    st.session_state.last_flight_log = []

st.markdown("""
<style>
    .reportview-container { background: #0E1117; }
    .stButton>button {
        background-color: #6366F1; color: white; border-radius: 8px; border: none; padding: 10px 24px; transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #4F46E5; transform: translateY(-2px); }
    .btn-reflect>button { background-color: #8B5CF6; }
    .metric-card {
        background-color: #1F2937; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center; border-left: 4px solid #6366F1; margin-bottom: 20px;
    }
    .regime-card { border-left: 4px solid #8B5CF6; }
    .flight-event {
        background: #1a1f2e; border-left: 3px solid #6366F1; border-radius: 8px;
        padding: 14px 18px; margin-bottom: 12px;
    }
    .flight-event h4 { color: #A78BFA; margin: 0 0 6px 0; font-size: 14px; }
    .vote-buy { color: #10B981; font-weight: bold; }
    .vote-sell { color: #EF4444; font-weight: bold; }
    .vote-hold { color: #F59E0B; font-weight: bold; }
    .verdict-approved { color: #10B981; font-weight: bold; font-size: 16px; }
    .verdict-blocked { color: #EF4444; font-weight: bold; font-size: 16px; }
</style>
""", unsafe_allow_html=True)

st.title("♾️ xRegime Oracle")
st.markdown("### Self-Evolving Enterprise Trading Agent · Kraken CLI · Featherless Ensemble · Speechmatics Voice AI")

with st.sidebar:
    st.header("Enterprise Inputs")
    input_text = st.text_area("Paste Earnings Report / Executive Briefing:", height=150)
    uploaded_file = st.file_uploader("Or Upload Earnings Call Audio / PDF", type=['pdf', 'txt', 'wav', 'mp3'])
    start_workflow = st.button("🚀 Analyze & Execute", use_container_width=True)
    
    st.divider()
    st.header("Self-Evolution")
    st.markdown("Trigger the Nightly Reflector to evolve the strategy based on Regime Score.")
    st.markdown('<div class="btn-reflect">', unsafe_allow_html=True)
    run_reflection = st.button("🧠 Run Nightly Reflector", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="metric-card regime-card"><h3>Regime Score</h3><h2 style="color: #A78BFA;">{st.session_state.regime_score:.1f} / 100</h2></div>', unsafe_allow_html=True)
with col2:
    win_rate = "N/A"
    if st.session_state.trade_log:
        wins = sum(1 for t in st.session_state.trade_log if t.get("pnl", 0) > 0)
        win_rate = f"{(wins/len(st.session_state.trade_log))*100:.0f}%"
    st.markdown(f'<div class="metric-card"><h3>Win Rate</h3><h2 style="color: #10B981;">{win_rate}</h2></div>', unsafe_allow_html=True)
with col3:
    trades_count = len(st.session_state.trade_log)
    st.markdown(f'<div class="metric-card"><h3>Executed Trades</h3><h2 style="color: #60A5FA;">{trades_count}</h2></div>', unsafe_allow_html=True)

col_main, col_rules = st.columns([2, 1])

with col_rules:
    st.subheader("🛡️ ERC-8004 Agent Identity")
    agent_identity = get_or_create_wallet()
    addr = agent_identity["agentAddress"]
    st.markdown(f"**Address:** `{addr}`")
    st.markdown(f"[View on Basescan](https://sepolia.basescan.org/address/{addr})")
    with st.expander("ERC-8004 Registration Data", expanded=False):
        st.json(agent_identity)
        
    st.subheader("Active Rules (Dynamic)")
    active_rules = read_dynamic_config()
    st.json(active_rules)
    
    st.subheader("Trade Log")
    if st.session_state.trade_log:
        st.dataframe(st.session_state.trade_log)
    else:
        st.write("No trades yet.")

with col_main:
    st.subheader("📈 Live Equity Curve")
    st.markdown("Cumulative PnL of all executed trades ($10,000 Starting Balance)")
    
    # Calculate Equity Curve
    starting_balance = 10000.0
    equity_curve = [starting_balance]
    
    for trade in st.session_state.trade_log:
        pnl = float(trade.get("pnl", 0.0))
        equity_curve.append(equity_curve[-1] + pnl)
        
    # Render interactive chart
    df_equity = pd.DataFrame({"Portfolio Value ($)": equity_curve})
    st.area_chart(df_equity, color="#6366F1")
    
    st.markdown("---")

    if start_workflow:
        if not input_text and not uploaded_file:
            st.error("Please provide an input text or file.")
        else:
            text_to_process = input_text
            if uploaded_file:
                if uploaded_file.name.endswith('.txt'):
                    text_to_process = uploaded_file.getvalue().decode("utf-8")
                elif uploaded_file.name.endswith('.wav') or uploaded_file.name.endswith('.mp3'):
                    import os
                    import tempfile
                    from agent.tools import transcribe_audio_with_speechmatics
                    st.info(f"🎙️ Ingesting earnings call audio via Speechmatics: {uploaded_file.name}...")
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name
                    try:
                        text_to_process = transcribe_audio_with_speechmatics(tmp_path)
                        st.success("Transcription complete!")
                        with st.expander("View Transcript"):
                            st.write(text_to_process)
                    except Exception as e:
                        st.error(f"Speechmatics failed: {e}")
                        st.stop()
                    finally:
                        os.unlink(tmp_path)
                else:
                    text_to_process = f"Received file {uploaded_file.name}. (Text extraction currently limited to .txt and audio files)"
            
            st.info("Starting Agentic Workflow...")
            workflow = build_workflow()
            initial_state = {
                "input_text": text_to_process, "documents": [], "extracted_signals": {},
                "analysis_results": {}, "backtest_results": {}, "execution_plan": None,
                "status": "init", "trade_log": st.session_state.trade_log, "regime_score": st.session_state.regime_score,
                "proposed_rule_changes": [], "active_rules": active_rules
            }
            
            with st.status("Agent Progress", expanded=True) as status:
                try:
                    for event in workflow.stream(initial_state):
                        for key, value in event.items():
                            step_status = value.get("status", "")
                            if step_status == "reasoned":
                                st.write("🧠 **Textual Extraction:** Extracted signals using Featherless (Qwen-7B).")
                                st.json(value.get("extracted_signals"))
                            elif step_status == "analyzed":
                                st.write("📊 **Financial Analysis:** Featherless 3-model ensemble evaluated trades.")
                                st.json(value.get("analysis_results"))
                            elif step_status == "backtested":
                                st.write("🛡️ **Backtest Simulation:** Passed.")
                            elif step_status == "executed":
                                st.write("⚡ **Execution:**")
                                plan = value.get("execution_plan")
                                if plan and plan != "NO_ACTION":
                                    st.code(plan, language="bash")
                                    st.success("✅ Kraken CLI command executed (paper/sandbox mode)")
                                    st.info("💡 Live mode: same execution layer supports real Kraken trading with no-withdrawal API keys + circuit breakers.")
                                else:
                                    st.warning("No high-confidence signal — no trade executed.")
                                # Update session state log
                                if "trade_log" in value:
                                    st.session_state.trade_log = value["trade_log"]
                                if "flight_log" in value:
                                    st.session_state.last_flight_log = value["flight_log"]
                            time.sleep(0.5)
                    status.update(label="Workflow Complete", state="complete", expanded=True)
                    st.rerun()
                except Exception as e:
                    status.update(label=f"Workflow Error: {e}", state="error", expanded=True)

    elif run_reflection:
        st.info("Initiating Nightly Reflection (Self-Evolution)...")
        workflow = build_reflection_workflow()
        initial_state = {
            "input_text": "", "documents": [], "extracted_signals": {},
            "analysis_results": {}, "backtest_results": {}, "execution_plan": None,
            "status": "init", "trade_log": st.session_state.trade_log, "regime_score": st.session_state.regime_score,
            "proposed_rule_changes": [], "active_rules": active_rules
        }
        
        with st.status("Reflection Progress", expanded=True) as status:
            try:
                for event in workflow.stream(initial_state):
                    for key, value in event.items():
                        step_status = value.get("status", "")
                        if step_status == "regime_calculated":
                            st.write(f"⚖️ **Calculated Regime Score:** {value.get('regime_score')}")
                            st.session_state.regime_score = value.get("regime_score")
                        elif step_status == "reflected":
                            st.write("🧠 **Featherless Reflection:** Qwen-72B proposed changes based on logs.")
                            st.json(value.get("proposed_rule_changes")[0])
                        elif step_status == "evolved":
                            st.write("✨ **Evolution Applied:** dynamic_config.json updated!")
                            st.success("Strategy successfully evolved!")
                        if "flight_log" in value:
                            st.session_state.last_flight_log = value["flight_log"]
                        time.sleep(1)
                status.update(label="Reflection Complete", state="complete", expanded=True)
                time.sleep(2)
                st.rerun()
            except Exception as e:
                status.update(label=f"Reflection Error: {e}", state="error", expanded=True)

# ====================== AGENT FLIGHT RECORDER ======================
if st.session_state.last_flight_log:
    st.markdown("---")
    st.subheader("🛫 Agent Flight Recorder: Replayable Decision Timeline")
    st.markdown("Audit exactly what the agent heard, what each model believed, and how rules were applied.")
    
    for event in st.session_state.last_flight_log:
        st.markdown(f'<div class="flight-event">', unsafe_allow_html=True)
        st.markdown(f"#### {event.get('icon', '🔹')} {event.get('title', 'Event')}")
        
        etype = event.get("type")
        if etype == "ingested":
            st.write(f"**Input Data:** {event.get('content', '')}")
        elif etype == "signals":
            st.write(f"**Extracted Tickers:** {', '.join(event.get('tickers', []))}")
            st.write(f"**Sentiment:** {event.get('sentiment', 'neutral').upper()}")
            st.write(f"**Signal Summary:** {event.get('summary', '')}")
        elif etype == "courtroom":
            votes = event.get("votes", [])
            cols = st.columns(max(len(votes), 1))
            for i, v in enumerate(votes):
                with cols[i]:
                    st.markdown(f"**{v['model']}**")
                    vote_str = v['vote']
                    css_class = f"vote-{vote_str.lower()}"
                    st.markdown(f'Verdict: <span class="{css_class}">{vote_str}</span> (Conf: {v["confidence"]})', unsafe_allow_html=True)
                    st.caption(f'"{v["reasoning"]}"')
            st.markdown(f"**Final Consensus:** {event.get('final_vote')} (Avg Conf: {event.get('avg_confidence'):.2f})")
        elif etype == "risk_judge":
            st.write(f"**Active Regime Score:** {event.get('regime_score', 50):.1f}")
            st.write(f"**Active Rules:** Risk Tolerance = `{event.get('rules', {}).get('risk_tolerance', 'N/A')}` | Stop Loss = `{event.get('rules', {}).get('stop_loss_percentage', 0)*100}%`")
            verdict = event.get("verdict", "BLOCKED")
            v_class = "verdict-approved" if verdict == "APPROVED" else "verdict-blocked"
            st.markdown(f'**Execution Verdict:** <span class="{v_class}">{verdict}</span>', unsafe_allow_html=True)
        elif etype == "execution":
            cmd = event.get("command", "NO_ACTION")
            if cmd != "NO_ACTION":
                st.code(cmd, language="bash")
                st.success(f"Execution successful. (Simulated PnL: {event.get('pnl', 'N/A')} USD)")
            else:
                st.warning("Execution blocked — NO_ACTION.")
        elif etype == "evolution":
            st.write(f"**Reflector Narrative:** _{event.get('narrative', '')}_")
            st.json(event.get("proposed_rules", {}))
            
        st.markdown(f"<div style='text-align: right; font-size: 10px; color: #6b7280;'>{event.get('ts', '')}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ====================== CHAT WITH AGENT + VOICE ======================
st.markdown("---")
st.subheader("💬 Chat with xRegime Oracle (Voice + Text)")

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Paste an earnings summary or ask the agent (e.g. 'NVDA beat estimates by 18%, bullish guidance'):"):
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = run_full_agent_analysis(prompt)
        st.markdown(response)
    st.session_state.chat_messages.append({"role": "assistant", "content": response})

st.markdown("**Or speak directly** (record or upload audio for voice command)")

from audio_recorder_streamlit import audio_recorder
recorded_audio = audio_recorder(text="Click to record voice command", recording_color="#e81e1e", neutral_color="#6aa36f", icon_size="2x")

if recorded_audio is not None:
    import hashlib
    audio_hash = hashlib.md5(recorded_audio).hexdigest()
    if "last_processed_recorded_voice" not in st.session_state or st.session_state.last_processed_recorded_voice != audio_hash:
        with st.chat_message("user"):
            st.markdown("*(Direct Voice Recording)*")
        with st.chat_message("assistant"):
            import os
            import tempfile
            from agent.tools import transcribe_audio_with_speechmatics
            st.info("🎙️ Ingesting earnings call audio via Speechmatics...")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(recorded_audio)
                tmp_path = tmp.name
            try:
                transcribed_text = transcribe_audio_with_speechmatics(tmp_path)
                st.success(f"Transcribed: {transcribed_text}")
                response = run_full_agent_analysis(transcribed_text)
                st.markdown(response)
                
                st.session_state.chat_messages.append({"role": "user", "content": f"*(Voice note: {transcribed_text})*"})
                st.session_state.chat_messages.append({"role": "assistant", "content": response})
                st.session_state.last_processed_recorded_voice = audio_hash
            except Exception as e:
                st.error(f"Speechmatics failed: {e}")
            finally:
                os.unlink(tmp_path)

st.markdown("*Or upload an earnings call / executive briefing audio:*")
uploaded_voice = st.file_uploader("Upload Earnings Call (.wav or .mp3)", type=["wav", "mp3"], key="voice_chat")

if uploaded_voice is not None:
    # Check if we already processed this exact uploaded file instance to avoid loops
    if "last_processed_voice" not in st.session_state or st.session_state.last_processed_voice != uploaded_voice.name + str(uploaded_voice.size):
        with st.chat_message("user"):
            st.markdown(f"*(Uploaded voice note: {uploaded_voice.name})*")
            
        with st.chat_message("assistant"):
            import os
            import tempfile
            from agent.tools import transcribe_audio_with_speechmatics
            st.info("🎙️ Ingesting earnings call audio via Speechmatics...")
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_voice.name.split('.')[-1]}") as tmp:
                tmp.write(uploaded_voice.getvalue())
                tmp_path = tmp.name
            try:
                transcribed_text = transcribe_audio_with_speechmatics(tmp_path)
                st.success(f"Transcribed: {transcribed_text}")
                response = run_full_agent_analysis(transcribed_text)
                st.markdown(response)
                
                # Append to chat
                st.session_state.chat_messages.append({"role": "user", "content": f"*(Voice note: {transcribed_text})*"})
                st.session_state.chat_messages.append({"role": "assistant", "content": response})
                # Mark as processed
                st.session_state.last_processed_voice = uploaded_voice.name + str(uploaded_voice.size)
            except Exception as e:
                st.error(f"Speechmatics failed: {e}")
            finally:
                os.unlink(tmp_path)

