import logging
from fastapi import Header, HTTPException
from app.utils.settings import get_settings

logger = logging.getLogger(__name__)


def verify_shared_key(x_shared_key: str | None = Header(default=None)) -> str:
    settings = get_settings()
    if x_shared_key != settings.app_shared_key:
        logger.warning(
            "Unauthorized request to API: x_shared_key=%r expected=%r",
            x_shared_key,
            settings.app_shared_key,
        )
        raise HTTPException(status_code=401, detail="UNAUTHORIZED")
    return x_shared_key or ""
