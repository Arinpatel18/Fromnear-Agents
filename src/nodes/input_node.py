import os
import sys
import asyncio
import logging
import re
import json
from urllib.parse import urlparse

from src.state import AgentState
from src.llm_client import get_ollama_client

# Configure logging with better formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



# -----------------------------------
# Noise patterns
# -----------------------------------
NOISE_PATTERNS = [
    r"javascript:void\(0\)",
    r"scroll to top",
    r"privacy policy",
    r"terms and conditions",
    r"copyright",
    r"all rights reserved",
    r"sign in",
    r"login",
    r"register",
    r"allow notifications",
    r"cookie policy"
]


# -----------------------------------
# Step 1 → Hard filtering
# -----------------------------------
def clean_markdown(markdown_text: str) -> str:
    lines = markdown_text.split("\n")
    cleaned_lines = []
    seen = set()

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # remove markdown image placeholders
        if line.startswith("![]("):
            continue

        # remove very small junk lines
        if len(line) < 3:
            continue

        # deduplicate repeated content
        if line in seen:
            continue

        is_noise = False
        for pattern in NOISE_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                is_noise = True
                break

        if is_noise:
            continue

        seen.add(line)
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


# -----------------------------------
# Step 2 → Regex extraction
# -----------------------------------
def extract_structured_data(text: str):
    phone_numbers = list(
        set(re.findall(r'\b\d{10}\b', text))
    )

    emails = list(
        set(
            re.findall(
                r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
                text
            )
        )
    )

    pricing = list(
        set(
            re.findall(
                r'(₹\s?\d+|Rs\.?\s?\d+|\$\s?\d+)',
                text
            )
        )
    )

    social_links = list(
        set(
            re.findall(
                r'https?://(?:www\.)?(?:instagram|facebook|linkedin|twitter|youtube)\.[^\s)]+',
                text
            )
        )
    )

    return {
        "phone_numbers": phone_numbers,
        "emails": emails,
        "pricing_signals": pricing,
        "social_links": social_links
    }


# -----------------------------------# Step 2b → Hallucination validation
# -----------------------------------
def validate_llm_output(extracted_data: dict, source_text: str, regex_data: dict, threshold: float = 0.2) -> dict:
    """
    Validate LLM output against source content to prevent hallucinations.
    Allows data from regex extraction and content, but flags completely invented data.
    """
    source_lower = source_text.lower()
    
    # Build a combined searchable text including regex data
    combined_text = source_lower
    for key, values in regex_data.items():
        if isinstance(values, list):
            for val in values:
                combined_text += " " + str(val).lower()
        else:
            combined_text += " " + str(values).lower()
    
    validation_report = {}
    
    for field, value in extracted_data.items():
        if value == "Not found" or not value:
            validation_report[field] = {"status": "empty", "found_refs": 0}
            continue
            
        # For strings
        if isinstance(value, str):
            words = [w for w in value.split() if len(w) > 3]
            refs_found = sum(1 for word in words if word.lower() in combined_text)
            ratio = refs_found / len(words) if words else 0
            
            status = "verified" if ratio > threshold else "suspicious"
            validation_report[field] = {
                "status": status,
                "found_refs": refs_found,
                "word_coverage": f"{ratio*100:.0f}%"
            }
            if status == "suspicious" and ratio == 0:
                logger.warning(f"⚠ Field '{field}' may be hallucinated (0% phrase match)")
        
        # For arrays
        elif isinstance(value, list):
            if not value or all(v == "Information unavailable" for v in value):
                validation_report[field] = {"status": "empty", "items": len(value)}
                continue
            
            valid_items = []
            for item in value:
                if isinstance(item, str):
                    words = [w for w in item.split() if len(w) > 3]
                    refs_found = sum(1 for w in words if w.lower() in combined_text)
                    if refs_found > 0 or len(words) == 0:
                        valid_items.append(item)
                    else:
                        logger.debug(f"⚠ Skipping likely hallucinated item: {item[:60]}")
            
            status = "verified" if len(valid_items) > 0 else "suspicious"
            validation_report[field] = {
                "status": status,
                "verified_items": len(valid_items),
                "total_items": len(value)
            }
            
            if len(valid_items) > 0:
                extracted_data[field] = valid_items
                if len(valid_items) < len(value):
                    logger.info(f"✓ Filtered '{field}': kept {len(valid_items)}/{len(value)} verified items")
    
    verified_count = sum(1 for v in validation_report.values() if v.get('status') == 'verified' or v.get('status') == 'empty')
    logger.info(f"✓ Validation complete: {verified_count}/{len(validation_report)} fields passed")
    return extracted_data


# -----------------------------------# Step 3 → LLM semantic extraction
# -----------------------------------
async def llm_extract_business_data(cleaned_text: str, regex_data: dict) -> dict:
    """Extract comprehensive business intelligence using LLM."""
    logger.info("Starting LLM-based business data extraction...")
    
    prompt = f"""You are a data organizer. Your task is to use the provided data to populate all fields.

CRITICAL RULES:
1. Use ONLY the website content and regex data provided below
2. Organize, synthesize, and structure all available data into JSON fields
3. DO NOT add information from your training data or general knowledge
4. DO NOT hallucinate or invent facts
5. For fields where data exists, actively use ALL of it to populate the field
6. Use regex-extracted data actively in your response

Website Content (First 20000 characters):
{cleaned_text[:20000]}

Regex Pre-extracted Data (ACTIVELY USE THIS):
Phone Numbers: {json.dumps(regex_data.get('phone_numbers', []))}
Emails: {json.dumps(regex_data.get('emails', []))}
Pricing Signals: {json.dumps(regex_data.get('pricing_signals', []))}
Social Links: {json.dumps(regex_data.get('social_links', []))}

Full Regex Data:
{json.dumps(regex_data, indent=2)}

Task: Organize and structure the provided data into JSON.

{{
    "business_summary": "Brief description based on website content about what this business does",
    "business_model": "Based on website content, how they operate/generate revenue",
    "products_services": ["Use product categories and mentions from website content"],
    "pricing_strategy": ["Use pricing signals found: {regex_data.get('pricing_signals', [])} plus pricing from content"],
    "active_promotions": ["Extract current offers or deals mentioned in content"],
    "target_audience": "Based on content, who is the target customer",
    "trust_signals": ["Include social links: {regex_data.get('social_links', [])} and trust indicators from content"],
    "marketing_channels": ["Extract from social links: {regex_data.get('social_links', [])} and other marketing mentions"],
    "pain_points": ["Problems the business addresses based on content"],
    "growth_opportunities": ["Potential growth areas based on content"]
}}

IMPORTANT: Actively use all provided regex data. Include discovered contact information and links.
Return ONLY valid JSON, nothing else."""

    try:
        # Try to use specified model or default to llama3
        model_name = os.getenv("SALES_AGENT_MODEL", "llama3:latest")
        logger.info(f"🔍 LLM Model: {model_name}")
        logger.info(f"🔍 Prompt size: {len(prompt)} characters")
        
        client = get_ollama_client()
        response = client.chat(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0.0,
                "num_predict": 2000,
                "top_p": 0.5,
                "top_k": 10
            }
        )

        logger.info(f"🔍 Response type: {type(response)}")
        logger.info(f"🔍 Response keys: {response.keys() if isinstance(response, dict) else 'N/A'}")
        
        if "message" not in response:
            logger.error(f"✗ No 'message' key in response: {response}")
            return {}
        
        if "content" not in response["message"]:
            logger.error(f"✗ No 'content' key in message: {response['message']}")
            return {}
        
        content = response["message"]["content"].strip()
        logger.info(f"🔍 Raw LLM response length: {len(content)} characters")
        logger.debug(f"🔍 First 500 chars of response: {content[:500]}")
        
        if not content:
            logger.error("✗ LLM returned empty content")
            return {}
        
        # Log raw response for debugging
        if content.startswith("I cannot") or content.startswith("I'm not") or content.startswith("I don't"):
            logger.warning(f"✗ LLM declined to process: {content[:200]}")
            return {}
        
        # Try to extract JSON if wrapped in markdown
        if "```json" in content:
            logger.info("ℹ Extracting JSON from ```json block")
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            logger.info("ℹ Extracting JSON from code block")
            content = content.split("```")[1].split("```")[0].strip()
        
        logger.debug(f"🔍 Cleaned response (first 300 chars): {content[:300]}")
        
        # Extract JSON from the response even if there's preamble text
        import re as regex_module
        json_match = regex_module.search(r'\{.*\}', content, regex_module.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
            logger.info(f"ℹ Extracted JSON from response using regex")
        else:
            json_str = content
        
        extracted_data = json.loads(json_str)
        logger.info(f"✓ Successfully extracted {len(extracted_data)} business intelligence fields")
        logger.info(f"✓ Fields: {list(extracted_data.keys())}")
        
        # Validate extracted data against source content to prevent hallucinations
        logger.info("🔍 Validating extracted data against source content...")
        extracted_data = validate_llm_output(extracted_data, cleaned_text, regex_data)
        
        return extracted_data

    except json.JSONDecodeError as e:
        logger.error(f"✗ JSON Decode Error: {str(e)}")
        logger.error(f"✗ Response snippet: {content[:300] if 'content' in locals() else 'N/A'}")
        return {}
    except Exception as conn_err:
        if "ResponseError" in type(conn_err).__name__ or "response" in str(conn_err).lower():
            logger.error(f"✗ Ollama Response Error: {str(conn_err)}")
        else:
            raise conn_err
        logger.info("💡 Fallback: Returning structured template with regex data")
        # Return a template populated with regex data
        return {
            "business_summary": f"Business located at {regex_data.get('social_links', ['Unknown'])[0] if regex_data.get('social_links') else 'Unknown'}. Contact: {regex_data.get('phone_numbers', ['Not provided'])[0] if regex_data.get('phone_numbers') else 'Not provided'}",
            "business_model": "Unable to determine - LLM service unavailable",
            "products_services": ["Information unavailable"],
            "pricing_strategy": ["Information from regex: " + (str(regex_data.get('pricing_signals', ['Not found'])[0]) if regex_data.get('pricing_signals') else 'Not found')],
            "active_promotions": ["Information unavailable"],
            "target_audience": "Information unavailable",
            "trust_signals": regex_data.get('social_links', []),
            "marketing_channels": [link.split('/')[-1] for link in regex_data.get('social_links', [])],
            "pain_points": ["Information unavailable"],
            "growth_opportunities": ["Information unavailable"]
        }
    except Exception as e:
        logger.exception(f"✗ Unexpected error during LLM extraction: {str(e)}")
        import traceback
        logger.error(f"✗ Traceback: {traceback.format_exc()}")
        return {}


# -----------------------------------
# Main website scraper
# -----------------------------------
async def scrape_website(url: str) -> dict:
    """Scrape and analyze website content using crawl4ai and LLM."""
    if not url:
        logger.warning("No URL provided for website scraping")
        return {}

    logger.info(f"Starting website scrape: {url}")

    try:
        # Lazy import — crawl4ai loads Playwright browser engine which is very heavy
        from crawl4ai import AsyncWebCrawler

        # Step 0: Crawl website with crawl4ai
        logger.debug("Fetching website content with Crawl4AI...")
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)

        raw_markdown = result.markdown
        logger.info(f"✓ Raw markdown retrieved: {len(raw_markdown)} characters")

        # Step 1: Hard clean
        logger.debug("Step 1: Cleaning and denoising markdown...")
        cleaned_markdown = clean_markdown(raw_markdown)
        logger.info(f"✓ Cleaned markdown: {len(cleaned_markdown)} characters (removed {len(raw_markdown) - len(cleaned_markdown)} noisy characters)")

        # Step 2: Regex extraction
        logger.debug("Step 2: Extracting contact info and social links via regex...")
        regex_data = extract_structured_data(cleaned_markdown)
        logger.info(f"✓ Regex extraction: Found {len(regex_data['phone_numbers'])} phone(s), {len(regex_data['emails'])} email(s), {len(regex_data['social_links'])} social link(s)")

        # Step 3: LLM extraction
        logger.debug("Step 3: Running LLM for semantic analysis...")
        llm_data = await llm_extract_business_data(cleaned_markdown, regex_data)
        
        if llm_data:
            logger.info(f"✓ LLM extraction successful: {len(llm_data)} intelligence fields populated")
        else:
            logger.warning("⚠ LLM extraction returned empty data")

        final_output = {
            "website_url": url,
            "domain": urlparse(url).netloc,
            "raw_markdown_length": len(raw_markdown),
            "cleaned_markdown_length": len(cleaned_markdown),
            "regex_extracted_data": regex_data,
            "llm_extracted_data": llm_data
        }

        logger.info("✓ Website scraping completed successfully")
        return final_output

    except Exception as e:
        logger.exception(f"✗ Website scraping failed for {url}: {str(e)}")
        return {}

MAX_POSTS = 5


def clean_external_urls(external_urls):
    """
    Keep only title + url from external URLs
    """
    if not isinstance(external_urls, list):
        return []

    cleaned = []
    for link in external_urls:
        cleaned.append({
            "title": link.get("title", ""),
            "url": link.get("url", "")
        })

    return cleaned


def clean_tagged_users(tagged_users):
    """
    Keep only required tagged user fields
    """
    if not isinstance(tagged_users, list):
        return []

    cleaned = []
    for user in tagged_users:
        cleaned.append({
            "full_name": user.get("full_name", ""),
            "username": user.get("username", "")
        })

    return cleaned


def clean_posts(posts):
    """
    Keep only required post fields
    """
    if not isinstance(posts, list):
        return []

    cleaned_posts = []

    for post in posts[:MAX_POSTS]:
        cleaned_post = {
            "type": post.get("type", ""),
            "caption": post.get("caption", ""),
            "hashtags": post.get("hashtags", []),
            "mentions": post.get("mentions", []),
            "likesCount": post.get("likesCount"),
            "commentsCount": post.get("commentsCount"),
            "videoViewCount": post.get("videoViewCount"),
            "timestamp": post.get("timestamp"),
            "productType": post.get("productType", ""),
            "images": post.get("images", []),
            "taggedUsers": clean_tagged_users(
                post.get("taggedUsers", [])
            )
        }

        cleaned_posts.append(cleaned_post)

    return cleaned_posts


def clean_profile_data(item):
    """
    Keep only required top-level profile fields
    """
    return {
        "username": item.get("username", ""),
        "url": item.get("url", ""),
        "fullName": item.get("fullName", ""),
        "biography": item.get("biography", ""),
        "followersCount": item.get("followersCount"),
        "followsCount": item.get("followsCount"),
        "postsCount": item.get("postsCount"),
        "highlightReelCount": item.get("highlightReelCount"),
        "businessCategoryName": item.get("businessCategoryName", ""),
        "verified": item.get("verified"),
        "externalUrls": clean_external_urls(
            item.get("externalUrls", [])
        ),
        "latestPosts": clean_posts(
            item.get("latestPosts", [])
        )
    }


def scrape_instagram(profile_url: str) -> list:
    if not profile_url:
        return []

    apify_token = os.environ.get("APIFY_API_TOKEN")
    if not apify_token:
        logger.warning("APIFY_API_TOKEN not set.")
        return []

    try:
        # Lazy import — avoid loading at startup
        from apify_client import ApifyClient
        client = ApifyClient(apify_token)

        logger.info(
            f"Scraping Instagram profile: {profile_url}"
        )

        run_input = {
            "directUrls": [profile_url],
            "resultsType": "details",
            "resultsLimit": 1,   # number of profiles
            "postsLimit": MAX_POSTS
        }

        run = client.actor(
            "shu8hvrXbJbY3Eb9W"
        ).call(run_input=run_input)

        raw_items = list(
            client.dataset(
                run["defaultDatasetId"]
            ).iterate_items()
        )

        cleaned_items = [
            clean_profile_data(item)
            for item in raw_items
        ]

        logger.info(
            f"Successfully scraped {len(cleaned_items)} "
            f"profiles with max {MAX_POSTS} posts each"
        )

        return cleaned_items

    except Exception as e:
        logger.exception(
            f"Instagram scraping failed for "
            f"{profile_url}: {str(e)}"
        )
        return []


def process_input(state: AgentState) -> dict:
    """
    Input Node: Orchestrates the complete scraping and preprocessing pipeline.
    
    Extracts data from:
    - Store's website (using Crawl4AI + LLM)
    - Instagram page (using Apify API)
    
    Returns structured data for downstream agents.
    """
    logger.info("========== INPUT NODE STARTED ==========")
    
    raw_data = state.get("raw_input", {})
    website_url = raw_data.get("website")
    instagram_url = raw_data.get("instagram_page")
    
    logger.info(f"Input URLs: Website={website_url is not None}, Instagram={instagram_url is not None}")
    
    # Scrape website using crawl4ai + LLM
    website_content = {}
    if website_url:
        try:
            # Lazy-apply nest_asyncio to allow asyncio.run() inside Streamlit's event loop
            import nest_asyncio
            nest_asyncio.apply()

            logger.info("─── Website Scraping Phase ───")
            website_content = asyncio.run(scrape_website(website_url))
            if website_content:
                logger.info(f"✓ Website data extracted with {len(website_content.get('llm_extracted_data', {}))} intelligence fields")
            else:
                logger.warning("⚠ Website scraping returned empty result")
        except Exception as e:
            logger.exception(f"✗ Website scraping failed: {e}")
            
    # Scrape instagram using Apify API
    instagram_data = []
    if instagram_url:
        try:
            logger.info("─── Instagram Scraping Phase ───")
            instagram_data = scrape_instagram(instagram_url)
            if instagram_data:
                logger.info(f"✓ Instagram profiles scraped: {len(instagram_data)} profiles with posts")
            else:
                logger.warning("⚠ No Instagram data retrieved")
        except Exception as e:
            logger.exception(f"✗ Instagram scraping failed: {e}")
    
    # Extract additional context fields
    category = raw_data.get("category", "")
    location = raw_data.get("location", "")
    
    # Bundle collected data to flow through the LangGraph state
    structured_data = {
        **raw_data,
        "scraped_website_content": website_content,
        "scraped_instagram_data": instagram_data,
        "category": category,
        "location": location,
    }
    
    logger.info("========== INPUT NODE COMPLETED ==========")
    return {"structured_data": structured_data}
def main():
    """Test the input node with sample URLs."""
    logger.info("\n" + "="*50)
    logger.info("INPUT NODE TEST EXECUTION")
    logger.info("="*50 + "\n")
    
    # Test state with sample URLs
    state = {
        "raw_input": {
            "website": "https://www.shopclues.com/?srsltid=AfmBOooj04gCjboXVCP8Dg2beNLVhw-1c186XK6I09KA0SBiZ8O6thGx",
            "instagram_page": "https://www.instagram.com/_fashion_store_44/"
        },
        "structured_data": None,
        "sales_output": None,
        "marketing_output": None
    }
    
    try:
        # Process input
        result = process_input(AgentState(**state))
        structured_data = result.get("structured_data", {})
        
        if structured_data:
            logger.info("\n" + "─"*50)
            logger.info("OUTPUT SUMMARY")
            logger.info("─"*50)
            
            website_data = structured_data.get("scraped_website_content", {})
            instagram_data = structured_data.get("scraped_instagram_data", [])
            
            logger.info(f"Website Intelligence Fields: {len(website_data.get('llm_extracted_data', {}))} populated")
            logger.info(f"Instagram Profiles: {len(instagram_data)} profile(s)")
            
            # Print formatted output
            logger.info("\nFull structured data:")
            print(json.dumps(structured_data, indent=2))
        else:
            logger.error("✗ No structured data returned from input node")
            
    except Exception as e:
        logger.exception(f"✗ Test execution failed: {e}")

        
if __name__ == "__main__":
    main()