from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.db import query, query_one, execute
from app.auth import require_login

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/library", response_class=HTMLResponse)
async def library(request: Request):
    user = require_login(request)

    bookmarks = query(
        "SELECT c.id::text, c.title_te, c.title_en, c.type, c.thumbnail_url, c.artist_author "
        "FROM bookmarks b JOIN content c ON c.id=b.content_id "
        "WHERE b.user_id=%s::uuid ORDER BY b.created_at DESC",
        (user["id"],)
    )

    history = query(
        "SELECT lh.position_sec, lh.updated_at, "
        "af.id::text as af_id, af.title_te as af_title_te, af.part_number, "
        "c.id::text as c_id, c.title_te, c.thumbnail_url "
        "FROM listen_history lh "
        "JOIN audio_files af ON af.id=lh.audio_file_id "
        "JOIN content c ON c.id=af.content_id "
        "WHERE lh.user_id=%s::uuid ORDER BY lh.updated_at DESC LIMIT 20",
        (user["id"],)
    )

    return templates.TemplateResponse("library.html", {
        "request": request, "user": user,
        "bookmarks": bookmarks, "history": history,
    })


@router.post("/library/bookmark/{content_id}", response_class=JSONResponse)
async def toggle_bookmark(request: Request, content_id: str):
    user = require_login(request)

    existing = query_one(
        "SELECT 1 FROM bookmarks WHERE user_id=%s::uuid AND content_id=%s::uuid",
        (user["id"], content_id)
    )

    if existing:
        execute("DELETE FROM bookmarks WHERE user_id=%s::uuid AND content_id=%s::uuid",
                (user["id"], content_id))
        return {"bookmarked": False}
    else:
        execute("INSERT INTO bookmarks (user_id, content_id) VALUES (%s::uuid, %s::uuid)",
                (user["id"], content_id))
        return {"bookmarked": True}
