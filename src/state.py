from typing import TypedDict, Any, Dict, Optional

class AgentState(TypedDict):
    """
    Represents the state of our LangGraph workflow.
    """
    raw_input: Dict[str, Any]
    structured_data: Optional[Dict[str, Any]]
    sales_output: Optional[Dict[str, Any]]
    marketing_output: Optional[Dict[str, Any]]
    aggregated_output: Optional[Dict[str, Any]]
