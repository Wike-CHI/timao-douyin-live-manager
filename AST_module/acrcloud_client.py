# -*- coding: utf-8 -*-
"""ACRCloud 识别客户端封装（可选依赖）。"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

try:
    from acrcloud.recognizer import ACRCloudRecognizer  # type: ignore

    ACR_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - SDK 未安装时降级
    ACRCloudRecognizer = object  # type: ignore
    ACR_SDK_AVAILABLE = False

LOGGER = logging.getLogger(__name__)


def _parse_bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _parse_float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass
class ACRMusicMatch:
    title: str
    artist: str
    album: Optional[str]
    score: float
    acrid: Optional[str]
    play_offset_ms: Optional[int]
    metadata: Dict[str, Any]


class ACRCloudClient:
    """Thin wrapper around acrcloud_sdk_python recognizer."""

    def __init__(
        self,
        *,
        host: str,
        access_key: str,
        access_secret: str,
        timeout: float = 10.0,
        min_score: float = 0.65,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        if not ACR_SDK_AVAILABLE:  # pragma: no cover
            raise RuntimeError("acrcloud_sdk_python 未安装，无法启用 ACRCloud 背景音乐识别。")
        self.logger = logger or LOGGER
        self.min_score = max(0.0, min_score)
        
        # 使用字典配置而不是ACRCloudConfig类
        config = {
            'host': host,
            'access_key': access_key,
            'access_secret': access_secret,
            'timeout': max(3, int(timeout))
        }
        self._recognizer = ACRCloudRecognizer(config)

    def identify(self, audio_bytes: bytes) -> Optional[ACRMusicMatch]:
        if not audio_bytes:
            return None
        try:
            result_str = self._recognizer.recognize_by_filebuffer(audio_bytes, 0)
        except Exception as exc:  # pragma: no cover - SDK 内部异常
            self.logger.warning("ACRCloud 识别失败: %s", exc)
            return None
        if not result_str:
            return None
        try:
            data = json.loads(result_str)
        except json.JSONDecodeError:  # pragma: no cover
            self.logger.debug("ACRCloud 返回内容无法解析: %r", result_str[:80])
            return None
        status = (data or {}).get("status") or {}
        if status.get("code") != 0:
            # 0 表示命中；其它 code 参考官方文档
            return None
        metadata = (data or {}).get("metadata") or {}
        candidates = metadata.get("music") or []
        if not candidates:
            return None
        best = candidates[0]
        try:
            score = float(best.get("score", 0.0))
        except Exception:
            score = 0.0
        if score < self.min_score:
            return None
        return ACRMusicMatch(
            title=str(best.get("title") or ""),
            artist=", ".join(best.get("artists", [])) if isinstance(best.get("artists"), list) else str(best.get("artist", "")),
            album=str(best.get("album", {}).get("name") if isinstance(best.get("album"), dict) else best.get("album") or ""),
            score=score,
            acrid=str(best.get("acrid") or "") or None,
            play_offset_ms=int(best.get("play_offset_ms") or 0) if best.get("play_offset_ms") is not None else None,
            metadata=best,
        )


def load_acr_client_from_env(
    *,
    logger: Optional[logging.Logger] = None,
) -> Tuple[Optional[ACRCloudClient], Optional[str]]:
    """Attempt to construct client from环境变量.

    Returns (client, error_message). error_message 为 None 表示成功。
    """
    log = logger or LOGGER
    if not _parse_bool_env("ACR_ENABLE", False):
        return None, "ACR_ENABLE 未开启"
    host = os.getenv("ACR_HOST") or os.getenv("ACR_SERVER")
    key = os.getenv("ACR_ACCESS_KEY") or os.getenv("ACR_KEY")
    secret = os.getenv("ACR_SECRET_KEY") or os.getenv("ACR_SECRET")
    if not host or not key or not secret:
        return None, "缺少 ACR_HOST / ACR_ACCESS_KEY / ACR_SECRET_KEY 配置"
    if not ACR_SDK_AVAILABLE:
        return None, "acrcloud_sdk_python 未安装"
    min_score = _parse_float_env("ACR_MIN_SCORE", 0.65)
    timeout = _parse_float_env("ACR_TIMEOUT", 10.0)
    try:
        client = ACRCloudClient(
            host=host,
            access_key=key,
            access_secret=secret,
            timeout=timeout,
            min_score=min_score,
            logger=log,
        )
        return client, None
    except Exception as exc:  # pragma: no cover - 初始化异常直接返回
        log.warning("初始化 ACRCloudClient 失败: %s", exc)
        return None, str(exc)
