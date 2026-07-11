from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List

from app.db import query, query_one, execute
from app.auth import require_admin
from app.storage import upload_file_to_s3, delete_s3_object
from app.config import MAX_UPLOAD_BYTES, ALLOWED_AUDIO_TYPES, ALLOWED_IMAGE_TYPES
from app.lang import lang_context

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
async def upload_content(request: Request):
    """Handle multi-part form with dynamic parts[0..N] fields."""
    user = require_admin(request)

    form = await request.form()

    title_te     = form.get("title_te", "").strip()
    title_en     = form.get("title_en", "").strip()
    content_type = form.get("content_type", "music")
    category_id  = form.get("category_id", "") or None
    artist_author= form.get("artist_author", "").strip()
    release_year = form.get("release_year", "").strip()
    description_te = form.get("description_te", "").strip()
    description_en = form.get("description_en", "").strip()
    thumbnail    = form.get("thumbnail")

    if not title_te or not title_en:
        raise HTTPException(status_code=400, detail="Both Telugu and English titles are required")

    # Upload thumbnail
    thumbnail_url = ""
    if thumbnail and hasattr(thumbnail, "filename") and thumbnail.filename:
        thumb_bytes = await thumbnail.read()
        if thumbnail.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail="Invalid image type")
        thumb_key = upload_file_to_s3(thumb_bytes, thumbnail.content_type, "thumbnails")
        from app.config import CLOUDFRONT_DOMAIN
        thumbnail_url = f"{CLOUDFRONT_DOMAIN.rstrip('/')}/{thumb_key}"

    # Create content row
    content_row = execute(
        """INSERT INTO content
           (title_te, title_en, description_te, description_en, type,
            category_id, artist_author, release_year, thumbnail_url, is_published, uploaded_by)
           VALUES (%s,%s,%s,%s,%s,%s::uuid,%s,%s,%s,FALSE,%s::uuid)
           RETURNING id::text""",
        (title_te, title_en, description_te, description_en, content_type,
         category_id, artist_author,
         int(release_year) if release_year.isdigit() else None,
         thumbnail_url, user["id"])
    )
    content_id = content_row["id"]

    # Upload all parts
    idx = 0
    while True:
        audio_file = form.get(f"parts[{idx}][audio]")
        if audio_file is None:
            break
        if not hasattr(audio_file, "filename") or not audio_file.filename:
            idx += 1
            continue

        audio_bytes = await audio_file.read()
        if len(audio_bytes) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=400, detail=f"Part {idx+1} exceeds 500 MB")
        if audio_file.content_type not in ALLOWED_AUDIO_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid audio type for part {idx+1}")

        audio_key = upload_file_to_s3(audio_bytes, audio_file.content_type, "audio")
        part_title_te = form.get(f"parts[{idx}][title_te]", "").strip()
        part_title_en = form.get(f"parts[{idx}][title_en]", "").strip()

        execute(
            "INSERT INTO audio_files (content_id, part_number, title_te, title_en, s3_key, file_size_bytes) "
            "VALUES (%s::uuid,%s,%s,%s,%s,%s)",
            (content_id, idx + 1, part_title_te or None, part_title_en or None,
             audio_key, len(audio_bytes))
        )
        idx += 1

    return RedirectResponse(f"/admin/content/{content_id}", status_code=303)


@router.post("/content/{content_id}/add-parts")
async def add_parts(request: Request, content_id: str):
    """Add more audio parts to existing content."""
    user = require_admin(request)

    # Get current max part number
    existing = query_one(
        "SELECT COALESCE(MAX(part_number), 0) as max_part FROM audio_files WHERE content_id=%s::uuid",
        (content_id,)
    )
    next_part = (existing["max_part"] or 0) + 1

    form = await request.form()
    idx = 0
    while True:
        audio_file = form.get(f"parts[{idx}][audio]")
        if audio_file is None:
            break
        if not hasattr(audio_file, "filename") or not audio_file.filename:
            idx += 1
            continue

        audio_bytes = await audio_file.read()
        if len(audio_bytes) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=400, detail=f"Part exceeds 500 MB")
        if audio_file.content_type not in ALLOWED_AUDIO_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid audio type")

        audio_key = upload_file_to_s3(audio_bytes, audio_file.content_type, "audio")
        part_title_te = form.get(f"parts[{idx}][title_te]", "").strip()
        part_title_en = form.get(f"parts[{idx}][title_en]", "").strip()

        execute(
            "INSERT INTO audio_files (content_id, part_number, title_te, title_en, s3_key, file_size_bytes) "
            "VALUES (%s::uuid,%s,%s,%s,%s,%s)",
            (content_id, next_part + idx, part_title_te or None, part_title_en or None,
             audio_key, len(audio_bytes))
        )
        idx += 1

    return RedirectResponse(f"/admin/content/{content_id}", status_code=303)


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
        **lang_context(request),
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


@router.post("/audiofile/{audio_file_id}/delete")
async def delete_audio_file(request: Request, audio_file_id: str):
    """Delete a single audio part."""
    user = require_admin(request)
    af = query_one(
        "SELECT af.s3_key, af.content_id::text FROM audio_files af WHERE af.id=%s::uuid",
        (audio_file_id,)
    )
    if not af:
        raise HTTPException(status_code=404)
    try:
        delete_s3_object(af["s3_key"])
    except Exception:
        pass
    execute("DELETE FROM audio_files WHERE id=%s::uuid", (audio_file_id,))
    # Renumber remaining parts
    remaining = query(
        "SELECT id::text FROM audio_files WHERE content_id=%s::uuid ORDER BY part_number",
        (af["content_id"],)
    )
    for i, row in enumerate(remaining, start=1):
        execute("UPDATE audio_files SET part_number=%s WHERE id=%s::uuid", (i, row["id"]))
    return RedirectResponse(f"/admin/content/{af['content_id']}", status_code=303)
