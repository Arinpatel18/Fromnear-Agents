import logging
import json
import os
from typing import Dict, Any
from src.state import AgentState
from src.llm_client import get_ollama_client
from src.company_context import FROMNEAR_CONTEXT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_marketing_insights(structured_data: Dict[str, Any]) -> str:
    """Extract all relevant data from structured input for marketing generation."""
    
    website_data = structured_data.get("scraped_website_content", {})
    instagram_data = structured_data.get("scraped_instagram_data", [{}])[0] if structured_data.get("scraped_instagram_data") else {}
    
    llm_data = website_data.get("llm_extracted_data", {})
    regex_data = website_data.get("regex_extracted_data", {})
    
    # Extract category and location
    category = structured_data.get("category", "")
    location = structured_data.get("location", "")
    
    # Extract website insights
    website_summary = llm_data.get("business_summary", "")
    business_model = llm_data.get("business_model", "")
    products = llm_data.get("products_services", [])
    target_audience = llm_data.get("target_audience", "")
    growth_ops = llm_data.get("growth_opportunities", [])
    pain_points = llm_data.get("pain_points", [])
    
    # Extract Instagram insights
    ig_username = instagram_data.get("username", "")
    ig_followers = instagram_data.get("followersCount", 0)
    ig_posts = instagram_data.get("postsCount", 0)
    ig_biography = instagram_data.get("biography", "")
    ig_category = instagram_data.get("businessCategoryName", "")
    
    latest_posts = instagram_data.get("latestPosts", [])
    post_engagement = []
    post_themes = []
    for post in latest_posts[:5]:
        likes = post.get("likesCount", 0)
        caption = post.get("caption", "")[:100]
        post_engagement.append(f"Likes: {likes}, Caption: {caption}")
        if "COMBO" in caption or "combo" in caption:
            post_themes.append("Bundle offers")
        if "KIDS" in caption or "BOYS" in caption:
            post_themes.append("Kids/Boys category")
        if "₹" in caption or "/-" in caption:
            post_themes.append("Price-focused posts")
    
    contact_numbers = instagram_data.get("externalUrls", [])
    
    context = f"""
=== VENDOR DETAILS ===
Category: {category if category else 'Not specified'}
Location: {location if location else 'Not specified'}

=== VENDOR WEBSITE DATA ===
Business Summary: {website_summary}
Business Model: {business_model}
Products/Services: {', '.join(products[:5]) if products else 'Various'}
Target Audience: {target_audience}
Pain Points: {', '.join(pain_points) if pain_points else 'Not specified'}
Growth Opportunities: {', '.join(growth_ops) if growth_ops else 'Not specified'}
Contact: {regex_data.get('phone_numbers', ['Not available'])[0] if regex_data.get('phone_numbers') else 'Not available'}
Social Links: {', '.join(regex_data.get('social_links', [])[:2]) if regex_data.get('social_links') else 'Not available'}

=== VENDOR INSTAGRAM DATA ===
Account: @{ig_username}
Followers: {ig_followers:,}
Posts: {ig_posts}
Category: {ig_category}
Biography: {ig_biography}
Recent Post Themes: {', '.join(set(post_themes)) if post_themes else 'Product showcase, pricing'}
Post Engagement Sample: {post_engagement[0] if post_engagement else 'Not available'}
"""
    return context


def _format_memory_for_marketing(memory_context: dict) -> str:
    """Format past analyses into marketing-relevant context."""
    similar = memory_context.get("similar_vendors", [])
    if not similar:
        return "\n(No past vendor launch data for similar categories — this is a first.)\n"

    lines = ["\n=== MEMORY: PAST VENDOR LAUNCHES IN SIMILAR CATEGORIES ==="]
    for i, v in enumerate(similar, 1):
        lines.append(
            f"{i}. {v['domain']} ({v['category']}, {v['location']}) "
            f"— Lead Score: {v['lead_score']}/10"
        )
    lines.append("Use these past launches to maintain consistency and build on learnings.\n")
    return "\n".join(lines)


def generate_marketing_output(
    structured_data: Dict[str, Any],
    memory_context: dict,
    model_name: str = "gemma3:12b",
) -> Dict[str, Any]:
    """
    Generate marketing strategies for FromNear to promote this vendor
    after they are onboarded onto the platform.
    
    The Marketing Agent acts as FromNear's marketing team planning how to
    launch and grow this vendor's presence on the FromNear platform.
    """
    logger.info("=" * 60)
    logger.info("MARKETING AGENT STARTED (FromNear Vendor Launch)")
    logger.info("=" * 60)
    
    context = extract_marketing_insights(structured_data)
    memory_text = _format_memory_for_marketing(memory_context)
    logger.info("✓ Vendor context extracted from website + Instagram data")
    logger.info(f"🧠 Memory context: {memory_context.get('total_past_analyses', 0)} similar vendor(s)")
    
    # Single comprehensive prompt
    prompt = f"""You are FromNear's Head of Marketing. Your job is to create marketing strategies
to promote a newly onboarded vendor on the FromNear platform.

{FROMNEAR_CONTEXT}

{context}

{memory_text}

YOUR TASK: This vendor has just been onboarded onto FromNear. Create a complete
marketing plan to launch their presence on the platform and drive customers to
discover and buy from them through FromNear.

Generate the following:

1. REASONING: 3-5 sentences explaining your marketing strategy rationale.
   Why these campaigns? What data drove your decisions?

2. CONFIDENCE LEVEL: Rate your confidence (0.0 to 1.0) in these recommendations.

3. AD CAMPAIGN IDEAS: 2-3 ad campaigns FromNear can run to promote this vendor.

4. INSTAGRAM CONTENT IDEAS: 3 Instagram posts/stories FromNear can create.

5. LAUNCH CAMPAIGN CONCEPTS: 2 launch campaign ideas for the vendor going live.

6. REELS/POST HOOKS: 3 attention-grabbing hooks for short-form video content.

7. GROWTH SUGGESTIONS: 3 strategies to grow this vendor's sales on FromNear
   over the first 90 days.

IMPORTANT:
- You are marketing FROM FromNear's perspective — promoting this vendor TO local customers
- Reference the vendor's actual products, location, Instagram handle, follower count
- Make all suggestions hyperlocal — mention the specific city/area

Return ONLY valid JSON (no markdown, no code blocks):
{{
    "reasoning": "Your marketing strategy rationale...",
    "confidence_level": 0.85,
    "ad_campaigns": [
        {{"name": "Campaign Name", "platform": "Platform", "duration": "Duration", "hook": "Main hook/angle"}}
    ],
    "instagram_content_calendar": [
        {{"day": "Monday", "post_type": "Type", "idea": "Post idea", "hashtags": "#tag1 #tag2"}}
    ],
    "launch_campaigns": [
        {{"title": "Campaign Title", "focus": "Focus", "tactics": ["Tactic 1", "Tactic 2"]}}
    ],
    "reels_and_hooks": [
        {{"hook": "Attention-grabbing text", "platform": "Reel/Shorts", "cta": "Call to action"}}
    ],
    "growth_strategies": [
        {{"strategy": "Strategy name", "action": "Specific action", "expected_impact": "Impact"}}
    ]
}}"""

    try:
        logger.info(f"🔍 Using model: {model_name}")
        logger.info(f"🔍 Prompt size: {len(prompt)} characters")
        
        client = get_ollama_client()
        response = client.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.3,
                "num_predict": 4000,
                "top_p": 0.7,
                "top_k": 20
            }
        )
        
        content = response["message"]["content"].strip()
        logger.info(f"✓ LLM Response received: {len(content)} characters")
        
        # Extract JSON from response
        import re as regex_module
        json_match = regex_module.search(r'\{.*\}', content, regex_module.DOTALL)
        
        if json_match:
            marketing_output = json.loads(json_match.group(0))
            logger.info("✓ Marketing JSON parsed successfully")
        else:
            logger.error("✗ Could not extract JSON from response")
            return {"error": "JSON extraction failed", "raw_response": content[:500]}
        
        # Log summary
        logger.info("=" * 60)
        logger.info("MARKETING OUTPUT SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✓ Reasoning: {len(marketing_output.get('reasoning', ''))} chars")
        logger.info(f"✓ Confidence: {marketing_output.get('confidence_level', 'N/A')}")
        logger.info(f"✓ Ad Campaigns: {len(marketing_output.get('ad_campaigns', []))} ideas")
        logger.info(f"✓ Instagram Calendar: {len(marketing_output.get('instagram_content_calendar', []))} posts planned")
        logger.info(f"✓ Launch Campaigns: {len(marketing_output.get('launch_campaigns', []))} campaigns")
        logger.info(f"✓ Reels & Hooks: {len(marketing_output.get('reels_and_hooks', []))} hooks created")
        logger.info(f"✓ Growth Strategies: {len(marketing_output.get('growth_strategies', []))} strategies")
        logger.info("=" * 60)
        
        return marketing_output
        
    except json.JSONDecodeError as e:
        logger.error(f"✗ JSON Parse Error: {str(e)}")
        return {"reasoning": "Parse error", "confidence_level": 0.0, "error": f"JSON parse failed: {str(e)}"}
    except Exception as e:
        logger.exception(f"✗ Error in marketing generation: {str(e)}")
        return {"reasoning": "Generation error", "confidence_level": 0.0, "error": str(e)}


def marketing_agent(state: AgentState) -> AgentState:
    """
    Marketing Agent Node — FromNear Vendor Launch Marketing (Memory-Augmented).
    """
    structured_data = state.get("structured_data", {})
    memory_context = state.get("memory_context", {})
    
    if not structured_data:
        logger.error("✗ No structured data provided to marketing agent")
        return {"marketing_output": {}}
    
    try:
        model_name = os.getenv("MARKETING_AGENT_MODEL", "gemma3:12b")
        marketing_output = generate_marketing_output(structured_data, memory_context, model_name)
        
        logger.info("✓ Marketing agent completed successfully")
        return {"marketing_output": marketing_output}
        
    except Exception as e:
        logger.exception(f"✗ Error in marketing_agent: {str(e)}")
        return {"marketing_output": {"error": str(e)}}
