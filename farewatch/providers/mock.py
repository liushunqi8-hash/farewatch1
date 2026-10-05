"""Mock provider for demos and tests: deterministic pseudo-prices."""
from __future__ import annotations

import hashlib

from .base import FareProvider, FareQuote


class MockProvider(FareProvider):
    def cheapest(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        currency: str = "CNY",
        adults: int = 1,
    ) -> FareQuote | None:
        seed = int(
            hashlib.md5(f"{origin}{destination}{departure_date}".encode()).hexdigest(), 16
        )
        return FareQuote(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            price=float(1200 + (seed % 4000)),
            currency=currency,
            airline="MOCK",
            stops=seed % 2,
        )
