from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json
import time
from typing import Any

import requests

from bonjournee.db import get_conn
from bonjournee.rate_limit import RequestBudget


@dataclass
class EndpointState:
    unchanged_count: int = 0
    next_allowed_poll: datetime | None = None
    backoff_until: datetime | None = None
    last_hash: str | None = None
    last_status_hash: str | None = None


@dataclass
class BaseCollector:
    name: str
    budget: RequestBudget
    endpoint_state: dict[str, EndpointState] = field(default_factory=dict)
    timeout_seconds: int = 15

    def can_poll(self, key: str, now: datetime | None = None) -> bool:
        now = now or datetime.utcnow()
        state = self.endpoint_state.setdefault(key, EndpointState())
        if state.backoff_until and now < state.backoff_until:
            return False
        if state.next_allowed_poll and now < state.next_allowed_poll:
            return False
        return True

    def request_json(self, endpoint: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any] | list[Any] | None:
        self.budget.wait_for_slot()
        started = time.perf_counter()
        code = None
        backoff_event = None
        try:
            response = requests.get(endpoint, params=params, headers=headers, timeout=self.timeout_seconds)
            code = response.status_code
            if response.status_code == 429 or 500 <= response.status_code < 600:
                backoff_event = self.register_backoff(endpoint)
                return None
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            backoff_event = self.register_backoff(endpoint)
            return None
        except requests.RequestException:
            backoff_event = self.register_backoff(endpoint)
            return None
        finally:
            latency_ms = int((time.perf_counter() - started) * 1000)
            with get_conn() as conn:
                conn.execute(
                    "INSERT INTO api_request_log(endpoint, timestamp, response_code, latency_ms, backoff_event) VALUES (?, ?, ?, ?, ?)",
                    (endpoint, datetime.utcnow().isoformat(), code, latency_ms, backoff_event),
                )

    def register_backoff(self, endpoint: str) -> str:
        state = self.endpoint_state.setdefault(endpoint, EndpointState())
        size = min(900, 30 * (2 ** min(5, state.unchanged_count)))
        state.backoff_until = datetime.utcnow() + timedelta(seconds=size)
        return f"backoff_{size}s"

    def should_persist(self, key: str, payload: Any) -> bool:
        encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
        state = self.endpoint_state.setdefault(key, EndpointState())
        if state.last_hash == digest:
            state.unchanged_count += 1
            state.next_allowed_poll = datetime.utcnow() + timedelta(seconds=min(900, 60 + state.unchanged_count * 30))
            return False
        state.last_hash = digest
        state.unchanged_count = 0
        state.next_allowed_poll = None
        return True
