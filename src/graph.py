import logging
from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.nodes.input_node import process_input
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
    Compiles the LangGraph workflow according to the proposed architecture.
    
    Flow:
    1. Input Node: Takes website + Instagram links, scrapes data
    2. Parallel: Sales Agent & Marketing Agent process the data
    3. Aggregator: Combines outputs into markdown report
    """
    # 1. Initialize the StateGraph
    workflow = StateGraph(AgentState)

    # 2. Add Nodes
    workflow.add_node("input_node", process_input)
    workflow.add_node("sales_agent", sales_agent)
    workflow.add_node("marketing_agent", marketing_agent)
    workflow.add_node("aggregator", aggregator)

    # 3. Define Edges
    # Start at the Input Node
    workflow.set_entry_point("input_node")
    
    # After input preprocessing, fan out to both Sales and Marketing Agents
    workflow.add_edge("input_node", "sales_agent")
    workflow.add_edge("input_node", "marketing_agent")
    
    # Both agents converge at Aggregator
    workflow.add_edge("sales_agent", "aggregator")
    workflow.add_edge("marketing_agent", "aggregator")
    
    # Terminate after aggregation
    workflow.add_edge("aggregator", END)

    # 4. Compile Graph
    app = workflow.compile()
    
    return app


async def run_pipeline(
    website_url: str,
    instagram_url: str,
    category: str = "",
    location: str = ""
) -> dict:
    """
    Execute the complete AI pipeline with website, Instagram URLs, category, and location.
    
    Args:
        website_url: URL of the business website
        instagram_url: Instagram profile URL or username
        category: Business category (e.g., Fashion, Electronics)
        location: Business location (e.g., Mumbai, India)
        
    Returns:
        Dictionary with aggregated output including markdown report
    """
    logger.info("=" * 50)
    logger.info("PIPELINE STARTED")
    logger.info("=" * 50)
    logger.info(f"Website: {website_url}")
    logger.info(f"Instagram: {instagram_url}")
    logger.info(f"Category: {category}")
    logger.info(f"Location: {location}")
    logger.info("=" * 50)
    
    # Create workflow
    workflow = create_workflow()
    
    # Initial state with input URLs and additional context
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
        "sales_output": {},
        "marketing_output": {},
        "aggregated_output": {}
    }
    
    # Execute workflow
    try:
        result = workflow.invoke(initial_state)
        logger.info("=" * 50)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 50)
        return result
    except Exception as e:
        logger.error(f"✗ Pipeline failed: {str(e)}")
        raise
