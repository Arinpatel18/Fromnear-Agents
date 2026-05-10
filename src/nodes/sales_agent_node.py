import json
import os
import logging
from src.state import AgentState
from src.llm_client import get_ollama_client
from src.company_context import FROMNEAR_CONTEXT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_sales_insights(structured_data: dict) -> str:
    """
    Extract and combine insights from website and Instagram data for sales context.
    Returns formatted context string for LLM.
    """
    context_parts = []

    # Extract category and location
    category = structured_data.get("category", "")
    location = structured_data.get("location", "")

    if category:
        context_parts.append(f"Business Category: {category}")
    if location:
        context_parts.append(f"Business Location: {location}")

    # Extract website data
    website_data = structured_data.get("scraped_website_content", {})
    llm_data = website_data.get("llm_extracted_data", {})
    regex_data = website_data.get("regex_extracted_data", {})

    # Extract Instagram data
    ig_data_list = structured_data.get("scraped_instagram_data", [])

    # Build context
    if llm_data:
        context_parts.append(f"Business Summary: {llm_data.get('business_summary', 'N/A')}")
        context_parts.append(f"Business Model: {llm_data.get('business_model', 'N/A')}")

        products = llm_data.get("products_services", [])
        if products:
            context_parts.append(f"Products/Services: {', '.join(products)}")

        context_parts.append(f"Target Audience: {llm_data.get('target_audience', 'N/A')}")

        pricing = llm_data.get("pricing_strategy", [])
        if pricing:
            context_parts.append(f"Pricing: {', '.join(pricing)}")

        pain_points = llm_data.get("pain_points", [])
        if pain_points:
            context_parts.append(f"Known Pain Points: {', '.join(pain_points)}")

        growth_ops = llm_data.get("growth_opportunities", [])
        if growth_ops:
            context_parts.append(f"Growth Opportunities: {', '.join(growth_ops)}")

    # Add contact info
    if regex_data:
        phones = regex_data.get("phone_numbers", [])
        if phones:
            context_parts.append(f"Contact Phone: {phones[0]}")

        emails = regex_data.get("emails", [])
        if emails:
            context_parts.append(f"Contact Email: {emails[0]}")

        socials = regex_data.get("social_links", [])
        if socials:
            context_parts.append(f"Social Presence: {len(socials)} platforms")

    # Add Instagram insights
    if ig_data_list and len(ig_data_list) > 0:
        ig = ig_data_list[0]
        context_parts.append(f"\nInstagram Profile: @{ig.get('username', 'N/A')}")
        context_parts.append(f"Followers: {ig.get('followersCount', 0):,}")
        context_parts.append(f"Total Posts: {ig.get('postsCount', 0):,}")
        context_parts.append(f"Instagram Category: {ig.get('businessCategoryName', 'N/A')}")

        bio = ig.get("biography", "")
        if bio:
            context_parts.append(f"Bio: {bio}")

        posts = ig.get("latestPosts", [])
        if posts:
            captions = [p.get('caption', '')[:80] for p in posts if p.get('caption')]
            if captions:
                context_parts.append(f"Recent Posts: {' | '.join(captions)}")

    return "\n".join(context_parts)


def _format_memory_context(memory_context: dict) -> str:
    """Format past analyses into a prompt-friendly string."""
    similar = memory_context.get("similar_vendors", [])
    if not similar:
        return "\n(No previous analyses for similar vendors — this is a fresh category/location.)\n"

    lines = ["\n=== MEMORY: PAST SIMILAR VENDOR ANALYSES ==="]
    for i, v in enumerate(similar, 1):
        lines.append(
            f"{i}. {v['domain']} ({v['category']}, {v['location']}) "
            f"— Lead Score: {v['lead_score']}/10, Confidence: {v['confidence']:.0%}"
        )
        if v.get("sales_summary"):
            lines.append(f"   Summary: {v['sales_summary'][:200]}")
    lines.append("Use these past analyses to stay consistent and refine your scoring.\n")
    return "\n".join(lines)


def generate_sales_output(
    structured_data: dict,
    memory_context: dict,
    model_name: str = "gemma3:12b",
) -> dict:
    """
    Generate a personalized vendor onboarding strategy for FromNear.

    Now includes:
    - Reasoning trace (chain-of-thought)
    - Lead score with breakdown (digital_presence, market_fit, growth_potential, engagement_quality)
    - Confidence level (0.0–1.0)
    - Actionable next steps with priority + timeline
    - Memory-augmented context from past analyses
    """
    logger.info("=" * 50)
    logger.info("SALES AGENT STARTED (FromNear Onboarding + Memory)")
    logger.info("=" * 50)

    vendor_context = extract_sales_insights(structured_data)
    memory_text = _format_memory_context(memory_context)
    logger.info("✓ Vendor context extracted from website + Instagram data")
    logger.info(f"🧠 Memory context: {memory_context.get('total_past_analyses', 0)} similar vendor(s)")
    logger.info(f"🔍 Using model: {model_name}")

    prompt = f"""You are a senior Business Development Manager at FromNear.

{FROMNEAR_CONTEXT}

=== VENDOR / PROSPECT DATA (the business you want to ONBOARD onto FromNear) ===
{vendor_context}

{memory_text}

YOUR TASK: Analyze this vendor and create a personalized onboarding strategy to
convince them to join the FromNear platform as a seller.

Generate the following:

1. REASONING: Write 3-5 sentences explaining your chain-of-thought analysis.
   Why is this vendor a good/bad fit? What stands out? What concerns do you have?

2. CONFIDENCE LEVEL: Rate your overall confidence (0.0 to 1.0) in this analysis.
   Consider: how much data you have, quality of sources, clarity of vendor profile.

3. BUSINESS SUMMARY: 2-3 sentence overview of who this vendor is and their fit for FromNear.

4. LEAD SCORE: Rate this vendor as a FromNear onboarding prospect.
   Provide an overall score (1-10) AND a breakdown:
   - digital_presence (1-10): Website quality, social media activity, online visibility
   - market_fit (1-10): How well their products/category fits FromNear's hyperlocal model
   - growth_potential (1-10): Room to grow with FromNear (underserved area, scaling needs)
   - engagement_quality (1-10): Instagram engagement, customer interaction, brand loyalty

5. PAIN POINT ANALYSIS: 3 specific pain points this vendor faces that FromNear solves.

6. OUTREACH STRATEGY: 3 specific steps to reach and engage this vendor.
   Include channel, message angle, and why it works for THIS vendor.

7. PERSONALIZED ONBOARDING PITCH: 3 compelling, personalized value propositions
   tailored for THIS vendor. Reference their actual data.

8. FOLLOW-UP SUGGESTIONS: 3 follow-up actions with specific timing and content.

9. ACTIONABLE NEXT STEPS: 3 concrete actions with priority (high/medium/low),
   timeline (e.g., "Day 1", "Week 1"), and owner (e.g., "BD Team", "Marketing").

Return ONLY valid JSON (no markdown, no code blocks):
{{
    "reasoning": "Your chain-of-thought analysis...",
    "confidence_level": 0.85,
    "business_summary": "...",
    "lead_score": {{
        "overall": 8,
        "reason": "Brief reason for the score",
        "breakdown": {{
            "digital_presence": 7,
            "market_fit": 9,
            "growth_potential": 8,
            "engagement_quality": 7
        }}
    }},
    "pain_point_analysis": ["...", "...", "..."],
    "outreach_strategy": ["...", "...", "..."],
    "personalized_sales_pitch": ["...", "...", "..."],
    "follow_up_suggestions": ["...", "...", "..."],
    "actionable_next_steps": [
        {{"action": "...", "priority": "high", "timeline": "Day 1", "owner": "BD Team"}},
        {{"action": "...", "priority": "medium", "timeline": "Week 1", "owner": "Marketing"}},
        {{"action": "...", "priority": "low", "timeline": "Week 2", "owner": "BD Team"}}
    ]
}}"""

    logger.info(f"🔍 Prompt size: {len(prompt)} characters")

    try:
        client = get_ollama_client()
        response = client.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.3,
                "top_p": 0.7,
                "top_k": 20,
                "num_predict": 5000,
            },
        )

        response_text = response["message"]["content"]
        logger.info(f"✓ LLM Response received: {len(response_text)} characters")

        # Extract JSON from response
        try:
            sales_json = json.loads(response_text)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                sales_json = json.loads(match.group())
            else:
                raise ValueError("Could not extract JSON from LLM response")

        logger.info("✓ Sales JSON parsed successfully")
        logger.info("=" * 50)
        logger.info("SALES OUTPUT SUMMARY")
        logger.info("=" * 50)

        lead = sales_json.get("lead_score", {})
        logger.info(f"✓ Reasoning: {len(sales_json.get('reasoning', ''))} chars")
        logger.info(f"✓ Confidence: {sales_json.get('confidence_level', 'N/A')}")
        logger.info(f"✓ Lead Score: {lead.get('overall', 'N/A')}/10")

        breakdown = lead.get("breakdown", {})
        if breakdown:
            logger.info(f"   Digital: {breakdown.get('digital_presence', '?')}/10 | "
                        f"Fit: {breakdown.get('market_fit', '?')}/10 | "
                        f"Growth: {breakdown.get('growth_potential', '?')}/10 | "
                        f"Engage: {breakdown.get('engagement_quality', '?')}/10")

        logger.info(f"✓ Pain Points: {len(sales_json.get('pain_point_analysis', []))}")
        logger.info(f"✓ Outreach: {len(sales_json.get('outreach_strategy', []))}")
        logger.info(f"✓ Pitches: {len(sales_json.get('personalized_sales_pitch', []))}")
        logger.info(f"✓ Follow-ups: {len(sales_json.get('follow_up_suggestions', []))}")
        logger.info(f"✓ Next Steps: {len(sales_json.get('actionable_next_steps', []))}")
        logger.info("=" * 50)

        return sales_json

    except Exception as e:
        logger.error(f"✗ Error generating sales output: {str(e)}")
        return {
            "reasoning": "Analysis failed due to an error.",
            "confidence_level": 0.0,
            "business_summary": "Error generating summary",
            "lead_score": {
                "overall": 0,
                "reason": "Error",
                "breakdown": {
                    "digital_presence": 0,
                    "market_fit": 0,
                    "growth_potential": 0,
                    "engagement_quality": 0,
                },
            },
            "pain_point_analysis": [],
            "outreach_strategy": [],
            "personalized_sales_pitch": [],
            "follow_up_suggestions": [],
            "actionable_next_steps": [],
        }


def sales_agent(state: AgentState) -> AgentState:
    """
    AI Sales Agent Node — FromNear Vendor Onboarding (Memory-Augmented).
    """
    structured_data = state.get("structured_data", {})
    memory_context = state.get("memory_context", {})

    model_name = os.getenv("SALES_AGENT_MODEL", "gemma3:12b")

    sales_output = generate_sales_output(structured_data, memory_context, model_name)

    return {"sales_output": sales_output}
