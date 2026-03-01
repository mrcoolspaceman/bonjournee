from __future__ import annotations

from datetime import datetime
from typing import Any

from bonjournee.config import settings
from bonjournee.db import get_conn
from bonjournee.sources.base import BaseCollector


class TfLCollector(BaseCollector):
    base_url = "https://api.tfl.gov.uk"

    def poll_station_arrivals(self, stop_point_id: str, station_name: str) -> None:
        endpoint = f"{self.base_url}/StopPoint/{stop_point_id}/Arrivals"
        if not self.can_poll(endpoint):
            return
        params: dict[str, Any] = {}
        if settings.tfl_app_id and settings.tfl_app_key:
            params = {"app_id": settings.tfl_app_id, "app_key": settings.tfl_app_key}
        payload = self.request_json(endpoint, params=params)
        if payload is None:
            return
        if not self.should_persist(endpoint, payload):
            return

        polled_at = datetime.utcnow().isoformat()
        with get_conn() as conn:
            for row in payload:
                train_id = str(row.get("vehicleId") or row.get("id") or "")
                if train_id:
                    conn.execute(
                        "INSERT OR IGNORE INTO trains(train_id, operator, origin, destination, service_type, scheduled_departure, scheduled_arrival) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            train_id,
                            row.get("operatorName"),
                            row.get("towards"),
                            row.get("towards"),
                            row.get("modeName"),
                            None,
                            row.get("expectedArrival"),
                        ),
                    )
                conn.execute(
                    "INSERT OR IGNORE INTO predictions(train_id, station, timestamp_polled, predicted_departure, predicted_arrival, platform, status, raw_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        train_id or None,
                        station_name,
                        polled_at,
                        row.get("expectedArrival"),
                        row.get("expectedArrival"),
                        row.get("platformName"),
                        row.get("currentStatus"),
                        None,
                    ),
                )

    def poll_line_status(self, line_ids: list[str]) -> None:
        ids = ",".join(line_ids)
        endpoint = f"{self.base_url}/Line/{ids}/Status"
        if not self.can_poll(endpoint):
            return
        params: dict[str, Any] = {}
        if settings.tfl_app_id and settings.tfl_app_key:
            params = {"app_id": settings.tfl_app_id, "app_key": settings.tfl_app_key}
        payload = self.request_json(endpoint, params=params)
        if payload is None:
            return
        if not self.should_persist(endpoint, payload):
            return

        now = datetime.utcnow().isoformat()
        with get_conn() as conn:
            for line in payload:
                statuses = line.get("lineStatuses") or []
                for status in statuses:
                    conn.execute(
                        "INSERT INTO service_status_log(timestamp, line, severity, description) VALUES (?, ?, ?, ?)",
                        (now, line.get("name"), str(status.get("statusSeverity")), status.get("reason") or status.get("statusSeverityDescription")),
                    )
