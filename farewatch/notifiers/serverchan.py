"""Push alerts via ServerChan (https://sct.ftqq.com) — handy for WeChat users."""
from __future__ import annotations

import urllib.parse
import urllib.request

from .base import Notifier


class ServerChanNotifier(Notifier):
    def __init__(self, key: str):
        if not key:
            raise ValueError("ServerChan SendKey is required")
        self.key = key

    def send(self, title: str, message: str) -> None:
        data = urllib.parse.urlencode({"title": title, "desp": message}).encode()
        req = urllib.request.Request(
            f"https://sctapi.ftqq.com/{self.key}.send", data=data
        )
        with urllib.request.urlopen(req, timeout=15):
            pass
