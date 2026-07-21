#!/usr/bin/env python3
"""Arranque local/producción: python run.py (o uvicorn app.main:app)."""
import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0",
                port=int(os.environ.get("PORT", 8000)),
                reload=bool(os.environ.get("DEV")))
