"""CLI: python -m farewatch check --config config.yaml"""
from __future__ import annotations

import argparse

from .config import load_config
from .notifiers.base import build_notifiers
from .providers.amadeus import AmadeusProvider
from .providers.mock import MockProvider
from .watcher import Watcher


def build_provider(config):
    if config.provider == "mock":
        return MockProvider()
    a = config.amadeus
    return AmadeusProvider(a.client_id, a.client_secret, a.hostname)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="farewatch",
        description="Watch flight fares and get notified on price drops.",
    )
    parser.add_argument("command", choices=["check"], help="run one fare check")
    parser.add_argument("--config", default="config.yaml", help="config file path")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print alerts to console instead of sending them",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    provider = build_provider(config)
    notifiers = build_notifiers(config, dry_run=args.dry_run)

    alerts = Watcher(config, provider, notifiers).check()
    total = sum(len(r.all_dates()) for r in config.routes)
    print(f"Checked {total} route/date combinations, {len(alerts)} new alert(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
