from functools import lru_cache

from app.core.config import SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL, USE_SUPABASE


@lru_cache(maxsize=1)
def get_supabase_client():
    if not USE_SUPABASE:
        return None
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None

    try:
        from supabase import create_client
    except ImportError:
        return None

    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
