from typing import TypedDict, Any, Dict, Optional, List


class AgentState(TypedDict):
    """
    Represents the state of our LangGraph multi-agent workflow.

    6-agent pipeline:
      input → research → memory → [sales, marketing] → validator → aggregator
    """
    # ── Core data flow ───────────────────────────────
    raw_input: Dict[str, Any]
    structured_data: Optional[Dict[str, Any]]

    # ── Research agent output ────────────────────────
    research_output: Optional[Dict[str, Any]]

    # ── Sales & Marketing agent outputs ──────────────
    sales_output: Optional[Dict[str, Any]]
    marketing_output: Optional[Dict[str, Any]]

    # ── Validator agent output ───────────────────────
    validation_report: Optional[Dict[str, Any]]

    # ── Final aggregated output ──────────────────────
    aggregated_output: Optional[Dict[str, Any]]

    # ── Memory & context ─────────────────────────────
    memory_context: Optional[Dict[str, Any]]
