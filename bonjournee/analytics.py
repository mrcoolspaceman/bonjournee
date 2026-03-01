from __future__ import annotations

from statistics import mean, median

from bonjournee.db import get_conn


def compute_route_metrics() -> dict[str, dict[str, float]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT route_family, total_duration, success_flag, lateness_minutes FROM route_instances"
        ).fetchall()

    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["route_family"], []).append(dict(row))

    metrics: dict[str, dict[str, float]] = {}
    for route, values in grouped.items():
        durations = [v["total_duration"] for v in values if v["total_duration"] is not None]
        late = [v for v in values if (v["lateness_minutes"] or 0) > 10]
        failed = [v for v in values if (v["success_flag"] or 0) == 0]
        metrics[route] = {
            "mean_journey_time": float(mean(durations)) if durations else 0.0,
            "median_journey_time": float(median(durations)) if durations else 0.0,
            "p_delay_gt_10m": len(late) / len(values) if values else 0.0,
            "p_cancellation_or_failure": len(failed) / len(values) if values else 0.0,
        }
    return metrics
