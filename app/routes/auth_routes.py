from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import sync_user_to_db
from app.config import SUPABASE_URL, SUPABASE_ANON_KEY, APP_BASE_URL

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/")
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "supabase_url": SUPABASE_URL,
            "supabase_anon_key": SUPABASE_ANON_KEY,
            "app_base_url": APP_BASE_URL,
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
