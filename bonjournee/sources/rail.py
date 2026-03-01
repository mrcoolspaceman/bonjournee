from __future__ import annotations

from datetime import datetime
from typing import Any

from bonjournee.config import settings
from bonjournee.db import get_conn
from bonjournee.sources.base import BaseCollector


class RailCollector(BaseCollector):
    """Generic rail collector for Darwin/RTT-like boards.

    Endpoint payload shape should be adapted in integration; this class stores common fields.
    """

    def poll_station_board(self, endpoint: str, station_name: str) -> None:
        if not self.can_poll(endpoint):
            return
        headers: dict[str, Any] = {}
        if settings.nr_api_key:
            headers["Authorization"] = f"Bearer {settings.nr_api_key}"

        payload = self.request_json(endpoint, headers=headers)
        if payload is None:
            return
        if not self.should_persist(endpoint, payload):
            return

        services = payload.get("services", []) if isinstance(payload, dict) else []
        polled_at = datetime.utcnow().isoformat()

        with get_conn() as conn:
            for service in services:
                train_id = str(service.get("service_id") or service.get("rid") or "")
                conn.execute(
                    "INSERT OR IGNORE INTO trains(train_id, operator, origin, destination, service_type, scheduled_departure, scheduled_arrival) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        train_id,
                        service.get("operator"),
                        service.get("origin"),
                        service.get("destination"),
                        service.get("service_type"),
                        service.get("std"),
                        service.get("sta"),
                    ),
                )
                conn.execute(
                    "INSERT OR IGNORE INTO predictions(train_id, station, timestamp_polled, predicted_departure, predicted_arrival, platform, status, raw_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        train_id,
                        station_name,
                        polled_at,
                        service.get("etd") or service.get("std"),
                        service.get("eta") or service.get("sta"),
                        service.get("platform"),
                        service.get("status"),
                        None,
                    ),
                )
                if service.get("atd") or service.get("ata") or service.get("cancelled"):
                    conn.execute(
                        "INSERT INTO actuals(train_id, station, actual_departure, actual_arrival, delay_seconds, cancellation_flag, platform_actual) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            train_id,
                            station_name,
                            service.get("atd"),
                            service.get("ata"),
                            service.get("delay_seconds"),
                            int(bool(service.get("cancelled"))),
                            service.get("platform"),
                        ),
                    )
