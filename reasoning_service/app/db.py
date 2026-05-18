import sqlite3
from pathlib import Path
import csv


DB_PATH = Path("app/events.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        people_count INTEGER NOT NULL,
        detected INTEGER NOT NULL,
        confidence REAL NOT NULL,
        position TEXT,
        inference_time_ms REAL NOT NULL,
        fps REAL NOT NULL,
        action TEXT NOT NULL,
        reason TEXT NOT NULL,
        stable_detection INTEGER NOT NULL,
        cooldown_active INTEGER NOT NULL,
        cooldown_remaining_sec REAL NOT NULL,
        e2e_latency_ms REAL NOT NULL
    )
    """
    )

    conn.commit()
    conn.close()


def insert_event(
    created_at: str,
    people_count: int,
    detected: bool,
    confidence: float,
    position: str | None,
    inference_time_ms: float,
    fps: float,
    action: str,
    reason: str,
    stable_detection: bool,
    cooldown_active: bool,
    cooldown_remaining_sec: float,
    e2e_latency_ms: float,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    INSERT INTO events (
        created_at,
        people_count,
        detected,
        confidence,
        position,
        inference_time_ms,
        fps,
        action,
        reason,
        stable_detection,
        cooldown_active,
        cooldown_remaining_sec,
        e2e_latency_ms
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            created_at,
            people_count,
            int(detected),
            confidence,
            position,
            inference_time_ms,
            fps,
            action,
            reason,
            int(stable_detection),
            int(cooldown_active),
            cooldown_remaining_sec,
            e2e_latency_ms,
        ),
    )

    conn.commit()
    conn.close()


def get_all_events(limit: int = 100):
    conn = get_connection()
    cursor = conn.cursor()

    rows = cursor.execute(
        """
    SELECT * FROM events
    ORDER BY id DESC
    LIMIT ?
    """,
        (limit,),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_latest_event():
    conn = get_connection()
    cursor = conn.cursor()

    row = cursor.execute(
        """
    SELECT * FROM events
    ORDER BY id DESC
    LIMIT 1
    """
    ).fetchone()

    conn.close()

    return dict(row) if row else None


def export_events_to_csv(csv_path: str):
    conn = get_connection()
    cursor = conn.cursor()

    rows = cursor.execute(
        """
    SELECT * FROM events
    ORDER BY id DESC
    """
    ).fetchall()

    conn.close()

    if not rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "id",
                    "created_at",
                    "people_count",
                    "detected",
                    "confidence",
                    "position",
                    "inference_time_ms",
                    "fps",
                    "action",
                    "reason",
                    "stable_detection",
                    "cooldown_active",
                    "cooldown_remaining_sec",
                    "e2e_latency_ms",
                ]
            )
        return

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(rows[0].keys())

        for row in rows:
            writer.writerow(row)
