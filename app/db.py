from typing import Optional
from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_SERVICE_KEY

# Service-role client — used only server-side, never exposed to browser
_client: Optional[Client] = None


def get_db() -> Client:
    global _client
    if _client is None:
        # supabase-py 2.x accepts both legacy JWT keys and new sb_secret_ format
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client
