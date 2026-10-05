"""Amadeus Self-Service API provider (free tier available).

Get free credentials at https://developers.amadeus.com/ and use the
"test" environment to try it out. Production access needs approval.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from .base import FareProvider, FareQuote

HOSTS = {
    "test": "https://test.api.amadeus.com",
    "production": "https://api.amadeus.com",
}


class AmadeusProvider(FareProvider):
    def __init__(self, client_id: str, client_secret: str, hostname: str = "test"):
        if not client_id or not client_secret:
            raise ValueError("Amadeus client_id / client_secret are required")
        self.base = HOSTS.get(hostname, HOSTS["test"])
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: str | None = None
        self._token_exp = 0.0

    def _auth(self) -> str:
        if self._token and time.time() < self._token_exp - 60:
            return self._token
        data = urllib.parse.urlencode(
            {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
        ).encode()
        req = urllib.request.Request(
            f"{self.base}/v1/security/oauth2/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.load(resp)
        self._token = body["access_token"]
        self._token_exp = time.time() + int(body.get("expires_in", 1799))
        return self._token

    def cheapest(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        currency: str = "CNY",
        adults: int = 1,
    ) -> FareQuote | None:
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "max": 10,
            "currencyCode": currency,
        }
        url = f"{self.base}/v2/shopping/flight-offers?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(
            url, headers={"Authorization": f"Bearer {self._auth()}"}
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.load(resp)
        except urllib.error.HTTPError:
            return None
        offers = body.get("data", [])
        if not offers:
            return None
        best = min(offers, key=lambda o: float(o["price"]["total"]))
        segments = best["itineraries"][0]["segments"]
        return FareQuote(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            price=float(best["price"]["total"]),
            currency=best["price"]["currency"],
            airline=segments[0].get("carrierCode", ""),
            stops=len(segments) - 1,
        )
