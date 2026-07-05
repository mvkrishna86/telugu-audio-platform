from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.db import query, query_one, execute
from app.auth import get_session_user, require_login
from app.storage import get_signed_url

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/content/{content_id}", response_class=HTMLResponse)
async def content_detail(request: Request, content_id: str):
    user = get_session_user(request)

    row = query_one(
        "SELECT c.*, cat.name_te as cat_name_te, cat.name_en as cat_name_en, cat.slug as cat_slug "
        "FROM content c LEFT JOIN categories cat ON cat.id=c.category_id "
        "WHERE c.id=%s AND c.is_published=TRUE",
        (content_id,)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Content not found")

    audio_files = query(
        "SELECT id, part_number, title_te, title_en, duration_sec FROM audio_files "
        "WHERE content_id=%s ORDER BY part_number",
        (content_id,)
    )

    # Increment play count best-effort
    try:
        execute("UPDATE content SET play_count=play_count+1 WHERE id=%s", (content_id,))
    except Exception:
        pass

    last_position = None
    if user and audio_files:
        af_ids = tuple(f["id"] for f in audio_files)
        last_position = query_one(
            "SELECT audio_file_id, position_sec FROM listen_history "
            "WHERE user_id=%s AND audio_file_id=ANY(%s) ORDER BY updated_at DESC LIMIT 1",
            (user["id"], list(af_ids))
        )

    return templates.TemplateResponse("content.html", {
        "request": request, "user": user,
        "content": row, "audio_files": audio_files, "last_position": last_position,
    })


@router.post("/api/play/{audio_file_id}", response_class=JSONResponse)
async def get_play_url(request: Request, audio_file_id: str):
    require_login(request)

    row = query_one("SELECT s3_key FROM audio_files WHERE id=%s", (audio_file_id,))
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

    execute(
        """
        INSERT INTO listen_history (user_id, audio_file_id, position_sec, updated_at)
        VALUES (%s, %s, %s, now())
        ON CONFLICT (user_id, audio_file_id) DO UPDATE
          SET position_sec=EXCLUDED.position_sec, updated_at=now()
        """,
        (user["id"], audio_file_id, position_sec)
    )
    return {"ok": True}
