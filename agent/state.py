from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    # Standard Execution Workflow
    input_text: str
    documents: List[str]
    extracted_signals: Dict[str, Any]
    analysis_results: Dict[str, Any]
    backtest_results: Dict[str, Any]
    execution_plan: Optional[str]
    execution_output: Optional[str]
    execution_ok: Optional[bool]
    status: str
    
    # Nightly Reflection Workflow
    trade_log: List[Dict[str, Any]]
    regime_score: float
    proposed_rule_changes: List[Dict[str, Any]]
    active_rules: Dict[str, Any]

    # Agent Flight Recorder — structured decision audit trail
    flight_log: List[Dict[str, Any]]
