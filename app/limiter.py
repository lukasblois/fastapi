import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings

storage_uri = "memory://" if os.getenv("TESTING") == "True" else "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.limit_global],
    storage_uri=storage_uri
)
