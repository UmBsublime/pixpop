"""Loader for ANSI alpha ASCII canvas exports."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual.color import Color

if TYPE_CHECKING:
    from pixpop.canvas import PaintCanvas

HALF_BLOCK_TOP = "▀"
HALF_BLOCK_BOTTOM = "▄"

# Refuse ANSI files larger than this many rows or columns per line.
MAX_ANSI_ROWS = 2048
MAX_ANSI_COLUMNS = 4096


def _read_text_with_fallback(path: Path) -> str:
    """Read text as UTF-8, falling back to CP437 (classic ANSI art encoding)."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp437", errors="replace")


def load_ascii_alpha(path: Path) -> dict[str, object]:
    """Parse an ANSI alpha ASCII export into drawable pixels.

    Args:
        path: Input path.

    Returns:
        Mapping with keys: pixels (list of (x, y, Color)), width, height.

    Raises:
        ValueError: If the file exceeds row/column limits.
    """
    text = _read_text_with_fallback(path)
    lines = text.splitlines()
    if len(lines) > MAX_ANSI_ROWS:
        raise ValueError(
            f"ANSI file has {len(lines)} rows; the limit is {MAX_ANSI_ROWS}."
        )
    pixels: list[tuple[int, int, Color]] = []
    max_x = 0
    max_y = 0

    for row_index, line in enumerate(lines):
        y = row_index * 2
        x = 0
        fg: Color | None = None
        bg: Color | None = None
        idx = 0
        while idx < len(line):
            if x >= MAX_ANSI_COLUMNS:
                raise ValueError(
                    f"ANSI line {row_index + 1} exceeds {MAX_ANSI_COLUMNS} columns."
                )
            if line[idx] == "\x1b" and idx + 1 < len(line) and line[idx + 1] == "[":
                end = line.find("m", idx + 2)
                if end == -1:
                    break
                seq = line[idx + 2 : end]
                codes = [c for c in seq.split(";") if c]
                i = 0
                while i < len(codes):
                    code = codes[i]
                    if code == "0":
                        fg = None
                        bg = None
                        i += 1
                        continue
                    if code == "38" and i + 4 < len(codes) and codes[i + 1] == "2":
                        try:
                            r = int(codes[i + 2])
                            g = int(codes[i + 3])
                            b = int(codes[i + 4])
                        except ValueError:
                            i += 5
                            continue
                        fg = Color.parse(f"#{r:02x}{g:02x}{b:02x}")
                        i += 5
                        continue
                    if code == "48" and i + 4 < len(codes) and codes[i + 1] == "2":
                        try:
                            r = int(codes[i + 2])
                            g = int(codes[i + 3])
                            b = int(codes[i + 4])
                        except ValueError:
                            i += 5
                            continue
                        bg = Color.parse(f"#{r:02x}{g:02x}{b:02x}")
                        i += 5
                        continue
                    i += 1
                idx = end + 1
                continue

            char = line[idx]
            if char == "\u2580":
                if fg is not None:
                    pixels.append((x, y, fg))
                    max_x = max(max_x, x + 1)
                    max_y = max(max_y, y + 1)
                if bg is not None:
                    pixels.append((x, y + 1, bg))
                    max_x = max(max_x, x + 1)
                    max_y = max(max_y, y + 2)
            elif char == "\u2584":
                if bg is not None:
                    pixels.append((x, y, bg))
                    max_x = max(max_x, x + 1)
                    max_y = max(max_y, y + 1)
                if fg is not None:
                    pixels.append((x, y + 1, fg))
                    max_x = max(max_x, x + 1)
                    max_y = max(max_y, y + 2)
            idx += 1
            x += 1

    return {"pixels": pixels, "width": max_x, "height": max_y}


def apply_ascii_alpha(canvas: PaintCanvas, path: Path) -> None:
    """Load an ANSI alpha ASCII export into a canvas.

    Args:
        canvas: PaintCanvas instance.
        path: Input path.
    """
    data = load_ascii_alpha(path)
    pixels = data.get("pixels", [])
    width = int(data.get("width", 0))
    height = int(data.get("height", 0))
    if width or height:
        target_width = max(canvas.width, width)
        target_height = max(canvas.height, height)
        canvas.resize_preserve_content(target_width, target_height)

    updated: set[tuple[int, int]] = set()
    for x, y, color in pixels:
        if canvas.is_valid_position(x, y):
            canvas.set_layer_pixel(x, y, color, refresh=False)
            updated.add((x, y))

    if updated:
        canvas.refresh_composite_pixels(updated)
