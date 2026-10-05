"""Push alerts via Bark (https://bark.day.app) — handy for iOS users."""
from __future__ import annotations

import urllib.parse
import urllib.request

from .base import Notifier


class BarkNotifier(Notifier):
    def __init__(self, key: str, server: str = "https://api.day.app"):
        if not key:
            raise ValueError("Bark key is required")
        self.key = key
        self.server = server.rstrip("/")

    def send(self, title: str, message: str) -> None:
        url = (
            f"{self.server}/{self.key}/"
            f"{urllib.parse.quote(title)}/{urllib.parse.quote(message)}"
        )
        with urllib.request.urlopen(url, timeout=15):
            pass
