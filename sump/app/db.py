import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS water_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,        -- ISO 8601 UTC
    parameter TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT,
    source TEXT NOT NULL DEFAULT 'manual',   -- 'manual' | 'apex_daily_avg'
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_water_tests_param_time
    ON water_tests (parameter, timestamp);

CREATE TABLE IF NOT EXISTS targets (
    parameter TEXT PRIMARY KEY,
    target_low REAL,
    target_high REAL,
    unit TEXT,
    updated_at TEXT
);

-- Prevents duplicate daily-average rows if the scheduler runs twice
CREATE UNIQUE INDEX IF NOT EXISTS idx_water_tests_daily_avg_dedupe
    ON water_tests (parameter, source, substr(timestamp, 1, 10))
    WHERE source = 'apex_daily_avg';
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


# ---------- water_tests ----------

def add_entry(parameter: str, value: float, unit: str | None, source: str,
              notes: str | None = None, timestamp: str | None = None) -> int:
    ts = timestamp or datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT OR REPLACE INTO water_tests (timestamp, parameter, value, unit, source, notes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ts, parameter, value, unit, source, notes),
        )
        return cur.lastrowid


def delete_entry(entry_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM water_tests WHERE id = ?", (entry_id,))


def list_entries(parameter: str | None = None, days: int | None = None):
    query = "SELECT * FROM water_tests WHERE 1=1"
    params: list = []
    if parameter:
        query += " AND parameter = ?"
        params.append(parameter)
    if days:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        query += " AND timestamp >= ?"
        params.append(cutoff)
    query += " ORDER BY timestamp ASC"
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def list_parameters() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT DISTINCT parameter FROM water_tests ORDER BY parameter").fetchall()
        params = {r["parameter"] for r in rows}
    with get_conn() as conn:
        rows = conn.execute("SELECT parameter FROM targets").fetchall()
        params |= {r["parameter"] for r in rows}
    return sorted(params)


# ---------- targets ----------

def set_target(parameter: str, target_low: float | None, target_high: float | None, unit: str | None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO targets (parameter, target_low, target_high, unit, updated_at) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(parameter) DO UPDATE SET "
            "target_low=excluded.target_low, target_high=excluded.target_high, "
            "unit=excluded.unit, updated_at=excluded.updated_at",
            (parameter, target_low, target_high, unit, datetime.now(timezone.utc).isoformat()),
        )


def get_targets() -> list[dict]:
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM targets").fetchall()]


def get_target(parameter: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM targets WHERE parameter = ?", (parameter,)).fetchone()
        return dict(row) if row else None
