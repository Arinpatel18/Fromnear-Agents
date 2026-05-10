"""
Memory Retrieval Node.

Runs after the Input Node and before the Sales/Marketing agents.
Queries the persistent memory for similar past vendor analyses and
injects them into the state so agents have historical context.
"""

import logging
from src.state import AgentState
from src.memory import get_similar_vendors

logger = logging.getLogger(__name__)


def memory_node(state: AgentState) -> AgentState:
    """
    Retrieve relevant past analyses from memory and inject into state.

    This gives agents historical context:
    - "We previously onboarded a similar fashion brand in Mumbai with score 8/10"
    - Helps agents stay consistent and learn from past pitches
    """
    logger.info("=" * 50)
    logger.info("MEMORY RETRIEVAL NODE")
    logger.info("=" * 50)

    structured_data = state.get("structured_data", {})
    category = structured_data.get("category", "")
    location = structured_data.get("location", "")

    logger.info(f"🧠 Searching memory for: category='{category}', location='{location}'")

    similar = get_similar_vendors(category=category, location=location, limit=3)

    if similar:
        logger.info(f"🧠 Found {len(similar)} relevant past analysis(es):")
        for v in similar:
            logger.info(
                f"   → {v['domain']} ({v['category']}, {v['location']}) "
                f"— score {v['lead_score']}/10, confidence {v['confidence']}"
            )
    else:
        logger.info("🧠 No past analyses found — first time for this category/location")

    memory_context = {
        "similar_vendors": similar,
        "has_history": len(similar) > 0,
        "total_past_analyses": len(similar),
    }

    logger.info("=" * 50)
    return {"memory_context": memory_context}
