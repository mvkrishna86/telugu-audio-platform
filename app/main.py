from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from starlette.middleware.sessions import SessionMiddleware

import base64, os
from app.config import APP_SECRET_KEY
from app.routes import home, content, search, library, auth_routes, admin, preferences

# Write CloudFront private key from base64 env var if present
_cf_key_b64 = os.environ.get("CLOUDFRONT_PRIVATE_KEY_B64", "")
if _cf_key_b64:
    with open("cloudfront_private_key.pem", "wb") as _f:
        _f.write(base64.b64decode(_cf_key_b64))

app = FastAPI(title="Sraavani", docs_url=None, redoc_url=None)

app.add_middleware(SessionMiddleware, secret_key=APP_SECRET_KEY, max_age=60 * 60 * 24 * 30)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth_routes.router)
app.include_router(home.router)
app.include_router(content.router)
app.include_router(search.router)
app.include_router(library.router)
app.include_router(admin.router)
app.include_router(preferences.router)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("app/static/icons/icon-192.png")


@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc):
    from fastapi.responses import RedirectResponse
    return RedirectResponse(f"/login?next={request.url.path}")


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
