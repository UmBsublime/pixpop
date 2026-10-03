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

# First 16 entries of the xterm 256-color palette (standard + bright).
_ANSI_16: tuple[str, ...] = (
    "#000000",
    "#800000",
    "#008000",
    "#808000",
    "#000080",
    "#800080",
    "#008080",
    "#c0c0c0",
    "#808080",
    "#ff0000",
    "#00ff00",
    "#ffff00",
    "#0000ff",
    "#ff00ff",
    "#00ffff",
    "#ffffff",
)

# 6x6x6 color cube levels used by indices 16..231.
_ANSI_CUBE_LEVELS: tuple[int, ...] = (0, 95, 135, 175, 215, 255)


def _ansi_256_to_hex(index: int) -> str:
    """Map an xterm 256-color palette index to a #rrggbb hex string."""
    if index < 16:
        return _ANSI_16[index]
    if index < 232:
        i = index - 16
        r = _ANSI_CUBE_LEVELS[i // 36]
        g = _ANSI_CUBE_LEVELS[(i // 6) % 6]
        b = _ANSI_CUBE_LEVELS[i % 6]
        return f"#{r:02x}{g:02x}{b:02x}"
    # 232..255: 24-step grayscale ramp from #080808 to #eeeeee.
    level = 8 + (index - 232) * 10
    return f"#{level:02x}{level:02x}{level:02x}"


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
        Mapping with keys: pixels (list of (x, y, Color)), width, height,
        saw_block_glyph (bool — True if any ▀/▄ was encountered, even when
        no pixels could be drawn because colors were unrecognized).

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
    saw_block_glyph = False

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
                    if (
                        code in {"38", "48"}
                        and i + 2 < len(codes)
                        and codes[i + 1] == "5"
                    ):
                        try:
                            index = int(codes[i + 2])
                        except ValueError:
                            i += 3
                            continue
                        if 0 <= index <= 255:
                            color = Color.parse(_ansi_256_to_hex(index))
                            if code == "38":
                                fg = color
                            else:
                                bg = color
                        i += 3
                        continue
                    i += 1
                idx = end + 1
                continue

            char = line[idx]
            if char == "▀":
                saw_block_glyph = True
                if fg is not None:
                    pixels.append((x, y, fg))
                    max_x = max(max_x, x + 1)
                    max_y = max(max_y, y + 1)
                if bg is not None:
                    pixels.append((x, y + 1, bg))
                    max_x = max(max_x, x + 1)
                    max_y = max(max_y, y + 2)
            elif char == "▄":
                saw_block_glyph = True
                if bg is not None:
                    pixels.append((x, y, bg))
                    max_x = max(max_x, x + 1)
                    max_y = max(max_y, y + 1)
                if fg is not None:
                    pixels.append((x, y + 1, fg))
                    max_x = max(max_x, x + 1)
                    max_y = max(max_y, y + 2)
            elif char == "█":
                saw_block_glyph = True
                if fg is not None:
                    pixels.append((x, y, fg))
                    pixels.append((x, y + 1, fg))
                    max_x = max(max_x, x + 1)
                    max_y = max(max_y, y + 2)
            idx += 1
            x += 1

    return {
        "pixels": pixels,
        "width": max_x,
        "height": max_y,
        "saw_block_glyph": saw_block_glyph,
    }


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
    elif data.get("saw_block_glyph"):
        try:
            canvas.app.notify(
                f"Loaded 0 pixels from {path.name} — file may use unsupported "
                "color codes.",
                title="Load",
                severity="warning",
            )
        except Exception:
            pass
