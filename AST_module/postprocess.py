# -*- coding: utf-8 -*-
"""
后处理与分句模块（中文）

- 清洗文本，统一中英文标点，去除重复与噪声
- 简单防幻觉：能量门限 + 文本规则过滤
- 智能分句：依据标点与静音边界进行长/短句拆分
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np


def pcm16_rms(audio: bytes) -> float:
    if not audio:
        return 0.0
    try:
        arr = np.frombuffer(audio, dtype=np.int16)
        if arr.size == 0:
            return 0.0
        # 归一化到 0..1
        f = arr.astype(np.float32) / 32768.0
        return float(np.sqrt(np.mean(f * f)))
    except Exception:
        return 0.0


_ZH_PUNCS = "，。！？；：、“”‘’（）《》【】…—·,.!?;:()[]<>\-"
_MONO_ALLOW = set("嗯啊哦喔唔呃诶咦哈呵哇啦呀嘛呐唉哟呜哼")


class ChineseCleaner:
    _multi_space = re.compile(r"\s+")
    _dup_punc = re.compile(r"([，。！？；：,…])\1+")

    def clean(self, text: str) -> str:
        if not text:
            return ""
        t = text.strip()
        # 替换英文标点为中文常用
        t = t.replace(",", "，").replace(";", "；").replace(":", "：")
        t = t.replace("?", "？").replace("!", "！").replace(".", "。")
        # 合并重复标点，如 “。。。”→“。”
        t = self._dup_punc.sub(r"\1", t)
        # 规范空白
        t = self._multi_space.sub("", t)
        return t


def _only_punc_or_space(text: str) -> bool:
    if not text:
        return True
    for ch in text:
        if ch.strip() and ch not in _ZH_PUNCS:
            return False
    return True


class HallucinationGuard:
    def __init__(self, min_rms: float = 0.012, min_len: int = 2, low_conf: float = 0.35):
        self.min_rms = min_rms
        self.min_len = min_len
        self.low_conf = low_conf

    def should_drop(self, text: str, confidence: float, rms: float) -> bool:
        # 无语音能量且文本过短/仅标点 → 丢弃
        if rms < self.min_rms and (len(text) < self.min_len or _only_punc_or_space(text)):
            return True
        # 仅标点 → 丢弃
        if _only_punc_or_space(text):
            return True
        # 单字且不在允许词且置信度低 → 丢弃
        if len(text) == 1 and text not in _MONO_ALLOW and confidence < self.low_conf:
            return True
        return False


@dataclass
class SentenceAssembler:
    """基于标点与静音的中文分句器。
    - max_wait: 超过该时间未出现结尾标点则强制出句
    - max_chars: 防止过长句
    - silence_flush: 连续静音次数触发出句
    """

    max_wait: float = 3.5
    max_chars: int = 48
    silence_flush: int = 2

    def __post_init__(self):
        self._buf: str = ""
        self._last_ts: float = 0.0
        self._silence: int = 0

    def feed(self, text: str, now: Optional[float] = None) -> Tuple[bool, str]:
        now = now or time.time()
        if not text:
            return False, ""
        self._buf += text
        self._last_ts = now

        end = any(ch in text for ch in "。！？；")
        if end and len(self._buf) >= 2:
            out = self._buf
            self._buf = ""
            self._silence = 0
            return True, out

        if len(self._buf) >= self.max_chars:
            out = self._buf
            self._buf = ""
            self._silence = 0
            return True, out

        return False, self._buf

    def mark_silence(self) -> Optional[str]:
        self._silence += 1
        if self._silence >= self.silence_flush and len(self._buf) >= 2:
            out = self._buf
            self._buf = ""
            self._silence = 0
            return out
        return None

    def tick(self, now: Optional[float] = None) -> Optional[str]:
        """基于时间的强制出句：
        - 距上次追加超过 max_wait，则将缓冲区内容作为一句输出。
        - 避免长时间没有终止标点时一直不出句。
        """
        now = now or time.time()
        if self._buf and self._last_ts > 0 and (now - self._last_ts) >= self.max_wait:
            out = self._buf
            self._buf = ""
            self._silence = 0
            self._last_ts = now
            return out
        return None

    def reset(self):
        self._buf = ""
        self._silence = 0
