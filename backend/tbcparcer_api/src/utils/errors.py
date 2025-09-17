"""Custom exceptions used for API-level error handling."""

from __future__ import annotations

from typing import Any, Dict, Optional


class APIError(Exception):
    """Error raised by view functions to trigger JSON error responses."""

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error = error or 'API Error'
        self.details = details

