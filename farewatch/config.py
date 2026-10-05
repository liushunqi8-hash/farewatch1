"""Configuration loading for farewatch."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date, timedelta

import yaml


@dataclass
class DateRange:
    start: str
    end: str
    step_days: int = 7

    def expand(self) -> list[str]:
        days: list[str] = []
        cur = date.fromisoformat(self.start)
        end = date.fromisoformat(self.end)
        while cur <= end:
            days.append(cur.isoformat())
            cur += timedelta(days=self.step_days)
        return days


@dataclass
class Route:
    origin: str
    destination: str
    dates: list[str] = field(default_factory=list)
    date_range: DateRange | None = None
    target_price: float = 0
    currency: str = "CNY"
    adults: int = 1

    def all_dates(self) -> list[str]:
        dates = list(self.dates)
        if self.date_range:
            dates.extend(self.date_range.expand())
        return sorted(set(dates))


@dataclass
class AmadeusConfig:
    client_id: str
    client_secret: str
    hostname: str = "test"  # test | production


@dataclass
class NotifierConfig:
    type: str
    options: dict = field(default_factory=dict)


@dataclass
class Config:
    amadeus: AmadeusConfig
    routes: list[Route]
    notifiers: list[NotifierConfig]
    state_file: str = "~/.farewatch/state.json"
    provider: str = "amadeus"  # amadeus | mock


def _expand_env(value):
    if isinstance(value, str):
        return os.path.expandvars(value)
    return value


def load_config(path: str) -> Config:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    am = raw.get("amadeus", {})
    amadeus = AmadeusConfig(
        client_id=_expand_env(am.get("client_id", "")),
        client_secret=_expand_env(am.get("client_secret", "")),
        hostname=am.get("hostname", "test"),
    )

    routes = []
    for r in raw.get("routes", []):
        dr = r.get("date_range")
        routes.append(
            Route(
                origin=r["origin"].upper(),
                destination=r["destination"].upper(),
                dates=r.get("departure_dates", []),
                date_range=DateRange(**dr) if dr else None,
                target_price=float(r.get("target_price", 0)),
                currency=r.get("currency", "CNY"),
                adults=int(r.get("adults", 1)),
            )
        )

    notifiers = [
        NotifierConfig(
            type=n["type"],
            options={k: _expand_env(v) for k, v in n.items() if k != "type"},
        )
        for n in raw.get("notifiers", [{"type": "console"}])
    ]

    return Config(
        amadeus=amadeus,
        routes=routes,
        notifiers=notifiers,
        state_file=raw.get("state_file", "~/.farewatch/state.json"),
        provider=raw.get("provider", "amadeus"),
    )
