from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from app.templates_env import templates

from app.auth import require_login
from app.db import execute, query_one
from app.lang import lang_context

router = APIRouter()


@router.get("/preferences", response_class=HTMLResponse)
async def preferences_page(request: Request):
    user = require_login(request)
    return templates.TemplateResponse("preferences.html", {
        "request": request, "user": user, **lang_context(request),
    })


@router.post("/preferences")
async def save_preferences(request: Request):
    user = require_login(request)
    form = await request.form()

    preferred_lang = form.get("preferred_lang", "te")
    preferred_types = form.getlist("preferred_types")

    execute(
        "UPDATE users SET preferred_lang=%s, preferred_types=%s WHERE id=%s::uuid",
        (preferred_lang, preferred_types, user["id"])
    )

    # Refresh session
    updated = query_one("SELECT * FROM users WHERE id=%s::uuid", (user["id"],))
    request.session["user"] = {k: str(v) if v is not None else None for k, v in updated.items()}
    request.session["lang"] = preferred_lang

    return RedirectResponse("/", status_code=303)
