from fastapi.templating import Jinja2Templates
from app.storage import thumb_url

# Single shared Jinja2 environment used by all routes
templates = Jinja2Templates(directory="app/templates")
templates.env.filters["thumb_url"] = thumb_url
