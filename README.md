# bonjournee

`bonjournee` is a local-first implementation of the **Personal Commute Reliability Engine (PCRE)**.
It is designed to run from a personal laptop, collect transit data safely, and produce reliability metrics without hammering APIs.

## What this repo includes (v0.1)

- Python collector service for TfL and National Rail-style endpoints.
- SQLite database schema for trains, predictions, actuals, route instances, service status, and API audit logs.
- Rate budgeting and adaptive backoff:
  - `MAX_REQUESTS_PER_MINUTE = 50`
  - `MAX_REQUESTS_PER_HOUR = 2000`
- Conditional polling and response hashing to avoid duplicate persistence.
- Monitoring windows (Mon–Fri):
  - Morning `05:30–08:30`
  - Afternoon `15:00–18:30`
  - Outside window uses lower-frequency intervals.
- Basic analytics queries for journey-time and reliability metrics.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

# initialize local database
bonjournee init-db

# run one collection cycle
bonjournee collect-once

# run scheduler loop
bonjournee run

# compute summary metrics
bonjournee metrics

# fetch next expected train for a station (all directions)
bonjournee next-train --station "Northwick Park"
```

## Configuration

Environment variables:

- `BONJOURNEE_DB_PATH` (default: `bonjournee.db`)
- `TFL_APP_ID` / `TFL_APP_KEY` (optional but recommended)
- `NR_API_KEY` (placeholder for rail provider key)

## Notes

- This project intentionally avoids route-planner and public UI features.
- Polling frequency never goes below 30 seconds; defaults are 60s in-window and 300s out-of-window.
- Sleep/resume is handled by detecting time jumps and immediately running a catch-up poll.
