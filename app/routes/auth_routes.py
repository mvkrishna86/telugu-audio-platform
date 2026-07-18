from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from app.templates_env import templates

from app.auth import sync_user_to_db
from app.config import SUPABASE_URL, SUPABASE_ANON_KEY, APP_BASE_URL

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/")
    from app.lang import lang_context
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "supabase_url": SUPABASE_URL,
            "supabase_anon_key": SUPABASE_ANON_KEY,
            "app_base_url": APP_BASE_URL,
            **lang_context(request),
        },
    )


@router.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback(request: Request):
    return templates.TemplateResponse("auth_callback.html", {
        "request": request,
        "supabase_url": SUPABASE_URL,
        "supabase_anon_key": SUPABASE_ANON_KEY,
    })


@router.post("/auth/session")
async def create_session(request: Request):
    """Receive user info from the browser after Supabase auth and store in session."""
    body = await request.json()
    supabase_uid = body.get("id")
    name = body.get("name", "")
    email = body.get("email", "")
    avatar_url = body.get("avatar_url", "")

    if not supabase_uid:
        raise HTTPException(status_code=400, detail="Missing user id")

    user_row = sync_user_to_db(supabase_uid, name, email, avatar_url)
    request.session["user"] = user_row
    return {"ok": True, "role": user_row.get("role")}


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")


@router.get("/lang/{code}")
async def set_language(request: Request, code: str):
    """Toggle UI language and redirect back."""
    if code in ("te", "en"):
        request.session["lang"] = code
        # Persist to DB if logged in
        from app.db import execute
        user = request.session.get("user")
        if user:
            execute(
                "UPDATE users SET preferred_lang=%s WHERE id=%s::uuid",
                (code, user["id"])
            )
            request.session["user"] = {**user, "preferred_lang": code}
    referer = request.headers.get("referer", "/")
    return RedirectResponse(referer)
