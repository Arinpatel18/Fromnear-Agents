from typing import TypedDict, Any, Dict, Optional, List


class AgentState(TypedDict):
    """
    Represents the state of our LangGraph workflow.

    Extended with memory, reasoning, and structured scoring fields.
    """
    # ── Core data flow ───────────────────────────────
    raw_input: Dict[str, Any]
    structured_data: Optional[Dict[str, Any]]
    sales_output: Optional[Dict[str, Any]]
    marketing_output: Optional[Dict[str, Any]]
    aggregated_output: Optional[Dict[str, Any]]

    # ── Memory & context ─────────────────────────────
    memory_context: Optional[Dict[str, Any]]       # past similar vendor analyses
