import logging
from datetime import datetime
from urllib.parse import urlparse
from src.state import AgentState
from src.memory import save_analysis, save_campaigns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def format_markdown_report(
    sales_output: dict,
    marketing_output: dict,
    research_output: dict,
    validation_report: dict,
    raw_input: dict,
) -> str:
    """
    Format all agent outputs into a professional markdown report.
    """
    report = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Header
    report.append("# 📊 FromNear — Vendor Onboarding Intelligence Report")
    report.append(f"*Generated on {timestamp}*\n")

    # Input Section
    report.append("---\n")
    report.append("## 📍 Vendor Information")
    website_url = raw_input.get("website_url") or raw_input.get("website", "N/A")
    instagram_url = raw_input.get("instagram_url") or raw_input.get("instagram_page", "N/A")
    report.append(f"- **Website:** {website_url}")
    report.append(f"- **Instagram:** {instagram_url}")
    report.append(f"- **Category:** {raw_input.get('category', 'N/A')}")
    report.append(f"- **Location:** {raw_input.get('location', 'N/A')}\n")

    # RESEARCH SECTION
    report.append("---\n")
    report.append("## 🔬 Research Analysis\n")
    if research_output:
        mp = research_output.get("market_positioning", {})
        report.append(f"**Market Position:** {mp.get('size', '?')} / "
                      f"{mp.get('niche', '?')} / {mp.get('price_tier', '?')}")
        report.append(f"**Positioning:** {mp.get('summary', 'N/A')}\n")

        cl = research_output.get("competitive_landscape", {})
        competitors = cl.get("likely_competitors", [])
        if competitors:
            report.append(f"**Competitors:** {', '.join(competitors)}")
        report.append(f"**Competitive Advantage:** {cl.get('competitive_advantage', 'N/A')}\n")

        df = research_output.get("digital_footprint", {})
        report.append(f"**Digital Footprint:** {df.get('score', '?')}/10\n")

        vr = research_output.get("vendor_readiness", {})
        report.append(f"**Vendor Readiness:** {vr.get('score', '?')}/10")
        for s in vr.get("strengths", []):
            report.append(f"  ✓ {s}")
        for g in vr.get("gaps", []):
            report.append(f"  ✗ {g}")
        report.append("")

        insights = research_output.get("key_insights", [])
        if insights:
            report.append("**Key Insights:**")
            for ins in insights:
                report.append(f"- {ins}")
            report.append("")

    # SALES SECTION
    report.append("---\n")
    report.append("## 💼 Onboarding Strategy\n")

    if sales_output:
        if sales_output.get("reasoning"):
            report.append("### 🧠 Agent Reasoning")
            report.append(f"{sales_output['reasoning']}\n")

        confidence = sales_output.get("confidence_level", 0)
        report.append(f"**Confidence Level:** {confidence:.0%}\n")

        if sales_output.get("business_summary"):
            report.append("### Business Summary")
            report.append(f"{sales_output['business_summary']}\n")

        lead = sales_output.get("lead_score", {})
        if lead:
            overall = lead.get("overall", "N/A")
            reason = lead.get("reason", "")
            breakdown = lead.get("breakdown", {})
            report.append("### 📊 Lead Score")
            report.append(f"**Overall:** {overall}/10 — {reason}")
            if breakdown:
                report.append(f"- Digital Presence: {breakdown.get('digital_presence', '?')}/10")
                report.append(f"- Market Fit: {breakdown.get('market_fit', '?')}/10")
                report.append(f"- Growth Potential: {breakdown.get('growth_potential', '?')}/10")
                report.append(f"- Engagement Quality: {breakdown.get('engagement_quality', '?')}/10")
            report.append("")

        for section, title in [
            ("pain_point_analysis", "🎯 Pain Point Analysis"),
            ("outreach_strategy", "📢 Outreach Strategy"),
            ("personalized_sales_pitch", "💬 Personalized Onboarding Pitch"),
            ("follow_up_suggestions", "⏰ Follow-up Suggestions"),
        ]:
            items = sales_output.get(section, [])
            if items:
                report.append(f"### {title}")
                for i, item in enumerate(items, 1):
                    report.append(f"{i}. {item}")
                report.append("")

        next_steps = sales_output.get("actionable_next_steps", [])
        if next_steps:
            report.append("### ✅ Actionable Next Steps")
            for step in next_steps:
                p = step.get("priority", "").upper()
                report.append(f"- [{p}] {step.get('action', '')} — "
                              f"*{step.get('timeline', '')}* ({step.get('owner', '')})")
            report.append("")

    # MARKETING SECTION
    report.append("---\n")
    report.append("## 📱 Vendor Launch Marketing\n")

    if marketing_output:
        if marketing_output.get("reasoning"):
            report.append("### 🧠 Agent Reasoning")
            report.append(f"{marketing_output['reasoning']}\n")

        confidence = marketing_output.get("confidence_level", 0)
        report.append(f"**Confidence Level:** {confidence:.0%}\n")

        if marketing_output.get("ad_campaigns"):
            report.append("### 🎬 Ad Campaigns")
            for i, c in enumerate(marketing_output["ad_campaigns"], 1):
                report.append(f"{i}. **{c.get('name', 'Campaign')}** ({c.get('platform', 'N/A')})")
                report.append(f"   - Duration: {c.get('duration', 'N/A')}")
                report.append(f"   - Hook: {c.get('hook', 'N/A')}")
            report.append("")

        if marketing_output.get("instagram_content_calendar"):
            report.append("### 📅 Instagram Content Calendar")
            for i, p in enumerate(marketing_output["instagram_content_calendar"], 1):
                report.append(f"{i}. **{p.get('day', 'Day')}** - {p.get('post_type', 'N/A')}")
                report.append(f"   - Idea: {p.get('idea', 'N/A')}")
                report.append(f"   - Hashtags: {p.get('hashtags', '')}")
            report.append("")

        if marketing_output.get("launch_campaigns"):
            report.append("### 🚀 Launch Campaigns")
            for i, c in enumerate(marketing_output["launch_campaigns"], 1):
                report.append(f"{i}. **{c.get('title', 'Campaign')}**")
                report.append(f"   - Focus: {c.get('focus', 'N/A')}")
                for t in c.get("tactics", []):
                    report.append(f"   - {t}")
            report.append("")

        if marketing_output.get("reels_and_hooks"):
            report.append("### 🎥 Reels & Hooks")
            for i, r in enumerate(marketing_output["reels_and_hooks"], 1):
                report.append(f"{i}. **{r.get('platform', 'N/A')}**")
                report.append(f"   - Hook: {r.get('hook', 'N/A')}")
                report.append(f"   - CTA: {r.get('cta', 'N/A')}")
            report.append("")

        if marketing_output.get("growth_strategies"):
            report.append("### 📈 Growth Strategies")
            for i, s in enumerate(marketing_output["growth_strategies"], 1):
                report.append(f"{i}. **{s.get('strategy', 'Strategy')}**")
                report.append(f"   - Action: {s.get('action', 'N/A')}")
                report.append(f"   - Expected Impact: {s.get('expected_impact', 'N/A')}")
            report.append("")

    # VALIDATION SECTION
    report.append("---\n")
    report.append("## ✅ Validation Report\n")
    if validation_report:
        qs = validation_report.get("overall_quality_score", 0)
        report.append(f"**Overall Quality Score:** {qs}/100\n")
        for check_name, check_key in [
            ("Data Grounding", "data_grounding"),
            ("Consistency", "consistency_check"),
            ("Actionability", "actionability"),
        ]:
            check = validation_report.get(check_key, {})
            status = check.get("status", "?").upper()
            score = check.get("score", "?")
            notes = check.get("notes", "")
            emoji = "✅" if status == "PASS" else "⚠️"
            report.append(f"{emoji} **{check_name}:** {score}/10 ({status})")
            if notes:
                report.append(f"   {notes}")
        report.append("")

        issues = validation_report.get("issues_found", [])
        if issues and issues != [""]:
            report.append("**Issues Found:**")
            for iss in issues:
                if iss:
                    report.append(f"- ⚠️ {iss}")
            report.append("")

    # Footer
    report.append("---\n")
    report.append("*End of Report — Powered by FromNear Multi-Agent Intelligence*")

    return "\n".join(report)


def aggregator(state: AgentState) -> AgentState:
    """
    Aggregator Node: Combines all agent outputs + saves to CRM memory.
    """
    logger.info("=" * 50)
    logger.info("AGGREGATOR STARTED")
    logger.info("=" * 50)

    sales_output = state.get("sales_output", {})
    marketing_output = state.get("marketing_output", {})
    research_output = state.get("research_output", {})
    validation_report = state.get("validation_report", {})
    raw_input = state.get("raw_input", {})
    structured_data = state.get("structured_data", {})

    # Format markdown report
    markdown_report = format_markdown_report(
        sales_output, marketing_output, research_output,
        validation_report, raw_input,
    )
    logger.info("✓ Markdown report generated")

    # ── Save to CRM memory ───────────────────────────────────────────
    try:
        website_url = raw_input.get("website_url") or raw_input.get("website", "")
        domain = urlparse(website_url).netloc if website_url else "unknown"
        instagram = raw_input.get("instagram_url") or raw_input.get("instagram_page", "")
        category = raw_input.get("category", "")
        location = raw_input.get("location", "")

        lead_score_data = sales_output.get("lead_score", {})
        lead_score = lead_score_data.get("overall", 0) if isinstance(lead_score_data, dict) else 0
        confidence = sales_output.get("confidence_level", 0.0)
        quality_score = validation_report.get("overall_quality_score", 0.0)

        save_analysis(
            domain=domain,
            instagram_handle=instagram,
            category=category,
            location=location,
            lead_score=float(lead_score),
            confidence=float(confidence),
            sales_output=sales_output,
            marketing_output=marketing_output,
            structured_data=structured_data,
            research_output=research_output,
            validation_report=validation_report,
            quality_score=float(quality_score),
        )
        logger.info("💾 Analysis saved to CRM memory")

        # Track proposed campaigns
        save_campaigns(domain, marketing_output)
        logger.info("📋 Campaigns tracked in CRM")
    except Exception as e:
        logger.error(f"⚠ Failed to save to CRM: {e}")

    logger.info("=" * 50)

    # Return structured output
    aggregated_output = {
        "sales_data": sales_output,
        "marketing_data": marketing_output,
        "research_data": research_output,
        "validation_data": validation_report,
        "markdown_report": markdown_report,
        "lead_score": lead_score_data,
        "confidence": confidence,
        "quality_score": quality_score,
    }

    return {"aggregated_output": aggregated_output}