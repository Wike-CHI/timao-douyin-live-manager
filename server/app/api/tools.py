# -*- coding: utf-8 -*-
"""Tools API: maintenance helpers exposed to the renderer.

Currently provides a safe cache-clean endpoint that only removes known
build/test caches. It will never delete source code or dependencies.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, Query


router = APIRouter(prefix="/api/tools", tags=["tools"])

ROOT = Path(__file__).resolve().parents[3]  # repo root


def _remove_path(p: Path, removed: List[str], dry_run: bool) -> None:
    if not p.exists():
        return
    rel = str(p.relative_to(ROOT))
    if dry_run:
        removed.append(rel)
        return
    try:
        if p.is_dir():
            # robust rmtree: walk bottom-up
            for base, dirs, files in os.walk(p, topdown=False):
                for f in files:
                    try:
                        Path(base, f).unlink()
                    except Exception:
                        pass
                for d in dirs:
                    try:
                        Path(base, d).rmdir()
                    except Exception:
                        pass
            try:
                p.rmdir()
            except Exception:
                pass
        else:
            p.unlink(missing_ok=True)  # py3.8+: ok to ignore missing
        removed.append(rel)
    except Exception:
        # swallow errors; best-effort cleanup
        pass


def _collect_python_cache_targets() -> List[Path]:
    targets: List[Path] = []
    py_roots = [
        ROOT / "server",
        ROOT / "AST_module",
        ROOT / "DouyinLiveWebFetcher",
        ROOT / "StreamCap",
        ROOT / "tools",
    ]
    for base in py_roots:
        if not base.exists():
            continue
        for p in base.rglob("__pycache__"):
            targets.append(p)
        for p in base.rglob("*.pyc"):
            targets.append(p)
    return targets


def _collect_cache_targets() -> List[Path]:
    t: List[Path] = [
        ROOT / "electron/renderer/node_modules/.vite",
        ROOT / "electron/renderer/.vite",
        ROOT / "electron/renderer/dist",
        ROOT / ".pytest_cache",
        ROOT / ".ruff_cache",
    ]
    t.extend(_collect_python_cache_targets())
    # de-dup
    seen = set()
    uniq: List[Path] = []
    for p in t:
        if str(p) in seen:
            continue
        seen.add(str(p))
        uniq.append(p)
    return uniq


def _clean_caches(dry_run: bool = False) -> Dict[str, List[str]]:
    removed: List[str] = []
    for p in _collect_cache_targets():
        _remove_path(p, removed, dry_run=dry_run)
    return {"removed": removed, "dry_run": ["true" if dry_run else "false"][0]}


@router.get("/clean_caches/preview")
async def clean_preview() -> Dict[str, List[str]]:
    """Preview what will be removed (no deletion)."""
    return _clean_caches(dry_run=True)


@router.post("/clean_caches")
async def clean_caches(apply: bool = Query(default=True)) -> Dict[str, List[str]]:
    """Apply cache cleanup. Set `apply=false` to preview."""
    return _clean_caches(dry_run=not apply)

