import sqlite3
import json
import shutil
from datetime import datetime
from typing import Dict, Any, Optional
from backend.app.services.retraining import DB_PATH

def init_job_queue():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS job_queue (
        job_id TEXT PRIMARY KEY,
        status TEXT,
        created_at TEXT,
        total_items INTEGER,
        payload TEXT,
        results TEXT,
        retry_count INTEGER DEFAULT 0
    )""")
    conn.commit()
    conn.close()

init_job_queue()

def enqueue_job(job_id: str, payload: list):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO job_queue (job_id, status, created_at, total_items, payload, results, retry_count)
    VALUES (?, 'PENDING', ?, ?, ?, NULL, 0)
    """, (job_id, datetime.utcnow().isoformat(), len(payload), json.dumps(payload)))
    conn.commit()
    conn.close()

def update_job_status(job_id: str, status: str, results: list):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    UPDATE job_queue SET status = ?, results = ? WHERE job_id = ?
    """, (status, json.dumps(results), job_id))
    conn.commit()
    conn.close()

def get_persisted_job(job_id: str) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT job_id, status, created_at, total_items, results FROM job_queue WHERE job_id = ?", (job_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "job_id": row[0],
            "status": row[1],
            "created_at": row[2],
            "total_items": row[3],
            "results": json.loads(row[4]) if row[4] else []
        }
    return None

def create_database_backup() -> str:
    backup_path = f"{DB_PATH}.backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(DB_PATH, backup_path)
    return backup_path