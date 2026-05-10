#!/usr/bin/env python3
"""
Streamlit UI for Fromnear Multi-Agent AI Pipeline.

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
    page_title="Fromnear · Multi-Agent Intelligence",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

:root {
    --accent-sales:    #6C63FF;
    --accent-mkt:      #00C9A7;
    --accent-research: #FF6B9D;
    --accent-validate: #FFB347;
    --bg-card:         rgba(255,255,255,0.04);
    --border-card:     rgba(255,255,255,0.08);
    --glow-sales:      rgba(108,99,255,0.15);
    --glow-mkt:        rgba(0,201,167,0.15);
}

#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 2rem; padding-bottom: 2rem;}

.hero-title {
    text-align: center; font-size: 2.6rem; font-weight: 800;
    background: linear-gradient(135deg, #6C63FF 0%, #FF6B9D 50%, #00C9A7 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.15rem; letter-spacing: -0.5px;
}
.hero-sub {
    text-align: center; color: #8B8FA3; font-size: 1.05rem;
    margin-bottom: 2rem; font-weight: 400;
}

.input-card {
    background: var(--bg-card); border: 1px solid var(--border-card);
    border-radius: 16px; padding: 1.8rem 2rem; margin-bottom: 2.2rem;
    backdrop-filter: blur(12px);
}

.section-hdr-sales { font-size: 1.45rem; font-weight: 700; color: #6C63FF; margin-bottom: 1rem; }
.section-hdr-mkt { font-size: 1.45rem; font-weight: 700; color: #00C9A7; margin-bottom: 1rem; }
.section-hdr-research { font-size: 1.3rem; font-weight: 700; color: #FF6B9D; margin-bottom: 1rem; }
.section-hdr-validate { font-size: 1.3rem; font-weight: 700; color: #FFB347; margin-bottom: 1rem; }

.result-card {
    background: var(--bg-card); border: 1px solid var(--border-card);
    border-radius: 14px; padding: 1.25rem 1.4rem; margin-bottom: 1rem;
    transition: box-shadow 0.25s ease, border-color 0.25s ease;
}
.result-card:hover { border-color: rgba(255,255,255,0.15); }
.result-card.sales:hover { box-shadow: 0 0 20px var(--glow-sales); }
.result-card.mkt:hover { box-shadow: 0 0 20px var(--glow-mkt); }
.result-card h4 { margin: 0 0 0.65rem 0; font-size: 1rem; font-weight: 600; }
.result-card .content { font-size: 0.92rem; line-height: 1.6; color: #C4C7D4; }
.result-card .content li { margin-bottom: 0.35rem; }

.score-badge {
    display: inline-block; font-size: 2rem; font-weight: 800;
    background: linear-gradient(135deg, #6C63FF, #00C9A7);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-right: 0.5rem;
}

.confidence-high { color: #00C9A7; font-weight: 600; }
.confidence-mid  { color: #FFB347; font-weight: 600; }
.confidence-low  { color: #FF6B6B; font-weight: 600; }

.stButton > button {
    background: linear-gradient(135deg, #6C63FF 0%, #00C9A7 100%) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; padding: 0.65rem 2.4rem !important;
    font-weight: 600 !important; font-size: 1rem !important;
    transition: opacity 0.2s ease, transform 0.2s ease !important;
}
.stButton > button:hover { opacity: 0.9 !important; transform: translateY(-1px) !important; }

.history-card {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px; padding: 0.8rem 1rem; margin-bottom: 0.6rem; font-size: 0.85rem;
}
.history-card .domain { font-weight: 600; color: #E0E0E0; }
.history-card .meta { color: #8B8FA3; font-size: 0.78rem; }

.stat-card {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px; padding: 1rem; text-align: center; margin-bottom: 0.5rem;
}
.stat-card .stat-value { font-size: 1.6rem; font-weight: 800; color: #E0E0E0; }
.stat-card .stat-label { font-size: 0.75rem; color: #8B8FA3; text-transform: uppercase; }

.agent-badge {
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 0.72rem; font-weight: 600; margin-right: 4px; margin-bottom: 4px;
}
</style>
""",
    unsafe_allow_html=True,
)


# ── Helpers ──────────────────────────────────────────────────────────
def _list_html(items: list) -> str:
    if not items:
        return "<p style='color:#8B8FA3;'>No data available</p>"
    li = "".join(f"<li>{item}</li>" for item in items)
    return f"<ul>{li}</ul>"


def _dict_items_html(items: list, fields: list[tuple[str, str]]) -> str:
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
    pct = f"{confidence:.0%}"
    if confidence >= 0.7:
        return f'<span class="confidence-high">🟢 {pct}</span>'
    elif confidence >= 0.4:
        return f'<span class="confidence-mid">🟡 {pct}</span>'
    else:
        return f'<span class="confidence-low">🔴 {pct}</span>'


def _next_steps_html(steps: list) -> str:
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


def _quality_badge(score: float) -> str:
    if score >= 80:
        return f'<span class="confidence-high">🟢 {score:.0f}/100</span>'
    elif score >= 50:
        return f'<span class="confidence-mid">🟡 {score:.0f}/100</span>'
    else:
        return f'<span class="confidence-low">🔴 {score:.0f}/100</span>'


# ── SIDEBAR: CRM Dashboard ──────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧠 CRM Memory")

    # CRM Stats
    try:
        from src.memory import get_history, get_crm_stats
        stats = get_crm_stats()

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f'<div class="stat-card"><div class="stat-value">{stats["total_analyses"]}</div>'
                f'<div class="stat-label">Analyses</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div class="stat-card"><div class="stat-value">{stats["avg_lead_score"]}</div>'
                f'<div class="stat-label">Avg Score</div></div>',
                unsafe_allow_html=True,
            )

        c3, c4 = st.columns(2)
        with c3:
            st.markdown(
                f'<div class="stat-card"><div class="stat-value">{stats["total_campaigns"]}</div>'
                f'<div class="stat-label">Campaigns</div></div>',
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                f'<div class="stat-card"><div class="stat-value">{stats["total_notes"]}</div>'
                f'<div class="stat-label">CRM Notes</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("#### 📋 Analysis History")

        history = get_history(limit=15)
        if history:
            for entry in history:
                domain = entry.get("domain", "unknown")
                cat = entry.get("category", "")
                loc = entry.get("location", "")
                score = entry.get("lead_score", 0)
                conf = entry.get("confidence", 0)
                qs = entry.get("quality_score", 0)
                ts = entry.get("created_at", "")[:16]

                st.markdown(
                    f"""<div class="history-card">
                    <div class="domain">🏪 {domain}</div>
                    <div class="meta">{cat} · {loc} · Score: {score}/10 · Quality: {qs:.0f}/100</div>
                    <div class="meta">{ts}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No analyses yet. Run your first analysis!")

    except Exception as e:
        st.warning(f"CRM unavailable: {e}")

    st.markdown("---")
    st.markdown(
        '<p style="color:#8B8FA3;font-size:0.78rem;">'
        '🤖 Agents: Input → Research → Memory → Sales + Marketing → Validator → Aggregator'
        '</p>',
        unsafe_allow_html=True,
    )


# ── HEADER ───────────────────────────────────────────────────────────
st.markdown('<p class="hero-title">🚀 Fromnear Multi-Agent Intelligence</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-sub">6 AI agents work autonomously — research, analyse, pitch, market, validate — all in one click.</p>',
    unsafe_allow_html=True,
)

# Agent badges
st.markdown(
    '<div style="text-align:center;margin-bottom:1.5rem;">'
    '<span class="agent-badge" style="background:#6C63FF22;color:#6C63FF;">🔍 Input</span>'
    '<span class="agent-badge" style="background:#FF6B9D22;color:#FF6B9D;">🔬 Research</span>'
    '<span class="agent-badge" style="background:#8B8FA322;color:#8B8FA3;">🧠 Memory</span>'
    '<span class="agent-badge" style="background:#6C63FF22;color:#6C63FF;">💼 Sales</span>'
    '<span class="agent-badge" style="background:#00C9A722;color:#00C9A7;">📱 Marketing</span>'
    '<span class="agent-badge" style="background:#FFB34722;color:#FFB347;">✅ Validator</span>'
    '</div>',
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
    )
with col_b:
    instagram_url = st.text_input(
        "📸  Instagram URL",
        placeholder="https://www.instagram.com/store_name/",
    )
    location = st.text_input(
        "📍  Location",
        placeholder="e.g. Jaipur, India",
    )

_, btn_col, _ = st.columns([2, 1, 2])
with btn_col:
    run_clicked = st.button("⚡  Run All Agents", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)


# ── PIPELINE EXECUTION ──────────────────────────────────────────────
if run_clicked:
    if not website_url and not instagram_url:
        st.warning("Please provide at least a **Website URL** or an **Instagram URL**.")
        st.stop()

    progress = st.empty()
    with st.spinner("🤖 Running 6-agent autonomous pipeline …"):
        try:
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
    research = aggregated.get("research_data", result.get("research_output", {}))
    validation = aggregated.get("validation_data", result.get("validation_report", {}))

    st.markdown("---")

    # ── RESEARCH + VALIDATION ROW ────────────────────────────────────
    col_res, col_val = st.columns(2, gap="large")

    with col_res:
        st.markdown('<div class="section-hdr-research">🔬 Research Analysis</div>', unsafe_allow_html=True)

        if research:
            mp = research.get("market_positioning", {})
            df = research.get("digital_footprint", {})
            vr = research.get("vendor_readiness", {})
            cl = research.get("competitive_landscape", {})

            # Key metrics
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Market Size", mp.get("size", "?").capitalize())
            with m2:
                st.metric("Digital Score", f"{df.get('score', 0)}/10")
            with m3:
                st.metric("Readiness", f"{vr.get('score', 0)}/10")

            st.markdown(
                f"""<div class="result-card">
                <h4>📍 Market Positioning</h4>
                <div class="content">
                <strong>Niche:</strong> {mp.get('niche', 'N/A')} · <strong>Price:</strong> {mp.get('price_tier', 'N/A')}<br>
                {mp.get('summary', 'N/A')}
                </div></div>""",
                unsafe_allow_html=True,
            )

            competitors = cl.get("likely_competitors", [])
            st.markdown(
                f"""<div class="result-card">
                <h4>⚔️ Competitive Landscape</h4>
                <div class="content">
                <strong>Competitors:</strong> {', '.join(competitors) if competitors else 'N/A'}<br>
                <strong>Advantage:</strong> {cl.get('competitive_advantage', 'N/A')}<br>
                <strong>Saturation:</strong> {cl.get('market_saturation', 'N/A')}
                </div></div>""",
                unsafe_allow_html=True,
            )

            insights = research.get("key_insights", [])
            if insights:
                st.markdown(
                    f"""<div class="result-card">
                    <h4>💡 Key Insights</h4>
                    <div class="content">{_list_html(insights)}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

    with col_val:
        st.markdown('<div class="section-hdr-validate">✅ Validation Report</div>', unsafe_allow_html=True)

        if validation:
            qs = validation.get("overall_quality_score", 0)
            st.markdown(
                f'<div style="margin-bottom:1rem;">Quality Score: {_quality_badge(qs)}</div>',
                unsafe_allow_html=True,
            )

            for check_name, check_key, emoji in [
                ("Data Grounding", "data_grounding", "🎯"),
                ("Consistency", "consistency_check", "🔗"),
                ("Actionability", "actionability", "⚡"),
            ]:
                check = validation.get(check_key, {})
                score = check.get("score", 0)
                status = check.get("status", "?").upper()
                notes = check.get("notes", "")
                status_color = "#00C9A7" if status == "PASS" else "#FF6B6B"
                st.markdown(
                    f"""<div class="result-card">
                    <h4>{emoji} {check_name} — <span style="color:{status_color};">{status}</span> ({score}/10)</h4>
                    <div class="content">{notes}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

            issues = validation.get("issues_found", [])
            issues = [i for i in issues if i]
            if issues:
                st.markdown(
                    f"""<div class="result-card">
                    <h4>⚠️ Issues Found</h4>
                    <div class="content">{_list_html(issues)}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

            recs = validation.get("recommendations", [])
            recs = [r for r in recs if r]
            if recs:
                st.markdown(
                    f"""<div class="result-card">
                    <h4>💡 Recommendations</h4>
                    <div class="content">{_list_html(recs)}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # ── SALES + MARKETING COLUMNS ────────────────────────────────────
    col_sales, col_mkt = st.columns(2, gap="large")

    # ── SALES COLUMN ─────────────────────────────────────────────────
    with col_sales:
        st.markdown('<div class="section-hdr-sales">💼 Onboarding Strategy</div>', unsafe_allow_html=True)

        reasoning = sales.get("reasoning", "")
        if reasoning:
            with st.expander("🧠 Agent Reasoning", expanded=False):
                st.markdown(reasoning)

        conf = sales.get("confidence_level", 0)
        st.markdown(f'<div style="margin-bottom:1rem;">Confidence: {_confidence_badge(conf)}</div>', unsafe_allow_html=True)

        st.markdown(
            f"""<div class="result-card sales">
            <h4>📋 Business Summary</h4>
            <div class="content">{sales.get('business_summary', 'N/A')}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Lead Score
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
                pct = val * 10
                color = "#00C9A7" if val >= 7 else "#FFB347" if val >= 5 else "#FF6B6B"
                score_html += (
                    f'<div style="display:flex;align-items:center;margin-bottom:0.35rem;">'
                    f'<span style="width:140px;color:#8B8FA3;font-size:0.85rem;">{label}</span>'
                    f'<div style="flex:1;background:rgba(255,255,255,0.05);border-radius:4px;height:8px;margin:0 8px;">'
                    f'<div style="width:{pct}%;background:{color};height:100%;border-radius:4px;"></div>'
                    f'</div>'
                    f'<span style="color:{color};font-weight:600;font-size:0.85rem;">{val}/10</span></div>'
                )
            score_html += '</div>'

        st.markdown(
            f"""<div class="result-card sales"><h4>📊 Lead Score</h4>
            <div class="content">{score_html}</div></div>""",
            unsafe_allow_html=True,
        )

        for section, title, icon in [
            ("pain_point_analysis", "Pain Point Analysis", "🎯"),
            ("outreach_strategy", "Outreach Strategy", "📢"),
            ("personalized_sales_pitch", "Personalized Onboarding Pitch", "💬"),
            ("follow_up_suggestions", "Follow-up Suggestions", "⏰"),
        ]:
            items = sales.get(section, [])
            st.markdown(
                f"""<div class="result-card sales"><h4>{icon} {title}</h4>
                <div class="content">{_list_html(items)}</div></div>""",
                unsafe_allow_html=True,
            )

        next_steps = sales.get("actionable_next_steps", [])
        if next_steps:
            st.markdown(
                f"""<div class="result-card sales"><h4>✅ Actionable Next Steps</h4>
                <div class="content">{_next_steps_html(next_steps)}</div></div>""",
                unsafe_allow_html=True,
            )

    # ── MARKETING COLUMN ─────────────────────────────────────────────
    with col_mkt:
        st.markdown('<div class="section-hdr-mkt">📱 Vendor Launch Marketing</div>', unsafe_allow_html=True)

        mkt_reasoning = marketing.get("reasoning", "")
        if mkt_reasoning:
            with st.expander("🧠 Agent Reasoning", expanded=False):
                st.markdown(mkt_reasoning)

        mkt_conf = marketing.get("confidence_level", 0)
        st.markdown(f'<div style="margin-bottom:1rem;">Confidence: {_confidence_badge(mkt_conf)}</div>', unsafe_allow_html=True)

        for section, title, icon, fields in [
            ("ad_campaigns", "Ad Campaign Ideas", "🎬",
             [("name", "Campaign"), ("platform", "Platform"), ("duration", "Duration"), ("hook", "Hook")]),
            ("instagram_content_calendar", "Instagram Content Ideas", "📅",
             [("day", "Day"), ("post_type", "Type"), ("idea", "Idea"), ("hashtags", "Hashtags")]),
            ("launch_campaigns", "Launch Campaign Concepts", "🚀",
             [("title", "Title"), ("focus", "Focus"), ("tactics", "Tactics")]),
            ("reels_and_hooks", "Reels / Post Hooks", "🎥",
             [("hook", "Hook"), ("platform", "Platform"), ("cta", "CTA")]),
            ("growth_strategies", "Growth Suggestions", "📈",
             [("strategy", "Strategy"), ("action", "Action"), ("expected_impact", "Impact")]),
        ]:
            items = marketing.get(section, [])
            st.markdown(
                f"""<div class="result-card mkt"><h4>{icon} {title}</h4>
                <div class="content">{_dict_items_html(items, fields)}</div></div>""",
                unsafe_allow_html=True,
            )

    # ── RAW JSON (collapsed) ─────────────────────────────────────────
    with st.expander("🔍  View raw JSON output"):
        st.json({
            "research": research,
            "sales": sales,
            "marketing": marketing,
            "validation": validation,
        })
