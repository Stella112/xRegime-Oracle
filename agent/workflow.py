from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.tools import (
    extract_signals_with_featherless, 
    analyze_with_featherless_ensemble, 
    execute_kraken_cli, 
    backtest_strategy,
    read_dynamic_config,
    update_dynamic_config,
    calculate_regime_score,
    reflect_on_performance_with_featherless
)

import datetime

def _ts():
    return datetime.datetime.utcnow().isoformat()

# --- Standard Execution Workflow ---

def node_ingest(state: AgentState):
    log = state.get("flight_log", [])
    log.append({
        "type": "ingested",
        "icon": "🎙️",
        "title": "Audio / Text Ingested",
        "content": state.get("input_text", "")[:800],
        "ts": _ts()
    })
    return {"status": "ingested", "flight_log": log}

def node_multimodal_reasoning(state: AgentState):
    signals = extract_signals_with_featherless(state.get("input_text", ""))
    log = state.get("flight_log", [])
    # Highlight key phrases from summary
    summary = signals.get("summary", "")
    tickers = signals.get("tickers", [])
    sentiment = signals.get("sentiment", "neutral")
    log.append({
        "type": "signals",
        "icon": "🔍",
        "title": "Signals Extracted",
        "tickers": tickers,
        "sentiment": sentiment,
        "summary": summary,
        "ts": _ts()
    })
    return {"extracted_signals": signals, "status": "reasoned", "flight_log": log}

def node_financial_analysis(state: AgentState):
    active_rules = read_dynamic_config()
    analysis = analyze_with_featherless_ensemble(state.get("extracted_signals", {}), active_rules)
    log = state.get("flight_log", [])
    # Capture per-model votes for the Model Courtroom
    raw = analysis.get("raw_results", [])
    model_names = [
        "Qwen-7B (Featherless)",
        "Qwen-72B (Featherless)",
        "Mixtral-8x7B (Featherless)"
    ]
    courtroom = []
    for i, result in enumerate(raw):
        courtroom.append({
            "model": model_names[i] if i < len(model_names) else f"Model {i+1}",
            "vote": result.get("vote", "HOLD"),
            "confidence": result.get("confidence", 0.0),
            "reasoning": result.get("reasoning", "")
        })
    log.append({
        "type": "courtroom",
        "icon": "⚖️",
        "title": "Model Courtroom — Ensemble Vote",
        "votes": courtroom,
        "final_vote": analysis.get("vote", "HOLD"),
        "avg_confidence": analysis.get("confidence", 0.0),
        "ts": _ts()
    })
    return {"analysis_results": analysis, "active_rules": active_rules, "status": "analyzed", "flight_log": log}

def node_backtest(state: AgentState):
    analysis = state.get("analysis_results", {})
    signals = state.get("extracted_signals", {})
    vote = analysis.get("vote", "HOLD")
    tickers = signals.get("tickers", [])
    results = backtest_strategy(tickers, vote)
    log = state.get("flight_log", [])
    rules = read_dynamic_config()
    regime = state.get("regime_score", 50.0)
    verdict = "APPROVED" if results.get("status") == "PASS" else "BLOCKED"
    log.append({
        "type": "risk_judge",
        "icon": "🛡️",
        "title": "Risk Judge — Regime Score Applied",
        "regime_score": regime,
        "rules": rules,
        "backtest": results,
        "verdict": verdict,
        "ts": _ts()
    })
    return {"backtest_results": results, "status": "backtested", "flight_log": log}

def node_execute(state: AgentState):
    analysis = state.get("analysis_results", {})
    signals = state.get("extracted_signals", {})
    results = state.get("backtest_results", {})
    vote = analysis.get("vote", "HOLD")
    tickers = signals.get("tickers", [])
    status = results.get("status", "FAIL")
    
    if vote == "BUY" and tickers and status == "PASS":
        command = f"/root/.cargo/bin/kraken paper buy {tickers[0]}/USD 1"
    elif vote == "SELL" and tickers and status == "PASS":
        command = f"/root/.cargo/bin/kraken paper sell {tickers[0]}/USD 1"
    else:
        command = "NO_ACTION"
    
    if command != "NO_ACTION":
        execute_kraken_cli(command)
        
    # Append to mock trade log in state
    trade_log = state.get("trade_log", [])
    pnl = None
    if command != "NO_ACTION":
        import random
        pnl = random.choice([50, -20, 100, -10]) 
        trade_log.append({"trade": command, "pnl": pnl})
        
    log = state.get("flight_log", [])
    log.append({
        "type": "execution",
        "icon": "⚡",
        "title": "Execution Moment — Kraken CLI",
        "command": command,
        "pnl": pnl,
        "ts": _ts()
    })
    return {"execution_plan": command, "trade_log": trade_log, "status": "executed", "flight_log": log}

def build_workflow():
    workflow = StateGraph(AgentState)
    workflow.add_node("ingest", node_ingest)
    workflow.add_node("reasoning", node_multimodal_reasoning)
    workflow.add_node("analysis", node_financial_analysis)
    workflow.add_node("backtest", node_backtest)
    workflow.add_node("execute", node_execute)
    
    workflow.set_entry_point("ingest")
    workflow.add_edge("ingest", "reasoning")
    workflow.add_edge("reasoning", "analysis")
    workflow.add_edge("analysis", "backtest")
    workflow.add_edge("backtest", "execute")
    workflow.add_edge("execute", END)
    return workflow.compile()

# --- Nightly Reflection Workflow ---

def node_calc_regime(state: AgentState):
    trade_log = state.get("trade_log", [])
    regime = calculate_regime_score(trade_log)
    flight = state.get("flight_log", [])
    return {"regime_score": regime, "status": "regime_calculated", "flight_log": flight}

def node_reflect(state: AgentState):
    regime = state.get("regime_score", 50.0)
    trade_log = state.get("trade_log", [])
    rules = read_dynamic_config()
    proposed = reflect_on_performance_with_featherless(regime, trade_log, rules)
    flight = state.get("flight_log", [])
    flight.append({
        "type": "evolution",
        "icon": "🌱",
        "title": "Self-Evolution — Nightly Reflector",
        "regime_score": regime,
        "old_rules": rules,
        "proposed_rules": proposed,
        "narrative": proposed.get("special_instructions", ""),
        "ts": _ts()
    })
    return {"proposed_rule_changes": [proposed], "status": "reflected", "flight_log": flight}

def node_apply_evolution(state: AgentState):
    proposals = state.get("proposed_rule_changes", [])
    if proposals:
        best_proposal = proposals[0]
        update_dynamic_config(best_proposal)
        return {"active_rules": best_proposal, "status": "evolved"}
    return {"status": "no_change"}

def build_reflection_workflow():
    workflow = StateGraph(AgentState)
    workflow.add_node("regime", node_calc_regime)
    workflow.add_node("reflect", node_reflect)
    workflow.add_node("apply", node_apply_evolution)
    
    workflow.set_entry_point("regime")
    workflow.add_edge("regime", "reflect")
    workflow.add_edge("reflect", "apply")
    workflow.add_edge("apply", END)
    return workflow.compile()
