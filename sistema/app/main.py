"""Punto de entrada FastAPI. Sirve la API y la PWA estática.

Los archivos estáticos se entregan como bytes completos (no streaming async),
para máxima compatibilidad con servidores WSGI como uWSGI de PythonAnywhere.
"""
import os

from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse

from .api import router
from .db import Base, SessionLocal, engine
from .seed import seed

STATIC_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "static"))

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".webmanifest": "application/manifest+json",
    ".json": "application/json",
    ".png": "image/png",
    ".ico": "image/x-icon",
}

app = FastAPI(title="Finanzas personales y familiares", docs_url=None, redoc_url=None)
app.include_router(router)


def _read(name: str) -> bytes:
    with open(os.path.join(STATIC_DIR, name), "rb") as f:
        return f.read()


def _serve(name: str) -> Response:
    path = os.path.normpath(os.path.join(STATIC_DIR, name))
    if not path.startswith(STATIC_DIR) or not os.path.isfile(path):
        return HTMLResponse(_read("index.html"))
    ext = os.path.splitext(path)[1]
    return Response(content=open(path, "rb").read(),
                    media_type=CONTENT_TYPES.get(ext, "application/octet-stream"))


@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)


@app.get("/static/{name:path}", include_in_schema=False)
def static_files(name: str):
    return _serve(name)


@app.get("/manifest.webmanifest", include_in_schema=False)
def manifest():
    return _serve("manifest.webmanifest")


@app.get("/sw.js", include_in_schema=False)
def sw():
    return _serve("sw.js")


@app.get("/{path:path}", include_in_schema=False)
def spa(path: str):
    return HTMLResponse(_read("index.html"))
