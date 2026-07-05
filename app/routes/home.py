from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.db import query
from app.auth import get_session_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = get_session_user(request)

    featured = query(
        "SELECT id::text, title_te, title_en, type, thumbnail_url, play_count FROM content "
        "WHERE is_published=TRUE ORDER BY play_count DESC LIMIT 6"
    )
    recent = query(
        "SELECT id::text, title_te, title_en, type, thumbnail_url, created_at FROM content "
        "WHERE is_published=TRUE ORDER BY created_at DESC LIMIT 12"
    )
    categories = query(
        "SELECT id::text, name_te, name_en, slug, icon_url FROM categories ORDER BY display_order"
    )

    return templates.TemplateResponse("home.html", {
        "request": request, "user": user,
        "featured": featured, "recent": recent, "categories": categories,
    })


@router.get("/browse/{content_type}", response_class=HTMLResponse)
async def browse(request: Request, content_type: str):
    user = get_session_user(request)

    valid_types = {"music", "podcast", "audiobook", "story"}
    if content_type not in valid_types:
        content_type = "music"

    items = query(
        "SELECT id::text, title_te, title_en, type, thumbnail_url, artist_author, play_count FROM content "
        "WHERE is_published=TRUE AND type=%s ORDER BY created_at DESC",
        (content_type,)
    )

    return templates.TemplateResponse("browse.html", {
        "request": request, "user": user,
        "items": items, "content_type": content_type,
    })
