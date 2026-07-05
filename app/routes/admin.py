from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import get_db
from app.auth import require_admin
from app.storage import upload_file_to_s3, delete_s3_object
from app.config import MAX_UPLOAD_BYTES, ALLOWED_AUDIO_TYPES, ALLOWED_IMAGE_TYPES

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    user = require_admin(request)
    db = get_db()

    stats = {
        "total_content": db.table("content").select("id", count="exact").execute().count,
        "published": db.table("content").select("id", count="exact").eq("is_published", True).execute().count,
        "total_users": db.table("users").select("id", count="exact").execute().count,
    }

    recent_content = (
        db.table("content")
        .select("id, title_te, title_en, type, is_published, play_count, created_at")
        .order("created_at", desc=True)
        .limit(20)
        .execute()
        .data
    )

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "user": user, "stats": stats, "recent_content": recent_content},
    )


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    user = require_admin(request)
    db = get_db()
    categories = db.table("categories").select("id, name_te, name_en").order("display_order").execute().data
    return templates.TemplateResponse(
        "admin/upload.html",
        {"request": request, "user": user, "categories": categories},
    )


@router.post("/upload")
async def upload_content(
    request: Request,
    title_te: str = Form(...),
    title_en: str = Form(""),
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
    db = get_db()

    # Validate audio file
    audio_bytes = await audio_file.read()
    if len(audio_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Audio file exceeds 500 MB limit")
    if audio_file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid audio type: {audio_file.content_type}")

    # Upload thumbnail if provided
    thumbnail_url = ""
    if thumbnail and thumbnail.filename:
        thumb_bytes = await thumbnail.read()
        if thumbnail.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail="Invalid image type for thumbnail")
        thumb_key = upload_file_to_s3(thumb_bytes, thumbnail.content_type, "thumbnails")
        from app.config import CLOUDFRONT_DOMAIN
        thumbnail_url = f"{CLOUDFRONT_DOMAIN.rstrip('/')}/{thumb_key}"

    # Upload audio to S3
    audio_key = upload_file_to_s3(audio_bytes, audio_file.content_type, "audio")

    # Insert content row (or find existing by title + type for multi-part)
    content_row = (
        db.table("content")
        .insert(
            {
                "title_te": title_te,
                "title_en": title_en,
                "description_te": description_te,
                "description_en": description_en,
                "type": content_type,
                "category_id": category_id or None,
                "artist_author": artist_author,
                "release_year": int(release_year) if release_year.isdigit() else None,
                "thumbnail_url": thumbnail_url,
                "is_published": False,
                "uploaded_by": user["id"],
            }
        )
        .execute()
        .data[0]
    )

    # Insert audio_files row
    db.table("audio_files").insert(
        {
            "content_id": content_row["id"],
            "part_number": part_number,
            "title_te": part_title_te,
            "title_en": part_title_en,
            "s3_key": audio_key,
            "file_size_bytes": len(audio_bytes),
        }
    ).execute()

    return RedirectResponse(f"/admin/content/{content_row['id']}", status_code=303)


@router.get("/content/{content_id}", response_class=HTMLResponse)
async def edit_content_page(request: Request, content_id: str):
    user = require_admin(request)
    db = get_db()

    content = db.table("content").select("*").eq("id", content_id).single().execute().data
    if not content:
        raise HTTPException(status_code=404)

    audio_files = (
        db.table("audio_files")
        .select("id, part_number, title_te, title_en, duration_sec, file_size_bytes")
        .eq("content_id", content_id)
        .order("part_number")
        .execute()
        .data
    )
    categories = db.table("categories").select("id, name_te, name_en").order("display_order").execute().data

    return templates.TemplateResponse(
        "admin/edit_content.html",
        {
            "request": request,
            "user": user,
            "content": content,
            "audio_files": audio_files,
            "categories": categories,
        },
    )


@router.post("/content/{content_id}/publish")
async def toggle_publish(request: Request, content_id: str):
    user = require_admin(request)
    db = get_db()

    current = db.table("content").select("is_published").eq("id", content_id).single().execute().data
    if not current:
        raise HTTPException(status_code=404)

    db.table("content").update({"is_published": not current["is_published"]}).eq("id", content_id).execute()
    return RedirectResponse(f"/admin/content/{content_id}", status_code=303)


@router.post("/content/{content_id}/delete")
async def delete_content(request: Request, content_id: str):
    user = require_admin(request)
    db = get_db()

    audio_files = db.table("audio_files").select("s3_key").eq("content_id", content_id).execute().data
    for af in audio_files:
        try:
            delete_s3_object(af["s3_key"])
        except Exception:
            pass

    db.table("content").delete().eq("id", content_id).execute()
    return RedirectResponse("/admin", status_code=303)
