from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.db import get_db
from app.auth import get_session_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = ""):
    db = get_db()
    user = get_session_user(request)
    results = []

    if q.strip():
        # ilike works with Telugu unicode in PostgreSQL
        pattern = f"%{q.strip()}%"
        results = (
            db.table("content")
            .select("id, title_te, title_en, type, thumbnail_url, artist_author")
            .eq("is_published", True)
            .or_(f"title_te.ilike.{pattern},title_en.ilike.{pattern},artist_author.ilike.{pattern}")
            .order("play_count", desc=True)
            .limit(50)
            .execute()
            .data
        )

    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "user": user,
            "query": q,
            "results": results,
        },
    )
