"""Print alerts to stdout."""
from .base import Notifier


class ConsoleNotifier(Notifier):
    def send(self, title: str, message: str) -> None:
        print(f"[farewatch] {title}\n{message}\n")
