"""httpOnly session cookie helpers for EventCore."""
from fastapi import Request, Response
from app.core.security import ACCESS_TOKEN_EXPIRE_MINUTES

COOKIE_NAME = "eventcore_session"


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")


def get_token_from_cookie(request: Request) -> str | None:
    return request.cookies.get(COOKIE_NAME)
