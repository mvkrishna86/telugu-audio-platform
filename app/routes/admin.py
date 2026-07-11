from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import query, query_one, execute
from app.auth import require_admin
from app.lang import lang_context
from app.storage import upload_file_to_s3, delete_s3_object
from app.config import MAX_UPLOAD_BYTES, ALLOWED_AUDIO_TYPES, ALLOWED_IMAGE_TYPES

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    user = require_admin(request)

    stats = {
        "total_content": (query_one("SELECT COUNT(*) as n FROM content") or {}).get("n", 0),
        "published":     (query_one("SELECT COUNT(*) as n FROM content WHERE is_published=TRUE") or {}).get("n", 0),
        "total_users":   (query_one("SELECT COUNT(*) as n FROM users") or {}).get("n", 0),
    }
    recent_content = query(
        "SELECT id::text, title_te, title_en, type, is_published, play_count, created_at "
        "FROM content ORDER BY created_at DESC LIMIT 20"
    )

    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request, "user": user,
        "stats": stats, "recent_content": recent_content,
        **lang_context(request),
    })


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    user = require_admin(request)
    categories = query("SELECT id::text, name_te, name_en FROM categories ORDER BY display_order")
    return templates.TemplateResponse("admin/upload.html", {
        "request": request, "user": user, "categories": categories,
        **lang_context(request),
    })


@router.post("/upload")
async def upload_content(
    request: Request,
    title_te: str = Form(...),
    title_en: str = Form(...),
    description_te: str = Form(""),
    description_en: str = Form(""),
    content_type: str = Form(...),
    category_id: str = Form(""),
    artist_author: str = Form(""),
    release_year: str = Form(""),
    part_number: int = Form(1),
    part_title_te: str = Form(""),
    part_title_en: str = Form(""),
    thumbnail: UploadFile = File(None),
    audio_file: UploadFile = File(...),
):
    user = require_admin(request)

    audio_bytes = await audio_file.read()
    if len(audio_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Audio file exceeds 500 MB limit")
    if audio_file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid audio type: {audio_file.content_type}")

    thumbnail_url = ""
    if thumbnail and thumbnail.filename:
        thumb_bytes = await thumbnail.read()
        if thumbnail.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail="Invalid image type for thumbnail")
        thumb_key = upload_file_to_s3(thumb_bytes, thumbnail.content_type, "thumbnails")
        from app.config import CLOUDFRONT_DOMAIN
        thumbnail_url = f"{CLOUDFRONT_DOMAIN.rstrip('/')}/{thumb_key}"

    audio_key = upload_file_to_s3(audio_bytes, audio_file.content_type, "audio")

    content_row = execute(
        """
        INSERT INTO content
          (title_te, title_en, description_te, description_en, type,
           category_id, artist_author, release_year, thumbnail_url, is_published, uploaded_by)
        VALUES (%s,%s,%s,%s,%s,%s::uuid,%s,%s,%s,FALSE,%s::uuid)
        RETURNING id::text
        """,
        (
            title_te, title_en, description_te, description_en, content_type,
            category_id or None, artist_author,
            int(release_year) if release_year.isdigit() else None,
            thumbnail_url, user["id"],
        )
    )

    execute(
        "INSERT INTO audio_files (content_id, part_number, title_te, title_en, s3_key, file_size_bytes) "
        "VALUES (%s::uuid,%s,%s,%s,%s,%s)",
        (content_row["id"], part_number, part_title_te, part_title_en, audio_key, len(audio_bytes))
    )

    return RedirectResponse(f"/admin/content/{content_row['id']}", status_code=303)


@router.get("/content/{content_id}", response_class=HTMLResponse)
async def edit_content_page(request: Request, content_id: str):
    user = require_admin(request)

    content = query_one("SELECT *, id::text as id FROM content WHERE id=%s::uuid", (content_id,))
    if not content:
        raise HTTPException(status_code=404)

    audio_files = query(
        "SELECT id::text, part_number, title_te, title_en, duration_sec, file_size_bytes "
        "FROM audio_files WHERE content_id=%s::uuid ORDER BY part_number",
        (content_id,)
    )
    categories = query("SELECT id::text, name_te, name_en FROM categories ORDER BY display_order")

    return templates.TemplateResponse("admin/edit_content.html", {
        "request": request, "user": user,
        "content": content, "audio_files": audio_files, "categories": categories,
    })


@router.post("/content/{content_id}/publish")
async def toggle_publish(request: Request, content_id: str):
    require_admin(request)
    current = query_one("SELECT is_published FROM content WHERE id=%s::uuid", (content_id,))
    if not current:
        raise HTTPException(status_code=404)
    execute("UPDATE content SET is_published=%s WHERE id=%s::uuid",
            (not current["is_published"], content_id))
    return RedirectResponse(f"/admin/content/{content_id}", status_code=303)


@router.post("/content/{content_id}/delete")
async def delete_content(request: Request, content_id: str):
    require_admin(request)

    audio_files = query("SELECT s3_key FROM audio_files WHERE content_id=%s::uuid", (content_id,))
    for af in audio_files:
        try:
            delete_s3_object(af["s3_key"])
        except Exception:
            pass

    execute("DELETE FROM content WHERE id=%s::uuid", (content_id,))
    return RedirectResponse("/admin", status_code=303)
