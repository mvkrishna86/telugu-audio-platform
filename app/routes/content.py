from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.db import get_db
from app.auth import get_session_user, require_login
from app.storage import get_signed_url

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/content/{content_id}", response_class=HTMLResponse)
async def content_detail(request: Request, content_id: str):
    db = get_db()
    user = get_session_user(request)

    row = (
        db.table("content")
        .select("*, categories(name_te, name_en, slug)")
        .eq("id", content_id)
        .eq("is_published", True)
        .single()
        .execute()
        .data
    )
    if not row:
        raise HTTPException(status_code=404, detail="Content not found")

    audio_files = (
        db.table("audio_files")
        .select("id, part_number, title_te, title_en, duration_sec")
        .eq("content_id", content_id)
        .order("part_number")
        .execute()
        .data
    )

    # Increment play count (best-effort, no failure on error)
    try:
        db.table("content").update({"play_count": row["play_count"] + 1}).eq("id", content_id).execute()
    except Exception:
        pass

    # Last position for logged-in user
    last_position = None
    if user and audio_files:
        pos = (
            db.table("listen_history")
            .select("audio_file_id, position_sec")
            .eq("user_id", user["id"])
            .in_("audio_file_id", [f["id"] for f in audio_files])
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
            .data
        )
        last_position = pos[0] if pos else None

    return templates.TemplateResponse(
        "content.html",
        {
            "request": request,
            "user": user,
            "content": row,
            "audio_files": audio_files,
            "last_position": last_position,
        },
    )


@router.post("/api/play/{audio_file_id}", response_class=JSONResponse)
async def get_play_url(request: Request, audio_file_id: str):
    user = require_login(request)
    db = get_db()

    row = db.table("audio_files").select("s3_key").eq("id", audio_file_id).single().execute().data
    if not row:
        raise HTTPException(status_code=404, detail="Audio file not found")

    signed_url = get_signed_url(row["s3_key"])
    return {"url": signed_url}


@router.post("/api/position", response_class=JSONResponse)
async def save_position(request: Request):
    user = require_login(request)
    body = await request.json()
    audio_file_id = body.get("audio_file_id")
    position_sec = int(body.get("position_sec", 0))

    if not audio_file_id:
        raise HTTPException(status_code=400, detail="audio_file_id required")

    db = get_db()
    db.table("listen_history").upsert(
        {
            "user_id": user["id"],
            "audio_file_id": audio_file_id,
            "position_sec": position_sec,
        },
        on_conflict="user_id,audio_file_id",
    ).execute()

    return {"ok": True}
