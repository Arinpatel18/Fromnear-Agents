#!/usr/bin/env python3
"""
Streamlit UI for Fromnear AI Sales & Marketing Pipeline.

Run with:
    streamlit run app.py
"""

import streamlit as st
import asyncio
import json
import logging

import nest_asyncio
nest_asyncio.apply()

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ── Page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Fromnear · AI Sales & Marketing Intelligence",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ── Google Font ───────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Root variables ────────────────────────────────── */
:root {
    --accent-sales:    #6C63FF;
    --accent-mkt:      #00C9A7;
    --bg-card:         rgba(255,255,255,0.04);
    --border-card:     rgba(255,255,255,0.08);
    --glow-sales:      rgba(108,99,255,0.15);
    --glow-mkt:        rgba(0,201,167,0.15);
}

/* ── Hide default streamlit chrome ─────────────────── */
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 2rem; padding-bottom: 2rem;}

/* ── Hero header ───────────────────────────────────── */
.hero-title {
    text-align: center;
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(135deg, #6C63FF 0%, #00C9A7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.15rem;
    letter-spacing: -0.5px;
}
.hero-sub {
    text-align: center;
    color: #8B8FA3;
    font-size: 1.05rem;
    margin-bottom: 2rem;
    font-weight: 400;
}

/* ── Input card ────────────────────────────────────── */
.input-card {
    background: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: 16px;
    padding: 1.8rem 2rem;
    margin-bottom: 2.2rem;
    backdrop-filter: blur(12px);
}

/* ── Section headers ───────────────────────────────── */
.section-hdr-sales {
    font-size: 1.45rem;
    font-weight: 700;
    color: #6C63FF;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.section-hdr-mkt {
    font-size: 1.45rem;
    font-weight: 700;
    color: #00C9A7;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ── Result cards ──────────────────────────────────── */
.result-card {
    background: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: 14px;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1rem;
    transition: box-shadow 0.25s ease, border-color 0.25s ease;
}
.result-card:hover {
    border-color: rgba(255,255,255,0.15);
}
.result-card.sales:hover {
    box-shadow: 0 0 20px var(--glow-sales);
}
.result-card.mkt:hover {
    box-shadow: 0 0 20px var(--glow-mkt);
}
.result-card h4 {
    margin: 0 0 0.65rem 0;
    font-size: 1rem;
    font-weight: 600;
}
.result-card .content {
    font-size: 0.92rem;
    line-height: 1.6;
    color: #C4C7D4;
}
.result-card .content li {
    margin-bottom: 0.35rem;
}

/* ── Score badge ───────────────────────────────────── */
.score-badge {
    display: inline-block;
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #6C63FF, #00C9A7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-right: 0.5rem;
}

/* ── Confidence badge ─────────────────────────────── */
.confidence-high { color: #00C9A7; font-weight: 600; }
.confidence-mid  { color: #FFB347; font-weight: 600; }
.confidence-low  { color: #FF6B6B; font-weight: 600; }

/* ── Divider ───────────────────────────────────────── */
.col-divider {
    border-left: 1px solid rgba(255,255,255,0.06);
    min-height: 60vh;
    margin: 0 auto;
}

/* ── Button override ───────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #6C63FF 0%, #00C9A7 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.65rem 2.4rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    letter-spacing: 0.3px;
    transition: opacity 0.2s ease, transform 0.2s ease !important;
}
.stButton > button:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
}

/* ── Spinner overlay ───────────────────────────────── */
.stSpinner > div {
    border-color: #6C63FF !important;
}

/* ── Sidebar history card ─────────────────────────── */
.history-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.6rem;
    font-size: 0.85rem;
}
.history-card .domain {
    font-weight: 600;
    color: #E0E0E0;
}
.history-card .meta {
    color: #8B8FA3;
    font-size: 0.78rem;
}
</style>
""",
    unsafe_allow_html=True,
)


# ── Helpers ──────────────────────────────────────────────────────────
def _list_html(items: list) -> str:
    """Render a Python list as an HTML <ul>."""
    if not items:
        return "<p style='color:#8B8FA3;'>No data available</p>"
    li = "".join(f"<li>{item}</li>" for item in items)
    return f"<ul>{li}</ul>"


def _dict_items_html(items: list, fields: list[tuple[str, str]]) -> str:
    """Render a list of dicts as a nicely formatted HTML block."""
    if not items:
        return "<p style='color:#8B8FA3;'>No data available</p>"
    parts = []
    for i, item in enumerate(items, 1):
        heading_vals = []
        detail_lines = []
        for key, label in fields:
            val = item.get(key, "")
            if isinstance(val, list):
                val = ", ".join(val)
            if not val:
                continue
            if not heading_vals:
                heading_vals.append(f"<strong>{i}. {val}</strong>")
            else:
                detail_lines.append(f"<span style='color:#8B8FA3;'>{label}:</span> {val}")
        entry = "<br>".join(heading_vals + detail_lines)
        parts.append(f"<div style='margin-bottom:0.75rem;'>{entry}</div>")
    return "".join(parts)


def _confidence_badge(confidence: float) -> str:
    """Return HTML for a color-coded confidence badge."""
    pct = f"{confidence:.0%}"
    if confidence >= 0.7:
        return f'<span class="confidence-high">🟢 {pct}</span>'
    elif confidence >= 0.4:
        return f'<span class="confidence-mid">🟡 {pct}</span>'
    else:
        return f'<span class="confidence-low">🔴 {pct}</span>'


def _next_steps_html(steps: list) -> str:
    """Render actionable next steps as a styled checklist."""
    if not steps:
        return "<p style='color:#8B8FA3;'>No next steps</p>"
    parts = []
    for step in steps:
        action = step.get("action", "")
        priority = step.get("priority", "medium").upper()
        timeline = step.get("timeline", "")
        owner = step.get("owner", "")
        color = {"HIGH": "#FF6B6B", "MEDIUM": "#FFB347", "LOW": "#00C9A7"}.get(priority, "#8B8FA3")
        parts.append(
            f'<div style="margin-bottom:0.5rem;">'
            f'<span style="color:{color};font-weight:700;">[{priority}]</span> '
            f'{action} — <em>{timeline}</em> '
            f'<span style="color:#8B8FA3;">({owner})</span>'
            f'</div>'
        )
    return "".join(parts)


# ── SIDEBAR: Analysis History ────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧠 Memory / Analysis History")
    st.markdown("<p style='color:#8B8FA3;font-size:0.85rem;'>Past vendor analyses are stored and used to improve future recommendations.</p>", unsafe_allow_html=True)
    
    try:
        from src.memory import get_history
        history = get_history(limit=15)
        
        if history:
            for entry in history:
                domain = entry.get("domain", "unknown")
                cat = entry.get("category", "")
                loc = entry.get("location", "")
                score = entry.get("lead_score", 0)
                conf = entry.get("confidence", 0)
                ts = entry.get("created_at", "")[:16]
                
                st.markdown(
                    f"""<div class="history-card">
                    <div class="domain">🏪 {domain}</div>
                    <div class="meta">{cat} · {loc} · Score: {score}/10 · Conf: {conf:.0%}</div>
                    <div class="meta">{ts}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No analyses yet. Run your first analysis to start building memory.")
    except Exception as e:
        st.warning(f"Memory unavailable: {e}")


# ── HEADER ───────────────────────────────────────────────────────────
st.markdown('<p class="hero-title">🚀 Fromnear Intelligence</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-sub">Analyse any vendor\'s web &amp; Instagram presence — generate a personalised onboarding pitch &amp; launch plan.</p>',
    unsafe_allow_html=True,
)

# ── INPUT FORM ───────────────────────────────────────────────────────
st.markdown('<div class="input-card">', unsafe_allow_html=True)

col_a, col_b = st.columns(2)
with col_a:
    website_url = st.text_input(
        "🌐  Website URL",
        placeholder="https://www.example.com",
        help="Full URL of the business website to analyse.",
    )
    category = st.text_input(
        "📂  Business Category",
        placeholder="e.g. Fashion, Electronics, F&B",
        help="Primary category of the business.",
    )
with col_b:
    instagram_url = st.text_input(
        "📸  Instagram URL",
        placeholder="https://www.instagram.com/store_name/",
        help="Full Instagram profile URL.",
    )
    location = st.text_input(
        "📍  Location",
        placeholder="e.g. Mumbai, India",
        help="City / region where the business operates.",
    )

_, btn_col, _ = st.columns([2, 1, 2])
with btn_col:
    run_clicked = st.button("⚡  Analyse", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)


# ── PIPELINE EXECUTION ──────────────────────────────────────────────
if run_clicked:
    if not website_url and not instagram_url:
        st.warning("Please provide at least a **Website URL** or an **Instagram URL**.")
        st.stop()

    with st.spinner("🔄  Running the AI pipeline — scraping, analysing, generating …"):
        try:
            # Lazy import — avoid loading heavy crawl4ai/langgraph at page startup
            from src.graph import run_pipeline

            result = asyncio.run(
                run_pipeline(
                    website_url=website_url or "",
                    instagram_url=instagram_url or "",
                    category=category or "",
                    location=location or "",
                )
            )
            st.session_state["result"] = result
        except Exception as exc:
            st.error(f"Pipeline failed: {exc}")
            logger.exception("Pipeline error")
            st.stop()

# ── RESULTS ──────────────────────────────────────────────────────────
if "result" in st.session_state:
    result = st.session_state["result"]
    aggregated = result.get("aggregated_output", {})
    sales = aggregated.get("sales_data", result.get("sales_output", {}))
    marketing = aggregated.get("marketing_data", result.get("marketing_output", {}))

    st.markdown("---")

    col_sales, col_mkt = st.columns(2, gap="large")

    # ── SALES COLUMN ─────────────────────────────────────────────────
    with col_sales:
        st.markdown(
            '<div class="section-hdr-sales">💼 Onboarding Strategy</div>',
            unsafe_allow_html=True,
        )

        # Reasoning trace
        reasoning = sales.get("reasoning", "")
        if reasoning:
            with st.expander("🧠 Agent Reasoning", expanded=False):
                st.markdown(reasoning)

        # Confidence badge
        conf = sales.get("confidence_level", 0)
        st.markdown(
            f'<div style="margin-bottom:1rem;">Confidence: {_confidence_badge(conf)}</div>',
            unsafe_allow_html=True,
        )

        # Business Summary
        st.markdown(
            f"""<div class="result-card sales">
            <h4>📋 Business Summary</h4>
            <div class="content">{sales.get('business_summary', 'N/A')}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Lead Score with Breakdown
        lead = sales.get("lead_score", {})
        overall = lead.get("overall", 0) if isinstance(lead, dict) else lead
        reason = lead.get("reason", "") if isinstance(lead, dict) else ""
        breakdown = lead.get("breakdown", {}) if isinstance(lead, dict) else {}

        score_html = f'<span class="score-badge">{overall}/10</span> <span style="color:#C4C7D4;">{reason}</span>'
        if breakdown:
            score_html += '<div style="margin-top:0.8rem;">'
            for dim, label in [
                ("digital_presence", "Digital Presence"),
                ("market_fit", "Market Fit"),
                ("growth_potential", "Growth Potential"),
                ("engagement_quality", "Engagement"),
            ]:
                val = breakdown.get(dim, 0)
                pct = val * 10  # out of 100 for progress bar
                color = "#00C9A7" if val >= 7 else "#FFB347" if val >= 5 else "#FF6B6B"
                score_html += (
                    f'<div style="display:flex;align-items:center;margin-bottom:0.35rem;">'
                    f'<span style="width:140px;color:#8B8FA3;font-size:0.85rem;">{label}</span>'
                    f'<div style="flex:1;background:rgba(255,255,255,0.05);border-radius:4px;height:8px;margin:0 8px;">'
                    f'<div style="width:{pct}%;background:{color};height:100%;border-radius:4px;"></div>'
                    f'</div>'
                    f'<span style="color:{color};font-weight:600;font-size:0.85rem;">{val}/10</span>'
                    f'</div>'
                )
            score_html += '</div>'

        st.markdown(
            f"""<div class="result-card sales">
            <h4>📊 Lead Score</h4>
            <div class="content">{score_html}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Pain Point Analysis
        pain_points = sales.get("pain_point_analysis", [])
        st.markdown(
            f"""<div class="result-card sales">
            <h4>🎯 Pain Point Analysis</h4>
            <div class="content">{_list_html(pain_points)}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Outreach Strategy
        outreach = sales.get("outreach_strategy", [])
        st.markdown(
            f"""<div class="result-card sales">
            <h4>📢 Outreach Strategy</h4>
            <div class="content">{_list_html(outreach)}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Personalized Onboarding Pitch
        pitches = sales.get("personalized_sales_pitch", [])
        st.markdown(
            f"""<div class="result-card sales">
            <h4>💬 Personalized Onboarding Pitch</h4>
            <div class="content">{_list_html(pitches)}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Follow-up Suggestions
        followups = sales.get("follow_up_suggestions", [])
        st.markdown(
            f"""<div class="result-card sales">
            <h4>⏰ Follow-up Suggestions</h4>
            <div class="content">{_list_html(followups)}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Actionable Next Steps
        next_steps = sales.get("actionable_next_steps", [])
        if next_steps:
            st.markdown(
                f"""<div class="result-card sales">
                <h4>✅ Actionable Next Steps</h4>
                <div class="content">{_next_steps_html(next_steps)}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    # ── MARKETING COLUMN ─────────────────────────────────────────────
    with col_mkt:
        st.markdown(
            '<div class="section-hdr-mkt">📱 Vendor Launch Marketing</div>',
            unsafe_allow_html=True,
        )

        # Reasoning trace
        mkt_reasoning = marketing.get("reasoning", "")
        if mkt_reasoning:
            with st.expander("🧠 Agent Reasoning", expanded=False):
                st.markdown(mkt_reasoning)

        # Confidence badge
        mkt_conf = marketing.get("confidence_level", 0)
        st.markdown(
            f'<div style="margin-bottom:1rem;">Confidence: {_confidence_badge(mkt_conf)}</div>',
            unsafe_allow_html=True,
        )

        # Ad Campaigns
        ad_campaigns = marketing.get("ad_campaigns", [])
        st.markdown(
            f"""<div class="result-card mkt">
            <h4>🎬 Ad Campaign Ideas</h4>
            <div class="content">{_dict_items_html(ad_campaigns, [
                ("name", "Campaign"),
                ("platform", "Platform"),
                ("duration", "Duration"),
                ("hook", "Hook"),
            ])}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Instagram Content Ideas
        ig_content = marketing.get("instagram_content_calendar", [])
        st.markdown(
            f"""<div class="result-card mkt">
            <h4>📅 Instagram Content Ideas</h4>
            <div class="content">{_dict_items_html(ig_content, [
                ("day", "Day"),
                ("post_type", "Type"),
                ("idea", "Idea"),
                ("hashtags", "Hashtags"),
            ])}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Launch Campaign Concepts
        launch = marketing.get("launch_campaigns", [])
        st.markdown(
            f"""<div class="result-card mkt">
            <h4>🚀 Launch Campaign Concepts</h4>
            <div class="content">{_dict_items_html(launch, [
                ("title", "Title"),
                ("focus", "Focus"),
                ("tactics", "Tactics"),
            ])}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Reels / Post Hooks
        reels = marketing.get("reels_and_hooks", [])
        st.markdown(
            f"""<div class="result-card mkt">
            <h4>🎥 Reels / Post Hooks</h4>
            <div class="content">{_dict_items_html(reels, [
                ("hook", "Hook"),
                ("platform", "Platform"),
                ("cta", "CTA"),
            ])}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Growth Suggestions
        growth = marketing.get("growth_strategies", [])
        st.markdown(
            f"""<div class="result-card mkt">
            <h4>📈 Growth Suggestions</h4>
            <div class="content">{_dict_items_html(growth, [
                ("strategy", "Strategy"),
                ("action", "Action"),
                ("expected_impact", "Impact"),
            ])}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    # ── RAW JSON (collapsed) ─────────────────────────────────────────
    with st.expander("🔍  View raw JSON output"):
        st.json({"sales": sales, "marketing": marketing})
