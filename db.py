"""
db.py - SQLite Database Management for PotholeVerify
Handles initialization, storing verified reports, fetching duplicate check hashes,
and managing reports requiring admin review.
"""

import os
import sqlite3
import json
from datetime import datetime

# Default database and uploads directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "pothole_verify.db")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

# Ensure uploads directory exists
os.makedirs(UPLOADS_DIR, exist_ok=True)


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Create and return a database connection with Row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """
    Initialize SQLite database schema.
    Creates table 'reports' if it does not already exist.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT NOT NULL,
                phash TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                score REAL NOT NULL,
                decision TEXT NOT NULL,
                reasons_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def save_report(
    image_path: str,
    phash: str,
    lat: float,
    lon: float,
    score: float,
    decision: str,
    reasons: list | dict,
    db_path: str = DB_PATH,
) -> int:
    """
    Save a report into the database.
    Note: Reject decisions are logged if desired, but duplicate checks
    only query records where decision in ('Accept', 'Review').
    """
    init_db(db_path)
    created_at = datetime.now().isoformat()
    reasons_str = json.dumps(reasons)

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO reports (image_path, phash, lat, lon, score, decision, reasons_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (image_path, phash, lat, lon, score, decision, reasons_str, created_at),
        )
        conn.commit()
        return cursor.lastrowid


def get_known_hashes(db_path: str = DB_PATH) -> list[tuple[int, str]]:
    """
    Retrieve perceptual hashes from existing accepted and review reports.
    Rejected report hashes are excluded so legitimate reports are not blocked.
    Returns: list of (report_id, phash_str).
    """
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, phash
            FROM reports
            WHERE decision IN ('Accept', 'Review')
            """
        )
        rows = cursor.fetchall()
        return [(row["id"], row["phash"]) for row in rows]


def get_pending_reviews(db_path: str = DB_PATH) -> list[dict]:
    """
    Fetch all reports pending manual review (decision == 'Review').
    """
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, image_path, phash, lat, lon, score, decision, reasons_json, created_at
            FROM reports
            WHERE decision = 'Review'
            ORDER BY id DESC
            """
        )
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append(
                {
                    "id": row["id"],
                    "image_path": row["image_path"],
                    "phash": row["phash"],
                    "lat": row["lat"],
                    "lon": row["lon"],
                    "score": row["score"],
                    "decision": row["decision"],
                    "reasons": json.loads(row["reasons_json"]),
                    "created_at": row["created_at"],
                }
            )
        return results


def update_report_decision(
    report_id: int, new_decision: str, db_path: str = DB_PATH
) -> bool:
    """
    Update decision status of a report (e.g., Accept or Reject after review).
    """
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE reports
            SET decision = ?
            WHERE id = ?
            """,
            (new_decision, report_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_all_reports(db_path: str = DB_PATH) -> list[dict]:
    """Fetch all reports for audit / summary statistics."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reports ORDER BY id DESC")
        rows = cursor.fetchall()
        return [
            {
                "id": row["id"],
                "image_path": row["image_path"],
                "phash": row["phash"],
                "lat": row["lat"],
                "lon": row["lon"],
                "score": row["score"],
                "decision": row["decision"],
                "reasons": json.loads(row["reasons_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

