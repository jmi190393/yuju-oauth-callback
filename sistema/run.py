#!/usr/bin/env python3
"""Arranque local: python run.py"""
import os

from app.main import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)),
            debug=bool(os.environ.get("DEV")))
