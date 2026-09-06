"""
API key authentication for the Printernizer Connect endpoints.

Only `/api/v1/connect/*` requires a key today. The rest of the API and the
frontend remain unauthenticated — see spec section 8.1.
"""
from typing import Any, Dict, Optional

import structlog
from fastapi import Depends, Header

from src.services.api_key_service import ApiKeyService
from src.utils.dependencies import get_api_key_service
from src.utils.errors import AuthenticationError

logger = structlog.get_logger()

_BEARER = "bearer "


async def require_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-Api-Key"),
    authorization: Optional[str] = Header(None),
    api_key_service: ApiKeyService = Depends(get_api_key_service),
) -> Dict[str, Any]:
    """
    Require a valid API key.

    Accepts `X-Api-Key: <key>` or `Authorization: Bearer <key>`; `X-Api-Key`
    takes precedence when both are present.

    Returns:
        The key record (id, name, created_at, last_used_at).

    Raises:
        AuthenticationError: no key supplied, or the key is unknown.
    """
    key = x_api_key
    if not key and authorization and authorization.lower().startswith(_BEARER):
        key = authorization[len(_BEARER):].strip()

    if not key:
        raise AuthenticationError(reason="API key required")

    record = await api_key_service.verify(key)
    if record is None:
        logger.warning("Rejected request with invalid API key")
        raise AuthenticationError(reason="Invalid API key")

    return record
