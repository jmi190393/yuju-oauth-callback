"""Adaptador WSGI para PythonAnywhere.

Flask ES una app WSGI nativa, así que se expone directamente — sin puentes
ASGI. En el tab Web, el archivo WSGI debe hacer: from wsgi import application
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app as application  # noqa: E402
