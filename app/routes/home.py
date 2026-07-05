from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.db import get_db
from app.auth import get_session_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    db = get_db()
    user = get_session_user(request)

    featured = (
        db.table("content")
        .select("id, title_te, title_en, type, thumbnail_url, play_count")
        .eq("is_published", True)
        .order("play_count", desc=True)
        .limit(6)
        .execute()
        .data
    )

    recent = (
        db.table("content")
        .select("id, title_te, title_en, type, thumbnail_url, created_at")
        .eq("is_published", True)
        .order("created_at", desc=True)
        .limit(12)
        .execute()
        .data
    )

    categories = (
        db.table("categories")
        .select("id, name_te, name_en, slug, icon_url")
        .order("display_order")
        .execute()
        .data
    )

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "user": user,
            "featured": featured,
            "recent": recent,
            "categories": categories,
        },
    )


@router.get("/browse/{content_type}", response_class=HTMLResponse)
async def browse(request: Request, content_type: str):
    db = get_db()
    user = get_session_user(request)

    valid_types = {"music", "podcast", "audiobook", "story"}
    if content_type not in valid_types:
        content_type = "music"

    items = (
        db.table("content")
        .select("id, title_te, title_en, type, thumbnail_url, artist_author, play_count")
        .eq("is_published", True)
        .eq("type", content_type)
        .order("created_at", desc=True)
        .execute()
        .data
    )

    return templates.TemplateResponse(
        "browse.html",
        {
            "request": request,
            "user": user,
            "items": items,
            "content_type": content_type,
        },
    )
