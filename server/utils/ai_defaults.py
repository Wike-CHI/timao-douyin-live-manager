"""
Default AI service environment values.

This module ensures that packaged builds ship with a working AI
configuration even when users do not provide a `.env` file.
"""

from __future__ import annotations

import os
from typing import Dict

# Hard-coded defaults bundled with the application.
_DEFAULTS: Dict[str, str] = {
    "AI_SERVICE": "qwen",
    "AI_BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "AI_MODEL": "qwen-plus",
    "AI_API_KEY": "sk-92045f0a33984350925ce3ccffb3489e",
    # OpenAI-compatible aliases (many downstream modules expect these)
    "OPENAI_API_KEY": "sk-92045f0a33984350925ce3ccffb3489e",
    "OPENAI_BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "OPENAI_MODEL": "qwen-plus",
}


def ensure_default_ai_env() -> None:
    """Populate AI-related env vars when missing."""
    for key, value in _DEFAULTS.items():
        if not os.getenv(key):
            os.environ[key] = value
