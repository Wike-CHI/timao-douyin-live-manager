# -*- coding: utf-8 -*-
"""First‑run bootstrap helpers

- Ensure local FFmpeg binary is available (prefer PATH, else download Windows zip to tools/ffmpeg/win64)
- Ensure SenseVoiceSmall + VAD models exist (invoke tools/download_* scripts if missing)

We do NOT modify system PATH permanently. Instead we resolve a local ffmpeg
binary and set FFMPEG_BIN in-process so subprocess calls can use it reliably.
"""
from __future__ import annotations

import io
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from threading import Lock
from typing import Dict, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
_status_lock = Lock()
_status: Dict[str, object] = {
    "running": False,
    "ffmpeg": {"state": "unknown", "path": "", "error": ""},
    "models": {"state": "unknown", "model_present": False, "vad_present": False},
    "suggestions": [],
    "paths": {"model_dir": "", "vad_dir": "", "ffmpeg_dir": ""},
}

def get_status() -> Dict[str, object]:
    with _status_lock:
        return dict(_status)


def _log(msg: str) -> None:
    try:
        import logging

        logging.info(msg)
    except Exception:
        print(msg)


def which(cmd: str) -> Optional[str]:
    try:
        return shutil.which(cmd)
    except Exception:
        return None


def resolve_local_ffmpeg_path() -> Optional[Path]:
    """Return a candidate local ffmpeg path under tools/ffmpeg/* if present."""
    tools = PROJECT_ROOT / "tools" / "ffmpeg"
    candidates = []
    if platform.system().lower().startswith("win"):
        candidates.append(tools / "win64" / "bin" / "ffmpeg.exe")
        candidates.append(tools / "win32" / "bin" / "ffmpeg.exe")
    elif platform.system().lower() == "darwin":
        candidates.append(tools / "mac" / "bin" / "ffmpeg")
    else:
        candidates.append(tools / "linux" / "bin" / "ffmpeg")
    for p in candidates:
        try:
            if p.exists():
                return p
        except Exception:
            pass
    return None


def ensure_ffmpeg() -> Optional[str]:
    """Ensure ffmpeg is invokable.

    Returns the absolute binary path if resolved or downloaded; otherwise None.
    """
    # Already available on PATH
    with _status_lock:
        _status["running"] = True
        _status["ffmpeg"] = {"state": "checking", "path": "", "error": ""}
    path_on_path = which("ffmpeg")
    if path_on_path:
        _log(f"FFmpeg found on PATH: {path_on_path}")
        os.environ.setdefault("FFMPEG_BIN", path_on_path)
        with _status_lock:
            _status["ffmpeg"] = {"state": "ok", "path": path_on_path, "error": ""}
            try:
                _status["paths"]["ffmpeg_dir"] = str(Path(path_on_path).parent)
            except Exception:
                pass
        return path_on_path

    # Local vendored path
    local = resolve_local_ffmpeg_path()
    if local and local.exists():
        os.environ.setdefault("FFMPEG_BIN", str(local))
        _log(f"FFmpeg found locally: {local}")
        with _status_lock:
            _status["ffmpeg"] = {"state": "ok", "path": str(local), "error": ""}
            _status["paths"]["ffmpeg_dir"] = str(local.parent)
        return str(local)

    # Attempt a lightweight download for Windows only (safe zip)
    if platform.system().lower().startswith("win"):
        try:
            import urllib.request  # Lazy import to avoid hard dependency at module import
            
            url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
            dest_root = PROJECT_ROOT / "tools" / "ffmpeg" / "win64"
            dest_bin = dest_root / "bin"
            dest_bin.mkdir(parents=True, exist_ok=True)
            _log("Downloading FFmpeg (Windows essentials zip)…")
            with urllib.request.urlopen(url, timeout=60) as r:
                buf = r.read()
            with zipfile.ZipFile(io.BytesIO(buf)) as zf:
                # extract ffmpeg.exe/ffprobe.exe from */bin/
                for name in zf.namelist():
                    if name.endswith("/bin/ffmpeg.exe") or name.endswith("/bin/ffprobe.exe"):
                        # Strip leading folder
                        filename = Path(name).name
                        with zf.open(name) as src, open(dest_bin / filename, "wb") as dst:
                            dst.write(src.read())
            ff = dest_bin / "ffmpeg.exe"
            if ff.exists():
                os.environ.setdefault("FFMPEG_BIN", str(ff))
                _log(f"FFmpeg installed to: {ff}")
                with _status_lock:
                    _status["ffmpeg"] = {"state": "ok", "path": str(ff), "error": ""}
                    _status["paths"]["ffmpeg_dir"] = str(ff.parent)
                return str(ff)
        except Exception as e:  # pragma: no cover
            _log(f"FFmpeg download failed (will require manual install): {e}")
            with _status_lock:
                _status["ffmpeg"] = {"state": "error", "path": "", "error": str(e)}

    _log("FFmpeg not available; please install ffmpeg and ensure it's on PATH")
    with _status_lock:
        _status["ffmpeg"] = {"state": "missing", "path": "", "error": _status["ffmpeg"].get("error", "") if isinstance(_status.get("ffmpeg"), dict) else ""}
    return None


def ensure_models() -> Dict[str, bool]:
    """Ensure SenseVoiceSmall and VAD directories exist; attempt download if missing."""
    mdir = PROJECT_ROOT / "models" / "models" / "iic" / "SenseVoiceSmall"
    vdir = PROJECT_ROOT / "models" / "models" / "iic" / "speech_fsmn_vad_zh-cn-16k-common-pytorch"
    ok_m = mdir.exists()
    ok_v = vdir.exists()
    with _status_lock:
        _status["models"] = {"state": "checking", "model_present": ok_m, "vad_present": ok_v}
    with _status_lock:
        _status["paths"]["model_dir"] = str(mdir)
        _status["paths"]["vad_dir"] = str(vdir)
    if ok_m and ok_v:
        with _status_lock:
            _status["models"] = {"state": "ok", "model_present": True, "vad_present": True}
        return {"model": True, "vad": True}

    # Try running download scripts (best effort, only if Python deps available)
    py_exe = sys.executable or "python"
    try:
        if not ok_m:
            _log("Downloading SenseVoiceSmall model…")
            subprocess.run([py_exe, str(PROJECT_ROOT / "tools" / "download_sensevoice.py")], check=False, cwd=str(PROJECT_ROOT))
        if not ok_v:
            _log("Downloading VAD model…")
            subprocess.run([py_exe, str(PROJECT_ROOT / "tools" / "download_vad_model.py")], check=False, cwd=str(PROJECT_ROOT))
    except Exception:
        pass
    ok_m = mdir.exists(); ok_v = vdir.exists()
    with _status_lock:
        _status["models"] = {"state": "ok" if (ok_m and ok_v) else "missing", "model_present": ok_m, "vad_present": ok_v}
        _status["paths"]["model_dir"] = str(mdir)
        _status["paths"]["vad_dir"] = str(vdir)
    return {"model": ok_m, "vad": ok_v}


def bootstrap_all() -> Dict[str, object]:
    ff = ensure_ffmpeg()
    mv = ensure_models()
    # Suggestions for offline fallback
    sugg = []
    if not mv.get("model"):
        sugg.append("手动放置 SenseVoiceSmall 到 models/models/iic/SenseVoiceSmall")
    if not mv.get("vad"):
        sugg.append("手动放置 VAD 到 models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch")
    with _status_lock:
        _status["running"] = False
        _status["suggestions"] = sugg
    return {"ffmpeg": ff or "", "models": mv, "suggestions": sugg}

def start_bootstrap_async() -> None:
    """Kick off bootstrap in a background thread/process."""
    with _status_lock:
        _status["running"] = True
    try:
        import threading
        threading.Thread(target=bootstrap_all, daemon=True).start()
    except Exception:
        # Best effort fallback
        try:
            bootstrap_all()
        except Exception:
            pass
