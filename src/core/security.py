from fastapi import Header, HTTPException
from typing import Optional
import logging

from .config import settings

logger = logging.getLogger(__name__)


def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key from header"""
    if x_api_key is None or x_api_key != settings.API_KEY:
        logger.warning(f"Invalid API key attempt: {x_api_key}")
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key
