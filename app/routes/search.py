from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.templates_env import templates

from app.db import query, query_one
from app.auth import get_session_user
from app.lang import lang_context

router = APIRouter()


@router.get("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    q: str = "",
    author: str = "",
    tag: str = "",
    year_from: str = "",
    year_to: str = "",
    content_type: str = "",
    sort: str = "relevance",
):
    user = get_session_user(request)
    results = []
    has_filter = any([q.strip(), author.strip(), tag.strip(), year_from, year_to, content_type])

    if has_filter:
        conditions = ["is_published=TRUE"]
        params = []

        if q.strip():
            pattern = f"%{q.strip()}%"
            conditions.append(
                "(title_te ILIKE %s OR COALESCE(title_en,'') ILIKE %s OR COALESCE(artist_author,'') ILIKE %s)"
            )
            params += [pattern, pattern, pattern]

        if author.strip():
            conditions.append("COALESCE(artist_author,'') ILIKE %s")
            params.append(f"%{author.strip()}%")

        if tag.strip():
            conditions.append("%s = ANY(tags)")
            params.append(tag.strip().lower())

        if year_from.isdigit():
            conditions.append("release_year >= %s")
            params.append(int(year_from))

        if year_to.isdigit():
            conditions.append("release_year <= %s")
            params.append(int(year_to))

        if content_type:
            conditions.append("type = %s")
            params.append(content_type)

        sort_clause = {
            "relevance": "play_count DESC",
            "newest":    "created_at DESC",
            "oldest":    "release_year ASC NULLS LAST, created_at ASC",
            "az":        "title_en ASC",
        }.get(sort, "play_count DESC")

        where = " AND ".join(conditions)
        results = query(
            f"SELECT id::text, title_te, title_en, type, thumbnail_url, artist_author, "
            f"release_year, tags, play_count FROM content "
            f"WHERE {where} ORDER BY {sort_clause} LIMIT 100",
            params
        )

    # Get all distinct tags and authors for filter dropdowns
    all_tags = query(
        "SELECT DISTINCT unnest(tags) as tag FROM content WHERE is_published=TRUE AND tags != '{}' ORDER BY 1"
    )
    all_authors = query(
        "SELECT DISTINCT artist_author FROM content WHERE is_published=TRUE AND artist_author IS NOT NULL ORDER BY 1"
    )

    return templates.TemplateResponse("search.html", {
        "request": request, "user": user,
        "query": q, "author": author, "tag": tag,
        "year_from": year_from, "year_to": year_to,
        "content_type": content_type, "sort": sort,
        "results": results,
        "all_tags": [r["tag"] for r in all_tags],
        "all_authors": [r["artist_author"] for r in all_authors],
        **lang_context(request),
    })
