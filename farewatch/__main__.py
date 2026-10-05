"""Allow `python -m farewatch check ...`"""
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
