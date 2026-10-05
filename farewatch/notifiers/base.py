"""Notifier interface."""
from __future__ import annotations

from abc import ABC, abstractmethod


class Notifier(ABC):
    @abstractmethod
    def send(self, title: str, message: str) -> None:
        """Deliver a notification."""


def build_notifiers(config, dry_run: bool = False) -> list[Notifier]:
    from .bark import BarkNotifier
    from .console import ConsoleNotifier
    from .serverchan import ServerChanNotifier

    notifiers: list[Notifier] = []
    for n in config.notifiers:
        if dry_run or n.type == "console":
            notifiers.append(ConsoleNotifier())
        elif n.type == "bark":
            notifiers.append(BarkNotifier(**n.options))
        elif n.type == "serverchan":
            notifiers.append(ServerChanNotifier(**n.options))
        else:
            raise ValueError(f"Unknown notifier type: {n.type}")
    return notifiers
