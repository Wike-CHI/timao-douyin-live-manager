from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


class JSONLWriter:
    """Simple JSON Lines writer with safe directory creation and flush-on-write."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._fh: Optional[Any] = None

    def open(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Use UTF-8 without BOM
        self._fh = self.path.open("a", encoding="utf-8")

    def write(self, obj: Any) -> None:
        if self._fh is None:
            self.open()
        assert self._fh is not None
        self._fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
        try:
            self._fh.flush()
        except Exception:
            pass

    def close(self) -> None:
        try:
            if self._fh is not None:
                self._fh.close()
        finally:
            self._fh = None

