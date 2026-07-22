"""Login con sesión firmada en cookie. Dos usuarios (pareja), sin dependencias externas.

Integración con Flask: current_user_id lee la cookie; login_required protege rutas.
"""
import base64
import functools
import hashlib
import hmac
import json
import os
import time

from flask import g, jsonify, request

from .models import User

def _load_secret() -> str:
    """Clave para firmar la sesión. Prioridad: variable de entorno
    FINANZAS_SECRET (recomendado en producción y obligatoria con varios workers)
    → archivo .secret persistente → valor efímero (último recurso: si el disco es
    de solo lectura, la sesión no sobrevive al reinicio)."""
    env = os.environ.get("FINANZAS_SECRET", "")
    if env:
        return env
    try:
        with open(_SECRET_FILE) as f:
            return f.read().strip()
    except OSError:
        pass
    secret = base64.urlsafe_b64encode(os.urandom(32)).decode()
    try:
        with open(_SECRET_FILE, "w") as f:
            f.write(secret)
    except OSError:
        pass
    return secret


_SECRET_FILE = os.path.join(os.path.dirname(__file__), "..", ".secret")
SECRET = _load_secret()
SESSION_DAYS = 30
COOKIE = "finanzas_session"


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return base64.b64encode(salt).decode() + "$" + base64.b64encode(dk).decode()


# Hash señuelo: se verifica cuando el usuario no existe, para que un login con
# usuario inexistente tarde lo mismo que uno con contraseña incorrecta (evita
# enumeración de usuarios por tiempo de respuesta).
DUMMY_HASH = hash_password("timing-equalizer")


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_b64, _ = stored.split("$")
        return hmac.compare_digest(hash_password(password, base64.b64decode(salt_b64)), stored)
    except Exception:
        return False


def make_token(user_id: int) -> str:
    payload = json.dumps({"uid": user_id, "exp": int(time.time()) + SESSION_DAYS * 86400})
    body = base64.urlsafe_b64encode(payload.encode()).decode()
    sig = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def read_token(token: str) -> int | None:
    try:
        body, sig = token.rsplit(".", 1)
        expect = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expect):
            return None
        payload = json.loads(base64.urlsafe_b64decode(body))
        if payload["exp"] < time.time():
            return None
        return payload["uid"]
    except Exception:
        return None


def current_user_id() -> int | None:
    return read_token(request.cookies.get(COOKIE, ""))


def login_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        uid = current_user_id()
        user = g.db.get(User, uid) if uid is not None else None
        if user is None:
            return jsonify({"detail": "Sesión inválida — vuelve a iniciar sesión"}), 401
        g.user = user
        return fn(*args, **kwargs)
    return wrapper
