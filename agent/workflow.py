import datetime
import random
from typing import Any

from langgraph.graph import END, StateGraph

from agent.state import AgentState
from agent.tools import (
    analyze_with_featherless_ensemble,
    backtest_strategy,
    build_kraken_order_args,
    calculate_regime_score,
    execute_kraken_cli,
    extract_signals_with_featherless,
    read_dynamic_config,
    reflect_on_performance_with_featherless,
    update_dynamic_config,
)


def _ts() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def _append_log(state: AgentState, event: dict[str, Any]) -> list[dict[str, Any]]:
    log = list(state.get("flight_log", []))
    log.append({**event, "ts": _ts()})
    return log


def node_ingest(state: AgentState):
    return {
        "status": "ingested",
        "flight_log": _append_log(
            state,
            {
                "type": "ingested",
                "icon": "🎙️",
                "title": "Audio / Text Ingested",
                "content": state.get("input_text", "")[:1000],
            },
        ),
    }


def node_multimodal_reasoning(state: AgentState):
    signals = extract_signals_with_featherless(state.get("input_text", ""))
    return {
        "extracted_signals": signals,
        "status": "reasoned",
        "flight_log": _append_log(
            state,
            {
                "type": "signals",
                "icon": "🔍",
                "title": "Signals Extracted",
                "tickers": signals.get("tickers", []),
                "sentiment": signals.get("sentiment", "neutral"),
                "summary": signals.get("summary", ""),
            },
        ),
    }


def node_financial_analysis(state: AgentState):
    active_rules = read_dynamic_config()
    analysis = analyze_with_featherless_ensemble(state.get("extracted_signals", {}), active_rules)
    courtroom = [
        {
            "model": result.get("model", f"Model {index + 1}"),
            "model_id": result.get("model_id", ""),
            "vote": result.get("vote", "HOLD"),
            "confidence": result.get("confidence", 0.0),
            "reasoning": result.get("reasoning", ""),
            "ok": result.get("ok", False),
        }
        for index, result in enumerate(analysis.get("raw_results", []))
    ]

    return {
        "analysis_results": analysis,
        "active_rules": active_rules,
        "status": "analyzed",
        "flight_log": _append_log(
            state,
            {
                "type": "courtroom",
                "icon": "⚖️",
                "title": "Model Courtroom — Ensemble Vote",
                "votes": courtroom,
                "final_vote": analysis.get("vote", "HOLD"),
                "avg_confidence": analysis.get("confidence", 0.0),
                "healthy": analysis.get("healthy", False),
                "reasoning": analysis.get("reasoning", ""),
            },
        ),
    }


def node_backtest(state: AgentState):
    analysis = state.get("analysis_results", {})
    signals = state.get("extracted_signals", {})
    rules = read_dynamic_config()
    regime = float(state.get("regime_score", 50.0))
    results = backtest_strategy(
        tickers=signals.get("tickers", []),
        vote=analysis.get("vote", "HOLD"),
        confidence=float(analysis.get("confidence", 0.0)),
        regime_score=regime,
        rules=rules,
    )
    verdict = "APPROVED" if results.get("status") == "PASS" else "BLOCKED"

    return {
        "backtest_results": results,
        "status": "backtested",
        "flight_log": _append_log(
            state,
            {
                "type": "risk_judge",
                "icon": "🛡️",
                "title": "Risk Judge — Regime Score Applied",
                "regime_score": regime,
                "rules": rules,
                "backtest": results,
                "verdict": verdict,
            },
        ),
    }


def node_execute(state: AgentState):
    analysis = state.get("analysis_results", {})
    signals = state.get("extracted_signals", {})
    results = state.get("backtest_results", {})
    args = None
    output = ""
    execution_ok = True

    if results.get("status") == "PASS":
        args = build_kraken_order_args(analysis.get("vote", "HOLD"), signals.get("tickers", []))

    if args:
        execution = execute_kraken_cli(args)
        execution_ok = bool(execution.get("ok"))
        output = execution.get("output") or execution.get("error", "")
        command = " ".join(args)
    else:
        command = "NO_ACTION"

    trade_log = list(state.get("trade_log", []))
    pnl = None
    if args and execution_ok:
        pnl = random.choice([50, -20, 100, -10])
        trade_log.append(
            {
                "trade": command,
                "vote": analysis.get("vote", "HOLD"),
                "ticker": args[3].split("/", 1)[0],
                "pnl": pnl,
                "ts": _ts(),
            }
        )

    return {
        "execution_plan": command,
        "execution_output": output,
        "execution_ok": execution_ok,
        "trade_log": trade_log,
        "status": "executed",
        "flight_log": _append_log(
            state,
            {
                "type": "execution",
                "icon": "⚡",
                "title": "Execution Moment — Kraken CLI",
                "command": command,
                "output": output,
                "execution_ok": execution_ok,
                "pnl": pnl,
            },
        ),
    }


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


def node_calc_regime(state: AgentState):
    trade_log = state.get("trade_log", [])
    regime = calculate_regime_score(trade_log)
    return {"regime_score": regime, "status": "regime_calculated", "flight_log": state.get("flight_log", [])}


def node_reflect(state: AgentState):
    regime = state.get("regime_score", 50.0)
    trade_log = state.get("trade_log", [])
    rules = read_dynamic_config()
    proposed = reflect_on_performance_with_featherless(regime, trade_log, rules)
    return {
        "proposed_rule_changes": [proposed],
        "status": "reflected",
        "flight_log": _append_log(
            state,
            {
                "type": "evolution",
                "icon": "🌱",
                "title": "Self-Evolution — Nightly Reflector",
                "regime_score": regime,
                "old_rules": rules,
                "proposed_rules": proposed,
                "narrative": proposed.get("special_instructions", ""),
            },
        ),
    }


def node_apply_evolution(state: AgentState):
    proposals = state.get("proposed_rule_changes", [])
    if proposals:
        best_proposal = proposals[0]
        updated = update_dynamic_config(best_proposal)
        return {
            "active_rules": best_proposal,
            "status": "evolved" if updated else "evolution_failed",
        }
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
