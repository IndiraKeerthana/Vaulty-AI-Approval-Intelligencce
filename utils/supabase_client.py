import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("VAULTY.SupabaseClient")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

_supabase_client = None
_client_initialized = False

def get_supabase_client():
    """
    Returns an initialized Supabase Client if credentials are present and valid,
    otherwise returns None.
    """
    global _supabase_client, _client_initialized

    if _client_initialized:
        return _supabase_client

    url = SUPABASE_URL
    key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY

    if not url or not key:
        logger.info("Supabase URL or Key not set. Operating in Local Files Fallback mode.")
        _client_initialized = True
        _supabase_client = None
        return None

    try:
        from supabase import create_client
        _supabase_client = create_client(url, key)
        logger.info("Successfully connected to Supabase.")
    except Exception as e:
        logger.warning(f"Failed to connect to Supabase: {e}. Operating in Local Files Fallback mode.")
        _supabase_client = None

    _client_initialized = True
    return _supabase_client

def is_supabase_available() -> bool:
    """
    Checks if Supabase client is connected and reachable.
    """
    client = get_supabase_client()
    if not client:
        return False
    try:
        # Simple health check ping against cases table
        client.table("cases").select("case_id").limit(1).execute()
        return True
    except Exception:
        return False
