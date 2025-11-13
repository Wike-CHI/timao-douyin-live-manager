"""
Default AI service environment values.

This module ensures that packaged builds ship with a working AI
configuration even when users do not provide a `.env` file.
"""

from __future__ import annotations

import os
from typing import Dict

_DEFAULTS: Dict[str, str] = {}


def ensure_default_ai_env() -> None:
    """Populate AI-related env vars when missing."""
    for key, value in _DEFAULTS.items():
        if not os.getenv(key):
            os.environ[key] = value
