"""Punto de entrada FastAPI. Sirve la API y la PWA estática."""
import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import router
from .db import Base, SessionLocal, engine
from .seed import seed

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")

app = FastAPI(title="Finanzas personales y familiares", docs_url=None, redoc_url=None)
app.include_router(router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/manifest.webmanifest", include_in_schema=False)
def manifest():
    return FileResponse(os.path.join(STATIC_DIR, "manifest.webmanifest"),
                        media_type="application/manifest+json")


@app.get("/sw.js", include_in_schema=False)
def sw():
    return FileResponse(os.path.join(STATIC_DIR, "sw.js"),
                        media_type="application/javascript")


@app.get("/{path:path}", include_in_schema=False)
def spa(path: str):
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
