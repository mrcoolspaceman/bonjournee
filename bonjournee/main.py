from __future__ import annotations

import argparse
import json

from bonjournee.analytics import compute_route_metrics
from bonjournee.db import init_db
from bonjournee.polling import create_runtime, run_collection_cycle, run_scheduler
from bonjournee.query import get_next_train


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="bonjournee PCRE CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init-db")
    sub.add_parser("collect-once")
    sub.add_parser("run")
    sub.add_parser("metrics")
    next_train = sub.add_parser("next-train")
    next_train.add_argument("--station", required=True, help="Station name as stored in predictions")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.cmd == "init-db":
        init_db()
        print("database initialized")
        return

    if args.cmd == "collect-once":
        init_db()
        runtime = create_runtime()
        run_collection_cycle(runtime)
        print("collection cycle complete")
        return

    if args.cmd == "run":
        init_db()
        run_scheduler()
        return

    if args.cmd == "metrics":
        init_db()
        print(json.dumps(compute_route_metrics(), indent=2))
        return

    if args.cmd == "next-train":
        init_db()
        next_train = get_next_train(args.station)
        if not next_train:
            print(json.dumps({"station": args.station, "next_train": None}, indent=2))
            return
        print(json.dumps({
            "station": next_train.station,
            "timestamp_polled": next_train.timestamp_polled,
            "predicted_time": next_train.predicted_time,
            "platform": next_train.platform,
            "status": next_train.status,
            "train_id": next_train.train_id,
        }, indent=2))
        return


if __name__ == "__main__":
    main()
