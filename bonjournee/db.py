from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from bonjournee.config import settings


SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS trains (
    train_id TEXT PRIMARY KEY,
    operator TEXT,
    origin TEXT,
    destination TEXT,
    service_type TEXT,
    scheduled_departure TEXT,
    scheduled_arrival TEXT
);

CREATE TABLE IF NOT EXISTS predictions (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    train_id TEXT,
    station TEXT NOT NULL,
    timestamp_polled TEXT NOT NULL,
    predicted_departure TEXT,
    predicted_arrival TEXT,
    platform TEXT,
    status TEXT,
    raw_hash TEXT,
    UNIQUE(train_id, station, timestamp_polled),
    FOREIGN KEY(train_id) REFERENCES trains(train_id)
);

CREATE TABLE IF NOT EXISTS actuals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    train_id TEXT,
    station TEXT NOT NULL,
    actual_departure TEXT,
    actual_arrival TEXT,
    delay_seconds INTEGER,
    cancellation_flag INTEGER DEFAULT 0,
    platform_actual TEXT,
    FOREIGN KEY(train_id) REFERENCES trains(train_id)
);

CREATE TABLE IF NOT EXISTS route_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_family TEXT NOT NULL,
    date TEXT NOT NULL,
    departure_time TEXT,
    arrival_time TEXT,
    total_duration INTEGER,
    success_flag INTEGER,
    lateness_minutes INTEGER
);

CREATE TABLE IF NOT EXISTS service_status_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    line TEXT NOT NULL,
    severity TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS api_request_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    response_code INTEGER,
    latency_ms INTEGER,
    backoff_event TEXT
);

CREATE INDEX IF NOT EXISTS idx_predictions_station_ts ON predictions(station, timestamp_polled);
CREATE INDEX IF NOT EXISTS idx_actuals_station ON actuals(station);
CREATE INDEX IF NOT EXISTS idx_route_instances_family_date ON route_instances(route_family, date);
"""


def init_db(path: str | None = None) -> None:
    db_path = path or settings.db_path
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


@contextmanager
def get_conn(path: str | None = None):
    db_path = path or settings.db_path
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
