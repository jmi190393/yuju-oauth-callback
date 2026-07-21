"""Punto de entrada Flask (WSGI puro — compatible con uWSGI de PythonAnywhere).

Sirve la API (blueprint /api) y la PWA estática. Al importarse crea las tablas
y siembra los datos iniciales una sola vez.
"""
import os

from flask import Flask, g, send_file
from sqlalchemy.exc import SQLAlchemyError

from .api import bp
from .auth import SESSION_DAYS  # noqa: F401 (asegura carga temprana del secreto)
from .db import Base, SessionLocal, engine
from .models import User  # noqa: F401
from .seed import seed

STATIC_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "static"))

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
app.register_blueprint(bp)

# Inicialización (una vez por proceso): tablas + siembra.
Base.metadata.create_all(engine)
with SessionLocal() as _db:
    seed(_db)


@app.before_request
def _open_db():
    g.db = SessionLocal()


@app.teardown_request
def _close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        if exc is not None and isinstance(exc, SQLAlchemyError):
            db.rollback()
        db.close()


@app.get("/manifest.webmanifest")
def manifest():
    return send_file(os.path.join(STATIC_DIR, "manifest.webmanifest"))


@app.get("/sw.js")
def sw():
    return send_file(os.path.join(STATIC_DIR, "sw.js"))


@app.get("/")
@app.get("/<path:path>")
def spa(path=""):
    return send_file(os.path.join(STATIC_DIR, "index.html"))
