"""Shared atomic file-write helper."""

from __future__ import annotations

import contextlib
import os
from pathlib import Path
from typing import Callable


def atomic_write(path: Path, writer: Callable[[Path], None]) -> None:
    """Write to ``path`` atomically via a temporary sibling file.

    ``writer`` is called with the temporary path and must produce the full
    file content there. On success the temp file atomically replaces the
    target; on any failure the temp file is removed and the original error
    propagates. The sibling temp file keeps ``os.replace`` on the same
    filesystem.
    """
    temp_path = path.with_name(path.name + ".tmp")
    try:
        writer(temp_path)
        os.replace(temp_path, path)
    except BaseException:
        with contextlib.suppress(OSError):
            temp_path.unlink(missing_ok=True)
        raise
