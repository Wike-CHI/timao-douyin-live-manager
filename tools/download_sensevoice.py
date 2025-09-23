#!/usr/bin/env python3
"""
Download SenseVoiceSmall model weights into models/models/iic/SenseVoiceSmall
using ModelScope snapshot_download. Re-runnable and offline-cache friendly.
"""
import os
from pathlib import Path

def main():
    try:
        from modelscope.hub.snapshot_download import snapshot_download
    except Exception as e:
        print("[download] Please install modelscope: pip install -U modelscope")
        raise

    repo = 'iic/SenseVoiceSmall'
    project_root = Path(__file__).resolve().parents[1]
    target = project_root / 'models' / 'models' / 'iic' / 'SenseVoiceSmall'
    cache = project_root / 'models' / '.cache' / 'modelscope'
    cache.mkdir(parents=True, exist_ok=True)
    print(f"[download] Downloading {repo} to cache {cache} ...")
    local_dir = snapshot_download(model_id=repo, cache_dir=str(cache))

    src = Path(local_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Create/Update a symlink to the cached dir to avoid copying large files
    try:
        if target.exists() or target.is_symlink():
            target.unlink()
    except Exception:
        pass
    try:
        target.symlink_to(src, target_is_directory=True)
        print(f"[download] Linked {target} -> {src}")
    except Exception:
        # Fallback: keep a marker file pointing to cache
        with open(target / 'CACHE_PATH.txt', 'w', encoding='utf-8') as f:
            f.write(str(src))
        print(f"[download] Wrote {target/'CACHE_PATH.txt'}")

    print("[download] Done.")

if __name__ == '__main__':
    main()

