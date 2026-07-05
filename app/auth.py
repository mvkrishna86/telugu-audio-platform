from typing import Optional
from fastapi import Request, HTTPException, status
from app.db import get_db


def get_session_user(request: Request) -> Optional[dict]:
    """Return the user dict stored in the session, or None if not logged in."""
    return request.session.get("user")


def require_login(request: Request) -> dict:
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    return user


def require_admin(request: Request) -> dict:
    user = require_login(request)
    if user.get("role") not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def require_superadmin(request: Request) -> dict:
    user = require_login(request)
    if user.get("role") != "superadmin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super-admin access required")
    return user


def sync_user_to_db(supabase_uid: str, name: str, email: str, avatar_url: str) -> dict:
    """Upsert user into our users table and return the full user row."""
    db = get_db()
    result = (
        db.table("users")
        .upsert(
            {
                "supabase_uid": supabase_uid,
                "name": name,
                "email": email,
                "avatar_url": avatar_url,
            },
            on_conflict="supabase_uid",
        )
        .execute()
    )
    return result.data[0]
