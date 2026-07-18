from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from app.templates_env import templates

from app.db import query, query_one, execute
from app.auth import require_admin
from app.lang import lang_context

router = APIRouter(prefix="/admin/users")

PAGE_SIZE = 20


@router.get("", response_class=HTMLResponse)
async def users_page(request: Request, q: str = "", role: str = "", page: int = 1):
    user = require_admin(request)

    conditions = []
    params = []

    if q.strip():
        conditions.append("(COALESCE(name,'') ILIKE %s OR COALESCE(email,'') ILIKE %s)")
        params += [f"%{q.strip()}%", f"%{q.strip()}%"]

    if role:
        conditions.append("role = %s")
        params.append(role)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    total = (query_one(f"SELECT COUNT(*) as n FROM users {where}", params) or {}).get("n", 0)
    total_pages = max(1, (int(total) + PAGE_SIZE - 1) // PAGE_SIZE)
    offset = (page - 1) * PAGE_SIZE

    users = query(
        f"SELECT id::text, name, email, phone, role, preferred_lang, avatar_url, created_at::text "
        f"FROM users {where} ORDER BY created_at DESC LIMIT %s OFFSET %s",
        params + [PAGE_SIZE, offset]
    )

    stats = {
        "total":  (query_one("SELECT COUNT(*) as n FROM users") or {}).get("n", 0),
        "admins": (query_one("SELECT COUNT(*) as n FROM users WHERE role IN ('admin','superadmin')") or {}).get("n", 0),
        "active": (query_one("SELECT COUNT(DISTINCT user_id) as n FROM listen_history") or {}).get("n", 0),
    }

    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "current_user": user,
        "user": user,
        "users": users,
        "stats": stats,
        "search_q": q,
        "role_filter": role,
        "page": page,
        "total_pages": total_pages,
        **lang_context(request),
    })


@router.post("/{user_id}/role")
async def update_role(request: Request, user_id: str, role: str = Form(...)):
    current_user = require_admin(request)

    allowed_roles = ["listener", "admin"]
    if current_user["role"] == "superadmin":
        allowed_roles.append("superadmin")

    if role not in allowed_roles:
        raise HTTPException(status_code=400, detail="Invalid role")

    # Prevent changing own role
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    # Only superadmin can create/modify other superadmins
    target = query_one("SELECT role FROM users WHERE id=%s::uuid", (user_id,))
    if not target:
        raise HTTPException(status_code=404)
    if target["role"] == "superadmin" and current_user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Only superadmin can modify another superadmin")

    execute("UPDATE users SET role=%s WHERE id=%s::uuid", (role, user_id))
    return RedirectResponse("/admin/users", status_code=303)
