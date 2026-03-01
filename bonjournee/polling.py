from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
import time as time_module

from bonjournee.config import settings
from bonjournee.rate_limit import RequestBudget
from bonjournee.sources.rail import RailCollector
from bonjournee.sources.tfl import TfLCollector


TFL_STOPS = {
    "940GZZLUNWP": "Northwick Park",
    "940GZZLUHOH": "Harrow-on-the-Hill",
    "940GZZLUWYP": "Wembley Park",
    "940GZZLUFYR": "Finchley Road",
}

RAIL_ENDPOINTS = {
    "West Hampstead Thameslink": "https://api.example.local/rail/west-hampstead",
    "Farringdon": "https://api.example.local/rail/farringdon",
    "London Bridge": "https://api.example.local/rail/london-bridge",
    "Clapham Junction": "https://api.example.local/rail/clapham-junction",
    "Cheam": "https://api.example.local/rail/cheam",
    "Sutton": "https://api.example.local/rail/sutton",
}


@dataclass
class CollectorRuntime:
    tfl: TfLCollector
    rail: RailCollector


def in_monitoring_window(now: datetime | None = None) -> bool:
    now = now or datetime.now()
    if now.weekday() >= 5:
        return False
    morning = time(5, 30) <= now.time() <= time(8, 30)
    afternoon = time(15, 0) <= now.time() <= time(18, 30)
    return morning or afternoon


def run_collection_cycle(runtime: CollectorRuntime) -> None:
    for stop_id, name in TFL_STOPS.items():
        runtime.tfl.poll_station_arrivals(stop_id, name)
    runtime.tfl.poll_line_status(["metropolitan", "jubilee"])
    for station, endpoint in RAIL_ENDPOINTS.items():
        runtime.rail.poll_station_board(endpoint, station)


def create_runtime() -> CollectorRuntime:
    budget = RequestBudget(
        max_per_minute=settings.max_requests_per_minute,
        max_per_hour=settings.max_requests_per_hour,
    )
    return CollectorRuntime(
        tfl=TfLCollector(name="tfl", budget=budget),
        rail=RailCollector(name="rail", budget=budget),
    )


def run_scheduler() -> None:
    runtime = create_runtime()
    last_tick = datetime.now()
    while True:
        now = datetime.now()
        if now - last_tick > timedelta(minutes=10):
            run_collection_cycle(runtime)
        interval = (
            settings.poll_interval_in_window_seconds
            if in_monitoring_window(now)
            else settings.poll_interval_outside_window_seconds
        )
        run_collection_cycle(runtime)
        last_tick = now
        time_module.sleep(interval)
