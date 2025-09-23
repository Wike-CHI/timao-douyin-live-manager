# -*- coding: utf-8 -*-
"""
Download the VAD model into the project VAD directory.

Usage (Windows PowerShell):
  .\.venv\Scripts\python.exe tools\download_vad_model.py

Usage (bash):
  .venv/bin/python tools/download_vad_model.py

By default this downloads `iic/speech_fsmn_vad_zh-cn-16k-common-pytorch`
from ModelScope into:
  models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch

Requirements:
  pip install modelscope
"""

from __future__ import annotations

import os
import sys
import shutil
from pathlib import Path


MODEL_ID = os.environ.get(
    "VAD_MODEL_ID", "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE = PROJECT_ROOT / "models" / ".cache"
DEFAULT_DEST = (
    PROJECT_ROOT
    / "models"
    / "models"
    / "iic"
    / "speech_fsmn_vad_zh-cn-16k-common-pytorch"
)


def main() -> int:
    # Prepare cache dirs and envs to keep everything inside project
    try:
        DEFAULT_CACHE.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    os.environ.setdefault("MODELSCOPE_CACHE", str(DEFAULT_CACHE))
    os.environ.setdefault("MS_CACHE_HOME", str(DEFAULT_CACHE))

    # Resolve destination directory
    dest = Path(os.environ.get("VAD_DEST_DIR", str(DEFAULT_DEST))).resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Ensure dependency
    try:
        from modelscope.hub.snapshot_download import snapshot_download  # type: ignore
    except Exception as e:  # pragma: no cover
        print("[ERR] modelscope 未安装，请先执行: pip install -U modelscope", file=sys.stderr)
        print(f"[ERR] ImportError: {e}", file=sys.stderr)
        return 2

    print(f"[INFO] Downloading VAD model: {MODEL_ID}")
    print(f"[INFO] Cache dir: {DEFAULT_CACHE}")
    try:
        local_path = snapshot_download(model_id=MODEL_ID, cache_dir=str(DEFAULT_CACHE))
    except Exception as e:  # pragma: no cover
        print(f"[ERR] 模型下载失败: {e}", file=sys.stderr)
        return 3

    src = Path(local_path)
    print(f"[INFO] Model cached at: {src}")
    print(f"[INFO] Copying to destination: {dest}")

    # Copy to destination folder
    if dest.exists():
        # Merge copy (Python 3.8+: dirs_exist_ok)
        for p in src.rglob("*"):
            rel = p.relative_to(src)
            target = dest / rel
            if p.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(p), str(target))
    else:
        shutil.copytree(src, dest)

    print("[OK] VAD 模型已就绪:")
    print(f"      {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

