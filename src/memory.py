"""
Persistent memory system for the FromNear AI pipeline.

Uses SQLite to store and retrieve past vendor analyses, providing agents
with historical context for better, more consistent recommendations.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "memory.db")


def _get_connection() -> sqlite3.Connection:
    """Return a connection to the memory database, creating tables if needed."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vendor_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT,
            instagram_handle TEXT,
            category TEXT,
            location TEXT,
            lead_score REAL,
            confidence REAL,
            sales_output TEXT,
            marketing_output TEXT,
            structured_data TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


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
) -> int:
    """
    Persist a completed vendor analysis to the memory database.
    Returns the row ID of the new record.
    """
    conn = _get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO vendor_analyses
                (domain, instagram_handle, category, location,
                 lead_score, confidence, sales_output, marketing_output, structured_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                domain,
                instagram_handle,
                category.lower().strip() if category else "",
                location.lower().strip() if location else "",
                lead_score,
                confidence,
                json.dumps(sales_output, default=str),
                json.dumps(marketing_output, default=str),
                json.dumps(structured_data, default=str) if structured_data else "{}",
            ),
        )
        conn.commit()
        row_id = cursor.lastrowid
        logger.info(f"💾 Memory saved: {domain} (id={row_id}, score={lead_score})")
        return row_id
    finally:
        conn.close()


def get_similar_vendors(
    category: str = "",
    location: str = "",
    limit: int = 3,
) -> list[dict]:
    """
    Retrieve past analyses of vendors with similar category or location.
    Returns the most recent matches (up to `limit`).
    """
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
                   lead_score, confidence, sales_output, marketing_output, created_at
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
                "sales_summary": json.loads(row["sales_output"]).get("business_summary", ""),
                "created_at": row["created_at"],
            })

        logger.info(f"🧠 Memory recall: {len(results)} similar vendor(s) found")
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
                   lead_score, confidence, created_at
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
        result["sales_output"] = json.loads(result["sales_output"])
        result["marketing_output"] = json.loads(result["marketing_output"])
        result["structured_data"] = json.loads(result.get("structured_data") or "{}")
        return result
    finally:
        conn.close()
