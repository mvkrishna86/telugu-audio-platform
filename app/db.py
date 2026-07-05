import urllib.parse
import psycopg2
import psycopg2.extras
from typing import Optional
from app.config import DATABASE_URL

_conn: Optional[psycopg2.extensions.connection] = None


def get_conn():
    global _conn
    if _conn is None or _conn.closed:
        url = urllib.parse.urlparse(DATABASE_URL)
        _conn = psycopg2.connect(
            host=url.hostname,
            port=url.port or 5432,
            dbname=url.path.lstrip("/"),
            user=url.username,
            password=urllib.parse.unquote(url.password or ""),
            sslmode="require",
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
        _conn.autocommit = True
    return _conn


def query(sql: str, params=None) -> list:
    with get_conn().cursor() as cur:
        cur.execute(sql, params or ())
        return [dict(r) for r in cur.fetchall()]


def query_one(sql: str, params=None) -> Optional[dict]:
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params=None) -> Optional[dict]:
    with get_conn().cursor() as cur:
        cur.execute(sql, params or ())
        try:
            row = cur.fetchone()
            return dict(row) if row else None
        except psycopg2.ProgrammingError:
            return None
