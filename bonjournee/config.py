from __future__ import annotations

from dataclasses import dataclass, field
import os


MONITORED_STATIONS = [
    "Northwick Park",
    "Harrow-on-the-Hill",
    "Wembley Park",
    "Finchley Road",
    "West Hampstead (Jubilee)",
    "West Hampstead Thameslink",
    "Farringdon",
    "London Bridge",
    "Clapham Junction",
    "Cheam",
    "Sutton",
    "Kenton",
    "Willesden Junction",
    "Harrow & Wealdstone",
    "Wembley Central",
]

BUS_ROUTES = ["SL7", "151", "213"]


@dataclass(slots=True)
class Settings:
    db_path: str = os.getenv("BONJOURNEE_DB_PATH", "bonjournee.db")
    tfl_app_id: str | None = os.getenv("TFL_APP_ID")
    tfl_app_key: str | None = os.getenv("TFL_APP_KEY")
    nr_api_key: str | None = os.getenv("NR_API_KEY")

    max_requests_per_minute: int = 50
    max_requests_per_hour: int = 2000

    poll_interval_in_window_seconds: int = 60
    poll_interval_outside_window_seconds: int = 300

    stations: list[str] = field(default_factory=lambda: MONITORED_STATIONS.copy())
    bus_routes: list[str] = field(default_factory=lambda: BUS_ROUTES.copy())


settings = Settings()
