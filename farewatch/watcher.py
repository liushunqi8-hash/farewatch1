"""Core watch loop: check fares, compare with targets, notify once per drop."""
from __future__ import annotations

import json
import os


class Watcher:
    def __init__(self, config, provider, notifiers):
        self.config = config
        self.provider = provider
        self.notifiers = notifiers
        self.state_path = os.path.expanduser(config.state_file)
        self.state = self._load_state()

    def _load_state(self) -> dict:
        try:
            with open(self.state_path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {"alerted": []}

    def _save_state(self) -> None:
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        # keep the alert history bounded
        self.state["alerted"] = self.state.get("alerted", [])[-500:]
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def check(self) -> list[dict]:
        """Check every route/date. Returns the list of new alerts."""
        alerts: list[dict] = []
        for route in self.config.routes:
            for dep_date in route.all_dates():
                quote = self.provider.cheapest(
                    route.origin,
                    route.destination,
                    dep_date,
                    currency=route.currency,
                    adults=route.adults,
                )
                if quote is None:
                    continue
                hit = quote.price <= route.target_price
                key = f"{route.origin}-{route.destination}-{dep_date}-{quote.price:.0f}"
                if hit and key not in self.state["alerted"]:
                    alert = {
                        "route": f"{route.origin} → {route.destination}",
                        "date": dep_date,
                        "price": quote.price,
                        "currency": quote.currency,
                        "airline": quote.airline,
                        "stops": quote.stops,
                    }
                    alerts.append(alert)
                    self.state["alerted"].append(key)
                    title = f"✈️ Fare drop: {alert['route']} {dep_date}"
                    stops = (
                        "nonstop"
                        if quote.stops == 0
                        else f"{quote.stops} stop(s)"
                        if quote.stops > 0
                        else "stops n/a"
                    )
                    message = (
                        f"{quote.price:.0f} {quote.currency} "
                        f"(target ≤ {route.target_price:.0f}) · "
                        f"{quote.airline} · {stops}"
                    )
                    for n in self.notifiers:
                        n.send(title, message)
        self._save_state()
        return alerts
