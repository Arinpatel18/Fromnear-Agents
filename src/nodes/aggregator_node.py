import logging
from datetime import datetime
from src.state import AgentState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def format_markdown_report(sales_output: dict, marketing_output: dict, raw_input: dict) -> str:
    """
    Format both sales and marketing outputs into a clean, professional markdown report.
    """
    report = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Header
    report.append("# 📊 AI-Driven Sales & Marketing Intelligence Report")
    report.append(f"*Generated on {timestamp}*\n")
    
    # Input Section
    report.append("---\n")
    report.append("## 📍 Business Information")
    website_url = raw_input.get("website_url") or raw_input.get("website", "N/A")
    instagram_url = raw_input.get("instagram_url") or raw_input.get("instagram_page", "N/A")
    report.append(f"- **Website:** {website_url}")
    report.append(f"- **Instagram:** {instagram_url}\n")
    
    # SALES SECTION
    report.append("---\n")
    report.append("## 💼 Sales Strategy\n")
    
    if sales_output:
        # Business Summary
        if sales_output.get("business_summary"):
            report.append("### Business Summary")
            report.append(f"{sales_output['business_summary']}\n")
        
        # Pain Point Analysis
        if sales_output.get("pain_point_analysis"):
            report.append("### 🎯 Pain Point Analysis")
            for i, pain_point in enumerate(sales_output["pain_point_analysis"], 1):
                report.append(f"{i}. {pain_point}")
            report.append("")
        
        # Qualification Score
        if sales_output.get("qualification_score"):
            score_data = sales_output["qualification_score"]
            score = score_data.get("score", "N/A")
            reason = score_data.get("reason", "N/A")
            report.append("### 📈 Qualification Score")
            report.append(f"**Score:** {score}/10")
            report.append(f"**Reason:** {reason}\n")
        
        # Outreach Strategy
        if sales_output.get("outreach_strategy"):
            report.append("### 📢 Outreach Strategy")
            for i, strategy in enumerate(sales_output["outreach_strategy"], 1):
                report.append(f"{i}. {strategy}")
            report.append("")
        
        # Personalized Sales Pitch
        if sales_output.get("personalized_sales_pitch"):
            report.append("### 💬 Personalized Sales Pitches")
            for i, pitch in enumerate(sales_output["personalized_sales_pitch"], 1):
                report.append(f"{i}. {pitch}")
            report.append("")
        
        # Follow-up Suggestions
        if sales_output.get("follow_up_suggestions"):
            report.append("### ⏰ Follow-up Suggestions")
            for i, followup in enumerate(sales_output["follow_up_suggestions"], 1):
                report.append(f"{i}. {followup}")
            report.append("")
    
    # MARKETING SECTION
    report.append("---\n")
    report.append("## 📱 Marketing Strategy\n")
    
    if marketing_output:
        # Ad Campaigns
        if marketing_output.get("ad_campaigns"):
            report.append("### 🎬 Ad Campaigns")
            for i, campaign in enumerate(marketing_output["ad_campaigns"], 1):
                name = campaign.get("name", "Campaign")
                platform = campaign.get("platform", "N/A")
                duration = campaign.get("duration", "N/A")
                hook = campaign.get("hook", "N/A")
                report.append(f"{i}. **{name}** ({platform})")
                report.append(f"   - Duration: {duration}")
                report.append(f"   - Hook: {hook}")
            report.append("")
        
        # Instagram Content Calendar
        if marketing_output.get("instagram_content_calendar"):
            report.append("### 📅 Instagram Content Calendar")
            for i, post in enumerate(marketing_output["instagram_content_calendar"], 1):
                day = post.get("day", "Day")
                post_type = post.get("post_type", "N/A")
                idea = post.get("idea", "N/A")
                hashtags = post.get("hashtags", "")
                report.append(f"{i}. **{day}** - {post_type}")
                report.append(f"   - Idea: {idea}")
                report.append(f"   - Hashtags: {hashtags}")
            report.append("")
        
        # Launch Campaigns
        if marketing_output.get("launch_campaigns"):
            report.append("### 🚀 Launch Campaigns")
            for i, campaign in enumerate(marketing_output["launch_campaigns"], 1):
                title = campaign.get("title", "Campaign")
                focus = campaign.get("focus", "N/A")
                tactics = campaign.get("tactics", [])
                report.append(f"{i}. **{title}**")
                report.append(f"   - Focus: {focus}")
                for tactic in tactics:
                    report.append(f"   - {tactic}")
            report.append("")
        
        # Reels and Hooks
        if marketing_output.get("reels_and_hooks"):
            report.append("### 🎥 Reels & Hooks")
            for i, reel in enumerate(marketing_output["reels_and_hooks"], 1):
                hook = reel.get("hook", "Hook")
                platform = reel.get("platform", "N/A")
                cta = reel.get("cta", "N/A")
                report.append(f"{i}. **{platform}**")
                report.append(f"   - Hook: {hook}")
                report.append(f"   - CTA: {cta}")
            report.append("")
        
        # Growth Strategies
        if marketing_output.get("growth_strategies"):
            report.append("### 📈 Growth Strategies")
            for i, strategy in enumerate(marketing_output["growth_strategies"], 1):
                strat_name = strategy.get("strategy", "Strategy")
                action = strategy.get("action", "N/A")
                impact = strategy.get("expected_impact", "N/A")
                report.append(f"{i}. **{strat_name}**")
                report.append(f"   - Action: {action}")
                report.append(f"   - Expected Impact: {impact}")
            report.append("")
    
    # Footer
    report.append("---\n")
    report.append("*End of Report*")
    
    return "\n".join(report)


def aggregator(state: AgentState) -> AgentState:
    """
    Aggregator Node: Combines outputs from Sales and Marketing Agents.
    Generates a clean, professional markdown report.
    """
    logger.info("=" * 50)
    logger.info("AGGREGATOR STARTED")
    logger.info("=" * 50)
    
    sales_output = state.get("sales_output", {})
    marketing_output = state.get("marketing_output", {})
    raw_input = state.get("raw_input", {})
    
    # Format markdown report
    markdown_report = format_markdown_report(sales_output, marketing_output, raw_input)
    
    logger.info("✓ Markdown report generated")
    logger.info("=" * 50)
    
    # Return structured output
    aggregated_output = {
        "sales_data": sales_output,
        "marketing_data": marketing_output,
        "markdown_report": markdown_report
    }
    
    return {"aggregated_output": aggregated_output}

    