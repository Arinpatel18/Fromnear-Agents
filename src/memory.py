"""
Local CRM Memory System for the FromNear AI pipeline.

Uses SQLite to provide persistent, queryable memory:
  - vendor_analyses: Full analysis history with scores
  - vendor_notes:    CRM-style notes / conversation logs per vendor
  - campaign_tracking: Track which campaigns were proposed and their status

This gives agents historical context and provides a local CRM
for the sales team.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "memory.db")


# ──────────────────────────────────────────────────────────────────────
#  Connection + Schema
# ──────────────────────────────────────────────────────────────────────

def _get_connection() -> sqlite3.Connection:
    """Return a connection to the CRM database, creating tables if needed."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Main analyses table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vendor_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT,
            instagram_handle TEXT,
            category TEXT,
            location TEXT,
            lead_score REAL,
            confidence REAL,
            quality_score REAL DEFAULT 0,
            sales_output TEXT,
            marketing_output TEXT,
            research_output TEXT DEFAULT '{}',
            validation_report TEXT DEFAULT '{}',
            structured_data TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # CRM Notes — conversation logs / interactions per vendor
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vendor_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_domain TEXT NOT NULL,
            note_type TEXT DEFAULT 'general',
            content TEXT NOT NULL,
            created_by TEXT DEFAULT 'system',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Campaign tracking — track proposed campaigns and their status
    conn.execute("""
        CREATE TABLE IF NOT EXISTS campaign_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_domain TEXT NOT NULL,
            campaign_name TEXT NOT NULL,
            campaign_type TEXT DEFAULT 'marketing',
            status TEXT DEFAULT 'proposed',
            details TEXT DEFAULT '{}',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    return conn


# ──────────────────────────────────────────────────────────────────────
#  Vendor Analyses (existing, enhanced)
# ──────────────────────────────────────────────────────────────────────

def save_analysis(
    domain: str,
    instagram_handle: str,
    category: str,
    location: str,
    lead_score: float,
    confidence: float,
    sales_output: dict,
    marketing_output: dict,
    structured_data: dict | None = None,
    research_output: dict | None = None,
    validation_report: dict | None = None,
    quality_score: float = 0.0,
) -> int:
    """Persist a completed vendor analysis to the CRM database."""
    conn = _get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO vendor_analyses
                (domain, instagram_handle, category, location,
                 lead_score, confidence, quality_score,
                 sales_output, marketing_output, research_output,
                 validation_report, structured_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                domain,
                instagram_handle,
                category.lower().strip() if category else "",
                location.lower().strip() if location else "",
                lead_score,
                confidence,
                quality_score,
                json.dumps(sales_output, default=str),
                json.dumps(marketing_output, default=str),
                json.dumps(research_output or {}, default=str),
                json.dumps(validation_report or {}, default=str),
                json.dumps(structured_data, default=str) if structured_data else "{}",
            ),
        )
        conn.commit()
        row_id = cursor.lastrowid
        logger.info(f"💾 CRM: Analysis saved for {domain} (id={row_id}, score={lead_score})")

        # Auto-log a CRM note
        _auto_note(conn, domain, lead_score, confidence, quality_score)

        return row_id
    finally:
        conn.close()


def _auto_note(conn, domain, lead_score, confidence, quality_score):
    """Automatically create a CRM note when an analysis is saved."""
    conn.execute(
        """INSERT INTO vendor_notes (vendor_domain, note_type, content, created_by)
           VALUES (?, ?, ?, ?)""",
        (
            domain,
            "analysis",
            f"New analysis completed. Lead score: {lead_score}/10, "
            f"Confidence: {confidence:.0%}, Quality: {quality_score}/100.",
            "ai_pipeline",
        ),
    )
    conn.commit()


def get_similar_vendors(
    category: str = "",
    location: str = "",
    limit: int = 3,
) -> list[dict]:
    """Retrieve past analyses of vendors with similar category or location."""
    conn = _get_connection()
    try:
        conditions = []
        params = []

        if category:
            conditions.append("LOWER(category) = ?")
            params.append(category.lower().strip())
        if location:
            conditions.append("LOWER(location) LIKE ?")
            params.append(f"%{location.lower().strip()}%")

        where_clause = " OR ".join(conditions) if conditions else "1=1"
        query = f"""
            SELECT id, domain, instagram_handle, category, location,
                   lead_score, confidence, quality_score,
                   sales_output, marketing_output, created_at
            FROM vendor_analyses
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ?
        """
        params.append(limit)

        rows = conn.execute(query, params).fetchall()

        results = []
        for row in rows:
            results.append({
                "id": row["id"],
                "domain": row["domain"],
                "instagram_handle": row["instagram_handle"],
                "category": row["category"],
                "location": row["location"],
                "lead_score": row["lead_score"],
                "confidence": row["confidence"],
                "quality_score": row["quality_score"],
                "sales_summary": json.loads(row["sales_output"]).get("business_summary", ""),
                "created_at": row["created_at"],
            })

        logger.info(f"🧠 CRM recall: {len(results)} similar vendor(s)")
        return results
    finally:
        conn.close()


def get_history(limit: int = 20) -> list[dict]:
    """Return the most recent analyses for the UI sidebar."""
    conn = _get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, domain, instagram_handle, category, location,
                   lead_score, confidence, quality_score, created_at
            FROM vendor_analyses
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_analysis_by_id(analysis_id: int) -> dict | None:
    """Return a full analysis record by its ID."""
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM vendor_analyses WHERE id = ?", (analysis_id,)
        ).fetchone()
        if row is None:
            return None
        result = dict(row)
        for field in ("sales_output", "marketing_output", "research_output",
                      "validation_report", "structured_data"):
            result[field] = json.loads(result.get(field) or "{}")
        return result
    finally:
        conn.close()


# ──────────────────────────────────────────────────────────────────────
#  CRM Notes — conversation logs / vendor interactions
# ──────────────────────────────────────────────────────────────────────

def add_vendor_note(
    domain: str,
    content: str,
    note_type: str = "general",
    created_by: str = "user",
) -> int:
    """Add a CRM note/interaction log for a vendor."""
    conn = _get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO vendor_notes (vendor_domain, note_type, content, created_by)
               VALUES (?, ?, ?, ?)""",
            (domain, note_type, content, created_by),
        )
        conn.commit()
        logger.info(f"📝 CRM note added for {domain}")
        return cursor.lastrowid
    finally:
        conn.close()


def get_vendor_notes(domain: str, limit: int = 20) -> list[dict]:
    """Get all CRM notes for a specific vendor."""
    conn = _get_connection()
    try:
        rows = conn.execute(
            """SELECT id, vendor_domain, note_type, content, created_by, created_at
               FROM vendor_notes
               WHERE vendor_domain = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (domain, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ──────────────────────────────────────────────────────────────────────
#  Campaign Tracking
# ──────────────────────────────────────────────────────────────────────

def save_campaigns(domain: str, marketing_output: dict) -> int:
    """Auto-save proposed campaigns from a marketing analysis."""
    conn = _get_connection()
    count = 0
    try:
        for campaign in marketing_output.get("ad_campaigns", []):
            conn.execute(
                """INSERT INTO campaign_tracking
                   (vendor_domain, campaign_name, campaign_type, status, details)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    domain,
                    campaign.get("name", "Unnamed"),
                    "ad",
                    "proposed",
                    json.dumps(campaign, default=str),
                ),
            )
            count += 1

        for campaign in marketing_output.get("launch_campaigns", []):
            conn.execute(
                """INSERT INTO campaign_tracking
                   (vendor_domain, campaign_name, campaign_type, status, details)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    domain,
                    campaign.get("title", "Unnamed"),
                    "launch",
                    "proposed",
                    json.dumps(campaign, default=str),
                ),
            )
            count += 1

        conn.commit()
        logger.info(f"📋 {count} campaign(s) tracked for {domain}")
        return count
    finally:
        conn.close()


def get_vendor_campaigns(domain: str) -> list[dict]:
    """Get all tracked campaigns for a vendor."""
    conn = _get_connection()
    try:
        rows = conn.execute(
            """SELECT id, vendor_domain, campaign_name, campaign_type,
                      status, details, created_at
               FROM campaign_tracking
               WHERE vendor_domain = ?
               ORDER BY created_at DESC""",
            (domain,),
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["details"] = json.loads(d.get("details") or "{}")
            results.append(d)
        return results
    finally:
        conn.close()


def update_campaign_status(campaign_id: int, new_status: str) -> bool:
    """Update a campaign's status (proposed → active → completed → cancelled)."""
    conn = _get_connection()
    try:
        conn.execute(
            """UPDATE campaign_tracking
               SET status = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (new_status, campaign_id),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def get_crm_stats() -> dict:
    """Get overall CRM statistics for the dashboard."""
    conn = _get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM vendor_analyses").fetchone()[0]
        avg_score = conn.execute("SELECT AVG(lead_score) FROM vendor_analyses").fetchone()[0] or 0
        avg_conf = conn.execute("SELECT AVG(confidence) FROM vendor_analyses").fetchone()[0] or 0
        total_campaigns = conn.execute("SELECT COUNT(*) FROM campaign_tracking").fetchone()[0]
        total_notes = conn.execute("SELECT COUNT(*) FROM vendor_notes").fetchone()[0]

        return {
            "total_analyses": total,
            "avg_lead_score": round(avg_score, 1),
            "avg_confidence": round(avg_conf, 2),
            "total_campaigns": total_campaigns,
            "total_notes": total_notes,
        }
    finally:
        conn.close()
