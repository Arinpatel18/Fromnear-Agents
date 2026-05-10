import logging
from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.nodes.input_node import process_input
from src.nodes.memory_node import memory_node
from src.nodes.sales_agent_node import sales_agent
from src.nodes.marketing_agent_node import marketing_agent
from src.nodes.aggregator_node import aggregator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_workflow():
    """
    Compiles the LangGraph workflow with memory integration.

    Flow:
    1. Input Node: Scrapes website + Instagram
    2. Memory Node: Retrieves similar past analyses for context
    3. Parallel: Sales Agent & Marketing Agent (with memory context)
    4. Aggregator: Combines outputs + saves to memory
    """
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("input_node", process_input)
    workflow.add_node("memory_node", memory_node)
    workflow.add_node("sales_agent", sales_agent)
    workflow.add_node("marketing_agent", marketing_agent)
    workflow.add_node("aggregator", aggregator)

    # Define Edges
    workflow.set_entry_point("input_node")

    # Input → Memory retrieval
    workflow.add_edge("input_node", "memory_node")

    # Memory → fan-out to both agents (parallel)
    workflow.add_edge("memory_node", "sales_agent")
    workflow.add_edge("memory_node", "marketing_agent")

    # Both agents converge at Aggregator
    workflow.add_edge("sales_agent", "aggregator")
    workflow.add_edge("marketing_agent", "aggregator")

    # Terminate after aggregation
    workflow.add_edge("aggregator", END)

    app = workflow.compile()
    return app


async def run_pipeline(
    website_url: str,
    instagram_url: str,
    category: str = "",
    location: str = ""
) -> dict:
    """
    Execute the complete AI pipeline with memory-augmented agents.
    """
    logger.info("=" * 50)
    logger.info("PIPELINE STARTED")
    logger.info("=" * 50)
    logger.info(f"Website: {website_url}")
    logger.info(f"Instagram: {instagram_url}")
    logger.info(f"Category: {category}")
    logger.info(f"Location: {location}")
    logger.info("=" * 50)

    workflow = create_workflow()

    initial_state = {
        "raw_input": {
            "website": website_url,
            "instagram_page": instagram_url,
            "website_url": website_url,
            "instagram_url": instagram_url,
            "category": category,
            "location": location,
        },
        "structured_data": {},
        "memory_context": {},
        "sales_output": {},
        "marketing_output": {},
        "aggregated_output": {},
    }

    try:
        result = workflow.invoke(initial_state)
        logger.info("=" * 50)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 50)
        return result
    except Exception as e:
        logger.error(f"✗ Pipeline failed: {str(e)}")
        raise
