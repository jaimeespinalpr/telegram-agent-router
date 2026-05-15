from fastapi import HTTPException, Request, status

from app.settings import Settings

SESSION_KEY = "authenticated"


def is_authenticated(request: Request) -> bool:
    return bool(request.session.get(SESSION_KEY))


def require_auth(request: Request) -> None:
    if not is_authenticated(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def login(request: Request, settings: Settings, username: str, password: str) -> bool:
    if username == settings.admin_username and password == settings.admin_password:
        request.session[SESSION_KEY] = True
        return True
    return False


def logout(request: Request) -> None:
    request.session.clear()

