"""Adaptador WSGI para PythonAnywhere (su hosting corre WSGI, no ASGI).

En el tab Web de PythonAnywhere, el archivo WSGI debe importar `application`
de aquí. El init (tablas + siembra) se hace directo porque el adaptador
no ejecuta los eventos de startup de FastAPI.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from a2wsgi import ASGIMiddleware

from app.db import Base, SessionLocal, engine
from app.main import app as asgi_app
from app.seed import seed

Base.metadata.create_all(engine)
with SessionLocal() as db:
    seed(db)

application = ASGIMiddleware(asgi_app)
