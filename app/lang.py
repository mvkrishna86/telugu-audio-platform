from fastapi import Request


def get_lang(request: Request) -> str:
    """Return current language from session, defaulting to Telugu."""
    return request.session.get("lang", "te")


def lang_context(request: Request) -> dict:
    return {"lang": get_lang(request)}
