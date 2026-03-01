from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time


@dataclass
class RequestBudget:
    max_per_minute: int
    max_per_hour: int
    minute_window: deque[datetime] = field(default_factory=deque)
    hour_window: deque[datetime] = field(default_factory=deque)

    def wait_for_slot(self) -> None:
        while True:
            now = datetime.utcnow()
            self._prune(now)
            if len(self.minute_window) < self.max_per_minute and len(self.hour_window) < self.max_per_hour:
                self.minute_window.append(now)
                self.hour_window.append(now)
                return
            time.sleep(0.5)

    def _prune(self, now: datetime) -> None:
        minute_cutoff = now - timedelta(minutes=1)
        hour_cutoff = now - timedelta(hours=1)
        while self.minute_window and self.minute_window[0] < minute_cutoff:
            self.minute_window.popleft()
        while self.hour_window and self.hour_window[0] < hour_cutoff:
            self.hour_window.popleft()
