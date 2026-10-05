"""Provider interface: anything that can return the cheapest fare."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class FareQuote:
    origin: str
    destination: str
    departure_date: str
    price: float
    currency: str
    airline: str = ""
    stops: int = -1


class FareProvider(ABC):
    @abstractmethod
    def cheapest(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        currency: str = "CNY",
        adults: int = 1,
    ) -> FareQuote | None:
        """Return the cheapest available quote, or None if nothing found."""
