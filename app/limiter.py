import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.limit_global],
    storage_uri="memory://",
    enabled=True
)
