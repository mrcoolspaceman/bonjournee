from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from bonjournee.db import get_conn


@dataclass(slots=True)
class NextTrainResult:
    station: str
    timestamp_polled: str
    predicted_time: str
    platform: str | None
    status: str | None
    train_id: str | None


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def get_next_train(station: str, now: datetime | None = None) -> NextTrainResult | None:
    """Return next expected train for a station, regardless of direction.

    Uses the latest prediction snapshot for the station, then selects the earliest
    predicted timestamp at or after `now`.
    """

    now = now or datetime.utcnow()

    with get_conn() as conn:
        latest = conn.execute(
            "SELECT MAX(timestamp_polled) AS ts FROM predictions WHERE station = ?",
            (station,),
        ).fetchone()
        if not latest or not latest["ts"]:
            return None

        rows = conn.execute(
            """
            SELECT train_id, station, timestamp_polled, predicted_departure, predicted_arrival, platform, status
            FROM predictions
            WHERE station = ? AND timestamp_polled = ?
            """,
            (station, latest["ts"]),
        ).fetchall()

    best: tuple[datetime, dict] | None = None
    for row in rows:
        d = dict(row)
        candidate = _parse_dt(d.get("predicted_departure")) or _parse_dt(d.get("predicted_arrival"))
        if candidate is None:
            continue
        if candidate < now:
            continue
        if best is None or candidate < best[0]:
            best = (candidate, d)

    if best is None:
        return None

    _, row = best
    predicted_time = row.get("predicted_departure") or row.get("predicted_arrival")
    return NextTrainResult(
        station=row["station"],
        timestamp_polled=row["timestamp_polled"],
        predicted_time=predicted_time,
        platform=row.get("platform"),
        status=row.get("status"),
        train_id=row.get("train_id"),
    )
