from typing import Optional
from fastapi import Request, HTTPException, status
from app.db import query_one, execute


def get_session_user(request: Request) -> Optional[dict]:
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
    row = execute(
        """
        INSERT INTO users (supabase_uid, name, email, avatar_url)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (supabase_uid) DO UPDATE
          SET name = EXCLUDED.name,
              email = EXCLUDED.email,
              avatar_url = EXCLUDED.avatar_url
        RETURNING *
        """,
        (supabase_uid, name, email, avatar_url),
    )
    # Convert uuid/date objects to strings so the session can be JSON-serialised
    serialized = {}
    for k, v in row.items():
        if k == "preferred_types":
            # Keep as list or empty list
            serialized[k] = list(v) if v else []
        elif v is None:
            serialized[k] = None
        else:
            serialized[k] = str(v)
    return serialized
