"""Utility helpers for FastAPI endpoints."""

from __future__ import annotations

from typing import Dict, Tuple

from fastapi import HTTPException

from server.app.schemas.common import BaseResponse, success_response as _success_response


def success_response(data=None, message: str = "ok") -> BaseResponse:
    """Expose a shared helper for building success responses."""

    return _success_response(data=data, message=message)


def handle_service_error(
    exc: Exception,
    mapping: Dict[str, Tuple[int, str]],
    *,
    default_message: str,
    default_status: int = 400,
) -> None:
    """Transform raw service exceptions into HTTP errors using a shared mapping.

    Args:
        exc: The raised exception.
        mapping: Mapping of lowercase keywords to ``(status_code, detail)`` tuples.
        default_message: Message appended when no mapping matches.
        default_status: HTTP status code used when no mapping matches.

    Raises:
        HTTPException: With mapped or default status/detail.
    """

    if isinstance(exc, HTTPException):
        raise exc

    error_text = str(exc) if exc else ""
    lowered = error_text.lower()

    for keyword, (status_code, detail) in mapping.items():
        if keyword.lower() in lowered:
            raise HTTPException(status_code=status_code, detail=detail)

    raise HTTPException(status_code=default_status, detail=f"{default_message}: {error_text}")

