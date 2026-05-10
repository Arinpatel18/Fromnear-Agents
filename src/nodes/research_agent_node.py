"""
Research Agent Node.

The first analytical agent in the pipeline. Takes raw scraped data and
performs deep business intelligence:
  - Market positioning analysis
  - Competitive landscape
  - Digital footprint assessment
  - Industry trend mapping
  - Vendor readiness evaluation

This research feeds into both the Sales and Marketing agents,
giving them a richer foundation to build strategies on.
"""

import json
import os
import logging
from src.state import AgentState
from src.llm_client import get_ollama_client
from src.company_context import FROMNEAR_CONTEXT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _build_research_context(structured_data: dict) -> str:
    """Compile all scraped data into a research brief."""
    parts = []

    category = structured_data.get("category", "")
    location = structured_data.get("location", "")
    if category:
        parts.append(f"Category: {category}")
    if location:
        parts.append(f"Location: {location}")

    website = structured_data.get("scraped_website_content", {})
    llm_data = website.get("llm_extracted_data", {})
    regex_data = website.get("regex_extracted_data", {})

    if llm_data:
        parts.append(f"Business Summary: {llm_data.get('business_summary', 'N/A')}")
        parts.append(f"Business Model: {llm_data.get('business_model', 'N/A')}")
        products = llm_data.get("products_services", [])
        if products:
            parts.append(f"Products: {', '.join(products[:8])}")
        parts.append(f"Target Audience: {llm_data.get('target_audience', 'N/A')}")
        pricing = llm_data.get("pricing_strategy", [])
        if pricing:
            parts.append(f"Pricing: {', '.join(pricing)}")
        trust = llm_data.get("trust_signals", [])
        if trust:
            parts.append(f"Trust Signals: {', '.join(trust)}")
        channels = llm_data.get("marketing_channels", [])
        if channels:
            parts.append(f"Marketing Channels: {', '.join(channels)}")
        pain = llm_data.get("pain_points", [])
        if pain:
            parts.append(f"Pain Points: {', '.join(pain)}")
        growth = llm_data.get("growth_opportunities", [])
        if growth:
            parts.append(f"Growth Opportunities: {', '.join(growth)}")

    if regex_data:
        phones = regex_data.get("phone_numbers", [])
        emails = regex_data.get("emails", [])
        socials = regex_data.get("social_links", [])
        if phones:
            parts.append(f"Phone: {phones[0]}")
        if emails:
            parts.append(f"Email: {emails[0]}")
        if socials:
            parts.append(f"Social platforms: {len(socials)}")

    ig_list = structured_data.get("scraped_instagram_data", [])
    if ig_list:
        ig = ig_list[0]
        parts.append(f"\nInstagram: @{ig.get('username', '?')}")
        parts.append(f"Followers: {ig.get('followersCount', 0):,}")
        parts.append(f"Posts: {ig.get('postsCount', 0):,}")
        parts.append(f"IG Category: {ig.get('businessCategoryName', 'N/A')}")
        bio = ig.get("biography", "")
        if bio:
            parts.append(f"Bio: {bio}")
        posts = ig.get("latestPosts", [])
        if posts:
            for p in posts[:3]:
                cap = (p.get("caption") or "")[:80]
                likes = p.get("likesCount", 0)
                parts.append(f"  Post ({likes} likes): {cap}")

    return "\n".join(parts)


def research_agent(state: AgentState) -> AgentState:
    """
    Research Agent — deep business intelligence and competitive analysis.

    Runs AFTER input_node and BEFORE memory_node.
    Adds research_output to state for downstream agents to consume.
    """
    logger.info("=" * 50)
    logger.info("🔬 RESEARCH AGENT STARTED")
    logger.info("=" * 50)

    structured_data = state.get("structured_data", {})
    context = _build_research_context(structured_data)
    model_name = os.getenv("SALES_AGENT_MODEL", "gemma3:12b")

    prompt = f"""You are a Senior Business Research Analyst at FromNear.

{FROMNEAR_CONTEXT}

=== RAW VENDOR DATA ===
{context}

YOUR TASK: Perform a deep research analysis on this vendor/business.
This research will be used by the Sales and Marketing teams to create
personalized onboarding strategies.

Analyze and return:

1. MARKET POSITIONING: Where does this vendor sit in their local market?
   Size (small/medium/large), niche vs mainstream, price positioning.

2. COMPETITIVE LANDSCAPE: Who are their likely competitors in the same
   category and location? What is their competitive advantage?

3. DIGITAL FOOTPRINT: Rate their digital maturity (1-10).
   Website quality, social media activity, online ordering capability.

4. INDUSTRY TRENDS: 2-3 relevant industry trends that affect this vendor
   and that FromNear can leverage in the pitch.

5. VENDOR READINESS: How ready is this vendor to onboard onto a digital
   platform like FromNear? Consider tech savviness, existing digital
   presence, and scale of operations.

6. KEY INSIGHTS: 3 unique insights about this vendor that would help
   the sales and marketing teams create a compelling pitch.

Return ONLY valid JSON (no markdown, no code blocks):
{{
    "market_positioning": {{
        "size": "small/medium/large",
        "niche": "mainstream/niche/premium",
        "price_tier": "budget/mid-range/premium",
        "summary": "2-3 sentence positioning analysis"
    }},
    "competitive_landscape": {{
        "likely_competitors": ["Competitor 1", "Competitor 2"],
        "competitive_advantage": "What sets them apart",
        "market_saturation": "low/medium/high"
    }},
    "digital_footprint": {{
        "score": 7,
        "website_quality": "brief assessment",
        "social_media_presence": "brief assessment",
        "online_ordering": "yes/no/partial"
    }},
    "industry_trends": ["Trend 1", "Trend 2", "Trend 3"],
    "vendor_readiness": {{
        "score": 8,
        "strengths": ["strength 1", "strength 2"],
        "gaps": ["gap 1", "gap 2"]
    }},
    "key_insights": ["Insight 1", "Insight 2", "Insight 3"]
}}"""

    logger.info(f"🔍 Using model: {model_name}")
    logger.info(f"🔍 Prompt size: {len(prompt)} characters")

    try:
        client = get_ollama_client()
        response = client.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.2,
                "top_p": 0.7,
                "num_predict": 3000,
            },
        )

        text = response["message"]["content"]
        logger.info(f"✓ Research response: {len(text)} characters")

        try:
            research = json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                research = json.loads(match.group())
            else:
                raise ValueError("Could not parse research JSON")

        logger.info("✓ Research JSON parsed")
        logger.info(f"  Market: {research.get('market_positioning', {}).get('size', '?')}")
        logger.info(f"  Digital: {research.get('digital_footprint', {}).get('score', '?')}/10")
        logger.info(f"  Readiness: {research.get('vendor_readiness', {}).get('score', '?')}/10")
        logger.info(f"  Insights: {len(research.get('key_insights', []))}")
        logger.info("=" * 50)

        return {"research_output": research}

    except Exception as e:
        logger.error(f"✗ Research agent failed: {e}")
        return {
            "research_output": {
                "market_positioning": {"size": "unknown", "summary": "Analysis failed"},
                "competitive_landscape": {},
                "digital_footprint": {"score": 0},
                "industry_trends": [],
                "vendor_readiness": {"score": 0, "strengths": [], "gaps": []},
                "key_insights": [],
            }
        }
