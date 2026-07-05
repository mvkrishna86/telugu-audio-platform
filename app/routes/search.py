from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.db import query
from app.auth import get_session_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = ""):
    user = get_session_user(request)
    results = []

    if q.strip():
        pattern = f"%{q.strip()}%"
        results = query(
            "SELECT id, title_te, title_en, type, thumbnail_url, artist_author FROM content "
            "WHERE is_published=TRUE AND (title_te ILIKE %s OR title_en ILIKE %s OR artist_author ILIKE %s) "
            "ORDER BY play_count DESC LIMIT 50",
            (pattern, pattern, pattern)
        )

    return templates.TemplateResponse("search.html", {
        "request": request, "user": user, "query": q, "results": results,
    })
