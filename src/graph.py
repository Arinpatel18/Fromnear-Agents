import logging
from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.nodes.input_node import process_input
from src.nodes.research_agent_node import research_agent
from src.nodes.memory_node import memory_node
from src.nodes.sales_agent_node import sales_agent
from src.nodes.marketing_agent_node import marketing_agent
from src.nodes.validator_node import validator_agent
from src.nodes.aggregator_node import aggregator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_workflow():
    """
    Compiles the full multi-agent LangGraph workflow.

    Autonomous pipeline — runs end-to-end without manual intervention:
    1. Input Node      → Scrape website + Instagram (tool usage)
    2. Research Agent   → Market positioning, competitive analysis (reasoning)
    3. Memory Node      → Retrieve similar past analyses (memory)
    4. Sales Agent      → Onboarding strategy + lead scoring (task execution)
    5. Marketing Agent  → Launch campaigns + growth plan (task execution)
    6. Validator Agent   → Cross-validate quality & consistency (reasoning)
    7. Aggregator       → Combine outputs + save to CRM (structured workflow)
    """
    workflow = StateGraph(AgentState)

    # Add all agent nodes
    workflow.add_node("input_node", process_input)
    workflow.add_node("research_agent", research_agent)
    workflow.add_node("memory_node", memory_node)
    workflow.add_node("sales_agent", sales_agent)
    workflow.add_node("marketing_agent", marketing_agent)
    workflow.add_node("validator_agent", validator_agent)
    workflow.add_node("aggregator", aggregator)

    # Define the autonomous workflow edges
    workflow.set_entry_point("input_node")

    # Stage 1: Input → Research (sequential — research needs scraped data)
    workflow.add_edge("input_node", "research_agent")

    # Stage 2: Research → Memory (retrieve past analyses for context)
    workflow.add_edge("research_agent", "memory_node")

    # Stage 3: Memory → fan-out to Sales + Marketing (parallel)
    workflow.add_edge("memory_node", "sales_agent")
    workflow.add_edge("memory_node", "marketing_agent")

    # Stage 4: Sales + Marketing → Validator (quality gate)
    workflow.add_edge("sales_agent", "validator_agent")
    workflow.add_edge("marketing_agent", "validator_agent")

    # Stage 5: Validator → Aggregator (final assembly + CRM save)
    workflow.add_edge("validator_agent", "aggregator")

    # Terminate
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
    Execute the full autonomous multi-agent pipeline.

    Flow: scrape → research → recall → [pitch + campaign] → validate → aggregate
    No manual intervention required.
    """
    logger.info("=" * 60)
    logger.info("🚀 AUTONOMOUS MULTI-AGENT PIPELINE STARTED")
    logger.info("=" * 60)
    logger.info(f"Website:   {website_url}")
    logger.info(f"Instagram: {instagram_url}")
    logger.info(f"Category:  {category}")
    logger.info(f"Location:  {location}")
    logger.info("Agents: Input → Research → Memory → [Sales | Marketing] → Validator → Aggregator")
    logger.info("=" * 60)

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
        "research_output": {},
        "memory_context": {},
        "sales_output": {},
        "marketing_output": {},
        "validation_report": {},
        "aggregated_output": {},
    }

    try:
        result = workflow.invoke(initial_state)
        logger.info("=" * 60)
        logger.info("✅ AUTONOMOUS PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        return result
    except Exception as e:
        logger.error(f"✗ Pipeline failed: {str(e)}")
        raise
