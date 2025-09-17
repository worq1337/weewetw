"""HTTP utility helpers for consistent API responses."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from flask import jsonify, g


def ensure_request_id(candidate: Optional[str] = None) -> str:
    """Return provided request id or generate a new one."""

    if candidate and isinstance(candidate, str) and candidate.strip():
        return candidate.strip()
    return uuid.uuid4().hex


def api_error(
    status_code: int,
    error: str,
    message: str,
    *,
    path: str = '',
    request_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
):
    """Build a JSON error response used across API handlers."""

    payload: Dict[str, Any] = {
        'status': 'error',
        'error': error,
        'message': message,
        'status_code': status_code,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
    }

    if path:
        payload['path'] = path

    request_id_value = request_id
    if not request_id_value:
        try:
            request_id_value = getattr(g, 'request_id', None)
        except RuntimeError:  # pragma: no cover - outside request context
            request_id_value = None

    if request_id_value:
        payload['request_id'] = request_id_value

    if details:
        payload['details'] = details

    response = jsonify(payload)
    response.status_code = status_code

    if request_id_value:
        response.headers['X-Request-ID'] = request_id_value

    return response
