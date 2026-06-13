"""SQLite job logger.

Tracks every scrub job: original filename, file type, status, which
metadata fields were stripped, and a timestamp. Backs the /history,
/status/<job_id> and /job/<job_id> endpoints.
"""

import json
import os
import sqlite3
import threading

_lock = threading.Lock()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    original_name TEXT NOT NULL,
    file_type TEXT,
    status TEXT NOT NULL,
    stripped_fields TEXT NOT NULL DEFAULT '[]',
    error TEXT,
    cleaned_filename TEXT,
    timestamp TEXT NOT NULL
);
"""


def _connect(db_path):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path):
    """Create the jobs table if it doesn't already exist."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with _lock:
        conn = _connect(db_path)
        try:
            conn.execute(_SCHEMA)
            conn.commit()
        finally:
            conn.close()


def create_job(db_path, job_id, original_name, file_type, timestamp):
    """Insert a new job row with status 'processing'."""
    with _lock:
        conn = _connect(db_path)
        try:
            conn.execute(
                """
                INSERT INTO jobs
                    (job_id, original_name, file_type, status, stripped_fields, timestamp)
                VALUES (?, ?, ?, 'processing', '[]', ?)
                """,
                (job_id, original_name, file_type, timestamp),
            )
            conn.commit()
        finally:
            conn.close()


def update_job_success(db_path, job_id, stripped_fields, cleaned_filename):
    """Mark a job as completed and record what was stripped."""
    with _lock:
        conn = _connect(db_path)
        try:
            conn.execute(
                """
                UPDATE jobs
                SET status = 'completed', stripped_fields = ?, cleaned_filename = ?
                WHERE job_id = ?
                """,
                (json.dumps(stripped_fields), cleaned_filename, job_id),
            )
            conn.commit()
        finally:
            conn.close()


def update_job_error(db_path, job_id, error_message):
    """Mark a job as failed and record the error message."""
    with _lock:
        conn = _connect(db_path)
        try:
            conn.execute(
                "UPDATE jobs SET status = 'failed', error = ? WHERE job_id = ?",
                (error_message, job_id),
            )
            conn.commit()
        finally:
            conn.close()


def get_job(db_path, job_id):
    """Return a job row as a dict, or None if it doesn't exist."""
    conn = _connect(db_path)
    try:
        row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def get_history(db_path, limit=50):
    """Return the most recent ``limit`` jobs, newest first."""
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM jobs ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


def delete_job(db_path, job_id):
    """Remove a job row entirely."""
    with _lock:
        conn = _connect(db_path)
        try:
            conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
            conn.commit()
        finally:
            conn.close()
