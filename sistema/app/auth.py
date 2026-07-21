"""Login con sesión firmada en cookie. Dos usuarios (pareja), sin dependencias externas."""
import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .db import get_db
from .models import User

SECRET = os.environ.get("FINANZAS_SECRET", "")
_SECRET_FILE = os.path.join(os.path.dirname(__file__), "..", ".secret")
if not SECRET:
    if os.path.exists(_SECRET_FILE):
        SECRET = open(_SECRET_FILE).read().strip()
    else:
        SECRET = base64.urlsafe_b64encode(os.urandom(32)).decode()
        with open(_SECRET_FILE, "w") as f:
            f.write(SECRET)

SESSION_DAYS = 30
COOKIE = "finanzas_session"


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return base64.b64encode(salt).decode() + "$" + base64.b64encode(dk).decode()


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


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE, "")
    uid = read_token(token)
    if uid is None:
        raise HTTPException(status_code=401, detail="Sesión inválida — vuelve a iniciar sesión")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user
