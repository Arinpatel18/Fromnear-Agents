"""
Validator Agent Node.

The quality-gate agent that runs AFTER Sales + Marketing agents
but BEFORE the Aggregator. It:

  - Cross-validates sales and marketing outputs for consistency
  - Checks that claims are grounded in actual scraped data
  - Validates lead score reasonableness
  - Identifies potential hallucinations or over-promises
  - Produces a validation report with pass/fail per section
  - Assigns an overall quality score

This ensures the final output sent to the user is reliable and actionable.
"""

import json
import os
import logging
from src.state import AgentState
from src.llm_client import get_ollama_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def validator_agent(state: AgentState) -> AgentState:
    """
    Validator Agent — cross-validates all agent outputs for quality.

    Runs AFTER sales_agent and marketing_agent converge.
    Adds validation_report to state before aggregation.
    """
    logger.info("=" * 50)
    logger.info("✅ VALIDATOR AGENT STARTED")
    logger.info("=" * 50)

    sales = state.get("sales_output", {})
    marketing = state.get("marketing_output", {})
    research = state.get("research_output", {})
    structured_data = state.get("structured_data", {})

    model_name = os.getenv("SALES_AGENT_MODEL", "gemma3:12b")

    # Build a summary of what the agents produced
    sales_summary = json.dumps(sales, default=str)[:2000]
    marketing_summary = json.dumps(marketing, default=str)[:2000]
    research_summary = json.dumps(research, default=str)[:1500]

    # Build a summary of actual data
    category = structured_data.get("category", "")
    location = structured_data.get("location", "")
    website_data = structured_data.get("scraped_website_content", {})
    llm_data = website_data.get("llm_extracted_data", {})
    ig_data = structured_data.get("scraped_instagram_data", [])

    actual_data_summary = f"""
Category: {category}
Location: {location}
Business: {llm_data.get('business_summary', 'N/A')}
Products: {', '.join(llm_data.get('products_services', [])[:5])}
Instagram Followers: {ig_data[0].get('followersCount', 0) if ig_data else 'No data'}
"""

    prompt = f"""You are a Quality Assurance Validator for FromNear's AI pipeline.

Your job is to cross-validate the outputs of the Research, Sales, and Marketing agents
to ensure quality, consistency, and factual accuracy.

=== ACTUAL VENDOR DATA (ground truth) ===
{actual_data_summary}

=== RESEARCH AGENT OUTPUT ===
{research_summary}

=== SALES AGENT OUTPUT ===
{sales_summary}

=== MARKETING AGENT OUTPUT ===
{marketing_summary}

VALIDATE each section and return a validation report:

1. For each agent output, check:
   - Are claims grounded in actual data? (not hallucinated)
   - Are recommendations specific and actionable?
   - Is the lead score reasonable given the data?
   - Are sales and marketing strategies consistent with each other?

2. Flag any issues:
   - Hallucinations (claims not supported by data)
   - Inconsistencies between agents
   - Over-promising or unrealistic suggestions
   - Missing critical information

3. Provide an overall quality score (0-100).

Return ONLY valid JSON:
{{
    "overall_quality_score": 85,
    "data_grounding": {{
        "score": 8,
        "status": "pass",
        "notes": "Most claims are well-grounded in scraped data"
    }},
    "consistency_check": {{
        "score": 9,
        "status": "pass",
        "notes": "Sales and marketing strategies are well-aligned"
    }},
    "actionability": {{
        "score": 8,
        "status": "pass",
        "notes": "Recommendations are specific and executable"
    }},
    "issues_found": [
        "Issue description if any"
    ],
    "recommendations": [
        "Suggestion to improve output quality"
    ],
    "validated": true
}}"""

    logger.info(f"🔍 Using model: {model_name}")
    logger.info(f"🔍 Prompt size: {len(prompt)} characters")

    try:
        client = get_ollama_client()
        response = client.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.1,
                "top_p": 0.5,
                "num_predict": 2000,
            },
        )

        text = response["message"]["content"]
        logger.info(f"✓ Validator response: {len(text)} characters")

        try:
            report = json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                report = json.loads(match.group())
            else:
                raise ValueError("Could not parse validation JSON")

        quality = report.get("overall_quality_score", 0)
        validated = report.get("validated", False)
        issues = report.get("issues_found", [])

        logger.info(f"✓ Quality Score: {quality}/100")
        logger.info(f"✓ Validated: {validated}")
        logger.info(f"✓ Data Grounding: {report.get('data_grounding', {}).get('status', '?')}")
        logger.info(f"✓ Consistency: {report.get('consistency_check', {}).get('status', '?')}")
        logger.info(f"✓ Actionability: {report.get('actionability', {}).get('status', '?')}")
        if issues:
            for iss in issues:
                logger.warning(f"  ⚠ Issue: {iss}")
        logger.info("=" * 50)

        return {"validation_report": report}

    except Exception as e:
        logger.error(f"✗ Validator agent failed: {e}")
        return {
            "validation_report": {
                "overall_quality_score": 0,
                "data_grounding": {"score": 0, "status": "error"},
                "consistency_check": {"score": 0, "status": "error"},
                "actionability": {"score": 0, "status": "error"},
                "issues_found": [f"Validation failed: {str(e)}"],
                "recommendations": [],
                "validated": False,
            }
        }
