from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.core.surgery_deps import get_current_user
from app.core.cookie_auth import set_auth_cookie, clear_auth_cookie

router = APIRouter(prefix="/auth", tags=["Auth"])

_BASE = Path(__file__).resolve().parent.parent.parent.parent  # routers/ → project root
templates = Jinja2Templates(directory=str(_BASE / "templates"))


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "user"
    department: str = ""


@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})


@router.post("/login")
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    set_auth_cookie(response, token)
    return {"access_token": token, "token_type": "bearer", "user": {"id": str(user.id), "email": user.email, "full_name": user.full_name, "role": user.role}}


@router.post("/register")
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=body.email,
        full_name=body.full_name,
        role=body.role,
        department=body.department,
        password_hash=hash_password(body.password),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    return {"message": "User created", "user": {"id": str(user.id), "email": user.email}}


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user


@router.post("/logout")
async def logout(response: Response):
    clear_auth_cookie(response)
    return {"message": "Logged out successfully"}
