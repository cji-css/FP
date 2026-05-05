#!/usr/bin/env python3
"""Start the Game 67 browser UI (local HTTP server). Run from the project root."""

import argparse

from backend import run_browser

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Game 67 — browser server")
    p.add_argument("--port", type=int, default=8765, help="Local port (default: 8765)")
    p.add_argument("--no-browser", action="store_true", help="Do not open a browser tab")
    args = p.parse_args()
    run_browser(port=args.port, open_browser=not args.no_browser)
