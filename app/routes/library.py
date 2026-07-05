from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.db import get_db
from app.auth import require_login

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/library", response_class=HTMLResponse)
async def library(request: Request):
    user = require_login(request)
    db = get_db()

    bookmarks = (
        db.table("bookmarks")
        .select("content(id, title_te, title_en, type, thumbnail_url, artist_author)")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .execute()
        .data
    )

    history = (
        db.table("listen_history")
        .select("position_sec, updated_at, audio_files(id, title_te, title_en, content_id, part_number, content(id, title_te, title_en, thumbnail_url))")
        .eq("user_id", user["id"])
        .order("updated_at", desc=True)
        .limit(20)
        .execute()
        .data
    )

    return templates.TemplateResponse(
        "library.html",
        {
            "request": request,
            "user": user,
            "bookmarks": bookmarks,
            "history": history,
        },
    )


@router.post("/library/bookmark/{content_id}", response_class=JSONResponse)
async def toggle_bookmark(request: Request, content_id: str):
    user = require_login(request)
    db = get_db()

    existing = (
        db.table("bookmarks")
        .select("user_id")
        .eq("user_id", user["id"])
        .eq("content_id", content_id)
        .execute()
        .data
    )

    if existing:
        db.table("bookmarks").delete().eq("user_id", user["id"]).eq("content_id", content_id).execute()
        return {"bookmarked": False}
    else:
        db.table("bookmarks").insert({"user_id": user["id"], "content_id": content_id}).execute()
        return {"bookmarked": True}
