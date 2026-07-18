from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.templates_env import templates

from app.db import query
from app.auth import get_session_user
from app.lang import lang_context

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = get_session_user(request)

    # Respect user's preferred content types for homepage
    preferred_types = []
    if user and user.get("preferred_types"):
        raw = user["preferred_types"]
        if isinstance(raw, str) and raw not in ("None", "", "{}"):
            preferred_types = [t.strip('{"} ') for t in raw.split(",") if t.strip('{"} ')]
        elif isinstance(raw, list):
            preferred_types = raw

    type_filter = "AND type=ANY(%s)" if preferred_types else ""
    type_params = [preferred_types] if preferred_types else []

    featured = query(
        f"SELECT id::text, title_te, title_en, type, thumbnail_url, play_count FROM content "
        f"WHERE is_published=TRUE {type_filter} ORDER BY play_count DESC LIMIT 6",
        type_params
    )
    recent = query(
        f"SELECT id::text, title_te, title_en, type, thumbnail_url, created_at FROM content "
        f"WHERE is_published=TRUE {type_filter} ORDER BY created_at DESC LIMIT 12",
        type_params
    )
    categories = query(
        "SELECT id::text, name_te, name_en, slug, icon_url FROM categories ORDER BY display_order"
    )

    return templates.TemplateResponse("home.html", {
        "request": request, "user": user,
        "featured": featured, "recent": recent, "categories": categories,
        **lang_context(request),
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
        **lang_context(request),
    })
