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


def generate_sales_output(structured_data: dict, model_name: str = "gemma3:12b") -> dict:
    """
    Generate a personalized vendor onboarding strategy for FromNear.
    
    The Sales Agent acts as a FromNear business development representative
    analyzing a potential vendor/retailer and crafting a strategy to onboard
    them onto the FromNear platform.
    
    Returns dict with: business_summary, pain_point_analysis, qualification_score,
                       outreach_strategy, personalized_sales_pitch, follow_up_suggestions
    """
    logger.info("=" * 50)
    logger.info("SALES AGENT STARTED (FromNear Onboarding)")
    logger.info("=" * 50)
    
    # Extract context about the vendor/prospect
    vendor_context = extract_sales_insights(structured_data)
    logger.info("✓ Vendor context extracted from website + Instagram data")
    logger.info(f"🔍 Using model: {model_name}")
    
    # Create FromNear onboarding-specific prompt
    prompt = f"""You are a senior Business Development Manager at FromNear.

{FROMNEAR_CONTEXT}

=== VENDOR / PROSPECT DATA (the business you want to ONBOARD onto FromNear) ===
{vendor_context}

YOUR TASK: Analyze this vendor and create a personalized onboarding strategy to
convince them to join the FromNear platform as a seller. Use their specific
business details, location, category, Instagram presence, and pain points to
craft a compelling, tailored pitch.

Generate the following:

1. BUSINESS SUMMARY: 2-3 sentence overview of who this vendor is, what they sell,
   and their current digital presence. Identify what makes them a good fit for FromNear.

2. PAIN POINT ANALYSIS: 2-3 specific pain points this vendor likely faces that
   FromNear can solve (e.g., limited online reach, high delivery costs, no app presence,
   inventory management challenges, competition from big e-commerce, etc.)

3. QUALIFICATION SCORE: Rate this vendor 1-10 as a FromNear onboarding prospect.
   Consider: local presence, product-market fit, digital readiness, category demand.

4. OUTREACH STRATEGY: 2-3 specific, actionable steps to reach and engage this vendor.
   Include the channel (in-person visit, WhatsApp, email, Instagram DM, phone call),
   the opening message angle, and why that approach works for THIS specific vendor.

5. PERSONALIZED ONBOARDING PITCH: Write 2-3 compelling value propositions
   specifically tailored for THIS vendor explaining why they should join FromNear.
   Reference their actual products, location, audience, and pain points.
   Example tone: "Your {{category}} store in {{location}} already has {{followers}} loyal
   followers — imagine reaching 10x more customers in your neighborhood through FromNear."

6. FOLLOW-UP SUGGESTIONS: 2-3 follow-up actions with specific timing and content.
   Include what to send, when to send it, and what outcome to aim for.

IMPORTANT:
- You are pitching FROM FromNear TO this vendor — not advising the vendor
- Reference the vendor's actual data (name, location, products, followers, etc.)
- Make it personal, specific, and compelling — not generic
- Focus on how FromNear solves THEIR specific problems

Return ONLY valid JSON (no markdown, no code blocks):
{{
    "business_summary": "...",
    "pain_point_analysis": ["...", "...", "..."],
    "qualification_score": {{"score": 8, "reason": "..."}},
    "outreach_strategy": ["...", "...", "..."],
    "personalized_sales_pitch": ["...", "...", "..."],
    "follow_up_suggestions": ["...", "...", "..."]
}}"""
    
    logger.info(f"🔍 Prompt size: {len(prompt)} characters")
    
    try:
        # Single LLM call via shared cloud-aware client
        client = get_ollama_client()
        response = client.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.3,
                "top_p": 0.7,
                "top_k": 20,
                "num_predict": 4000
            }
        )
        
        response_text = response["message"]["content"]
        logger.info(f"✓ LLM Response received: {len(response_text)} characters")
        
        # Extract JSON from response
        try:
            sales_json = json.loads(response_text)
        except json.JSONDecodeError:
            # Try regex extraction if pure JSON parse fails
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
        logger.info(f"✓ Business Summary: Generated")
        logger.info(f"✓ Pain Point Analysis: {len(sales_json.get('pain_point_analysis', []))} points")
        logger.info(f"✓ Qualification Score: {sales_json.get('qualification_score', {}).get('score', 'N/A')}/10")
        logger.info(f"✓ Outreach Strategy: {len(sales_json.get('outreach_strategy', []))} tactics")
        logger.info(f"✓ Sales Pitches: {len(sales_json.get('personalized_sales_pitch', []))} pitches")
        logger.info(f"✓ Follow-up Actions: {len(sales_json.get('follow_up_suggestions', []))} actions")
        logger.info("=" * 50)
        
        return sales_json
    
    except Exception as e:
        logger.error(f"✗ Error generating sales output: {str(e)}")
        return {
            "business_summary": "Error generating summary",
            "pain_point_analysis": [],
            "qualification_score": {"score": 0, "reason": "Error"},
            "outreach_strategy": [],
            "personalized_sales_pitch": [],
            "follow_up_suggestions": []
        }


def sales_agent(state: AgentState) -> AgentState:
    """
    AI Sales Agent Node — FromNear Vendor Onboarding.
    Analyzes a potential vendor and generates a personalized onboarding strategy
    to convince them to join the FromNear platform.
    
    Outputs:
    - business_summary: Overview of the vendor and their fit for FromNear
    - pain_point_analysis: Vendor pain points that FromNear solves
    - qualification_score: Onboarding prospect rating
    - outreach_strategy: How to approach and engage this vendor
    - personalized_sales_pitch: Tailored pitch to join FromNear
    - follow_up_suggestions: Follow-up actions with timing
    """
    structured_data = state.get("structured_data", {})
    
    # Read model from env
    model_name = os.getenv("SALES_AGENT_MODEL", "gemma3:12b")
    
    # Generate sales output (synchronous — no asyncio.run needed)
    sales_output = generate_sales_output(structured_data, model_name)
    
    return {"sales_output": sales_output}
