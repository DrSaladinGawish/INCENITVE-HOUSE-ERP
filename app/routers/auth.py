import json
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.models import UserSession
from app.schemas import LoginRequest, TokenResponse

router = APIRouter(tags=["auth"])
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.environ.get("JWT_SECRET", "incentivehouse-dev-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.environ.get("JWT_EXPIRE_HOURS", "8"))

DEFAULT_USERS_RAW = os.environ.get(
    "AUTH_USERS_JSON",
    json.dumps({
        "admin": {"password": "admin", "role": "admin", "display": "Administrator"},
        "accountant": {"password": "accountant", "role": "accountant", "display": "Accountant"},
        "event_manager": {"password": "events", "role": "event_manager", "display": "Event Manager"},
        "viewer": {"password": "viewer", "role": "viewer", "display": "Viewer"},
    }),
)

try:
    AUTH_USERS = json.loads(DEFAULT_USERS_RAW)
except (json.JSONDecodeError, TypeError):
    AUTH_USERS = {}


def verify_password(plain: str, stored: str) -> bool:
    try:
        return pwd_context.verify(plain, stored)
    except (ValueError, TypeError):
        return plain == stored


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(username: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_user(username: str) -> Optional[dict]:
    user = AUTH_USERS.get(username)
    if not user:
        return None
    return {"username": username, "password": user["password"], "role": user["role"], "display": user.get("display", username)}


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = get_user(req.username)
    if not user or not verify_password(req.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user["username"], user["role"])
    session = UserSession(username=user["username"], token=token, role=user["role"], expires_at=datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    db.add(session)
    await db.commit()
    return TokenResponse(access_token=token, role=user["role"], username=user["username"])


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if not username or not role:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return {"username": username, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_role(*roles: str):
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in roles:
            raise HTTPException(status_code=403, detail=f"Requires one of: {', '.join(roles)}")
        return current_user
    return role_checker


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
