#!/usr/bin/env python3
"""
Clean common build/test caches for this repo (safe, targeted; no source deletion).

Usage:
  - Dry run (default):   python tools/clean_caches.py
  - Apply deletion:      python tools/clean_caches.py --apply

What it removes (if present):
  - Vite/Rollup caches & build artifacts under electron/renderer
    · electron/renderer/node_modules/.vite
    · electron/renderer/.vite
    · electron/renderer/dist
  - Generic Node/Vite caches in repo root
    · node_modules/.vite
    · .vite
  - Python caches
    · **/__pycache__ directories
    · .pytest_cache, .ruff_cache
    · *.pyc files

It will NOT touch:
  - node_modules, package-lock.json, records/, data/, logs/
  - any tracked source code
"""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rm(path: Path, apply: bool) -> None:
    if not path.exists():
        return
    rel = path.relative_to(ROOT)
    if apply:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
            print(f"removed dir  {rel}")
        else:
            try:
                path.unlink()
                print(f"removed file {rel}")
            except FileNotFoundError:
                pass
    else:
        print(f"would remove  {rel}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually delete files")
    args = ap.parse_args()
    apply = args.apply

    # Targeted directories/files
    targets = [
        ROOT / "electron/renderer/node_modules/.vite",
        ROOT / "electron/renderer/.vite",
        ROOT / "electron/renderer/dist",
        ROOT / "node_modules/.vite",
        ROOT / ".vite",
        ROOT / ".pytest_cache",
        ROOT / ".ruff_cache",
    ]

    for t in targets:
        rm(t, apply)

    # Python bytecode and __pycache__ across repo (shallow scan)
    # Python bytecode and __pycache__ within selected source roots (fast)
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
            rm(p, apply)
        for p in base.rglob("*.pyc"):
            rm(p, apply)

    print("done.")
    if not apply:
        print("(dry run) no files were deleted; re-run with --apply to cleanup")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
