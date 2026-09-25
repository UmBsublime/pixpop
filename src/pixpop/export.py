"""Export utilities for saving canvas data."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image
from textual.color import Color

from pixpop._io import atomic_write

if TYPE_CHECKING:
    from pixpop.canvas import PaintCanvas


def _write_text_atomic(path: Path, content: str) -> None:
    """Write text to a file atomically via a temporary sibling file."""
    atomic_write(path, lambda p: p.write_text(content, encoding="utf-8"))


def _save_image_atomic(image: Image.Image, path: Path) -> None:
    """Save a PIL image atomically via a temporary sibling file.

    PIL infers the format from the file extension, which the temp suffix does
    not provide — pass it explicitly.
    """
    atomic_write(path, lambda p: image.save(p, format="PNG"))


def _color_to_rgba(color: Color) -> tuple[int, int, int, int]:
    """Convert a Textual Color to RGBA bytes.

    Args:
        color: Color instance.

    Returns:
        Tuple of (r, g, b, a) in 0-255 range.
    """
    alpha = max(0, min(255, int(round(color.a * 255))))
    return color.r, color.g, color.b, alpha


def _is_background_color(canvas: PaintCanvas, color: Color) -> bool:
    """Check if a color matches the canvas background."""
    canvas_color = canvas.canvas_color
    if canvas_color is not None and color == canvas_color:
        return True
    return color == canvas.styles.background


def _get_canvas_pixel(canvas: PaintCanvas, x: int, y: int) -> Color:
    """Get composited pixel if available, otherwise raw canvas pixel."""
    if hasattr(canvas, "get_composited_pixel"):
        color = canvas.get_composited_pixel(x, y)
        if color is not None:
            return color
        if hasattr(canvas, "get_background_pixel"):
            return canvas.get_background_pixel(x, y)
    color = canvas.get_pixel(x, y)
    if color is not None:
        return color
    background = canvas.canvas_color or canvas.styles.background
    if isinstance(background, Color):
        return background
    return Color.parse(str(background))


def _is_background_at(canvas: PaintCanvas, x: int, y: int, color: Color) -> bool:
    """Check if a pixel location is treated as background."""
    if hasattr(canvas, "get_composited_pixel"):
        return canvas.get_composited_pixel(x, y) is None
    return _is_background_color(canvas, color)


def save_canvas_ansi(canvas: PaintCanvas, path: Path, trim: bool = False) -> None:
    """Save the canvas as ANSI art with background transparency.

    Pixels matching the background are rendered as spaces. When trim is enabled,
    output is cropped to the bounding box of visible pixels with a 1px border.
    """
    width = canvas.width
    height = canvas.height
    if trim:
        bounds = _find_visible_bounds(canvas)
        if bounds is None:
            _write_text_atomic(path, "")
            return
        min_x, min_y, max_x, max_y = bounds
        min_x = max(min_x - 1, 0)
        min_y = max(min_y - 1, 0)
        max_x = min(max_x + 1, width - 1)
        max_y = min(max_y + 1, height - 1)
        output_lines = _render_ansi_region(canvas, min_x, min_y, max_x, max_y)
    else:
        output_lines = _render_ansi_region(canvas, 0, 0, width - 1, height - 1)

    content = "\n".join(output_lines)
    if content:
        content += "\n"
    _write_text_atomic(path, content)


def _find_visible_bounds(
    canvas: PaintCanvas,
) -> tuple[int, int, int, int] | None:
    width = canvas.width
    height = canvas.height
    min_x = min_y = None
    max_x = max_y = None
    for y in range(height):
        for x in range(width):
            color = _get_canvas_pixel(canvas, x, y)
            if _is_background_at(canvas, x, y, color):
                continue
            if min_x is None:
                min_x = max_x = x
                min_y = max_y = y
            else:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    if min_x is None or min_y is None or max_x is None or max_y is None:
        return None
    return min_x, min_y, max_x, max_y


def _render_ansi_region(
    canvas: PaintCanvas,
    min_x: int,
    min_y: int,
    max_x: int,
    max_y: int,
) -> list[str]:
    width = canvas.width
    height = canvas.height
    start_y = (min_y // 2) * 2
    end_y = (max_y // 2) * 2
    lines: list[str] = []

    for y in range(start_y, end_y + 1, 2):
        parts = []
        for x in range(min_x, max_x + 1):
            if x < 0 or x >= width:
                parts.append("\x1b[0m ")
                continue
            top, top_bg = _pixel_for_render(canvas, x, y, min_y, max_y, height)
            bottom, bottom_bg = _pixel_for_render(
                canvas, x, y + 1, min_y, max_y, height
            )
            if top_bg and bottom_bg:
                parts.append("\x1b[0m ")
                continue
            tr, tg, tb, _ = _color_to_rgba(top)
            br, bg, bb, _ = _color_to_rgba(bottom)
            if top_bg and not bottom_bg:
                parts.append(f"\x1b[0m\x1b[38;2;{br};{bg};{bb}m\u2584")
            elif bottom_bg and not top_bg:
                parts.append(f"\x1b[0m\x1b[38;2;{tr};{tg};{tb}m\u2580")
            else:
                parts.append(
                    f"\x1b[38;2;{tr};{tg};{tb}m\x1b[48;2;{br};{bg};{bb}m\u2580"
                )
        parts.append("\x1b[0m")
        lines.append("".join(parts))

    return lines


def _pixel_for_render(
    canvas: PaintCanvas,
    x: int,
    y: int,
    min_y: int,
    max_y: int,
    height: int,
) -> tuple[Color, bool]:
    if y < min_y or y > max_y or y < 0 or y >= height:
        color = _get_canvas_pixel(canvas, x, max(min_y, 0))
        return color, True
    color = _get_canvas_pixel(canvas, x, y)
    return color, _is_background_at(canvas, x, y, color)


def save_canvas_png(canvas: PaintCanvas, path: Path, scale: int = 1) -> None:
    """Save the full canvas as a PNG image.

    Args:
        canvas: PaintCanvas instance.
        path: Output path.
        scale: Integer upscale factor (minimum 1).
    """
    width = canvas.width
    height = canvas.height

    scale = max(1, scale)
    image = Image.new("RGBA", (width, height))
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            color = _get_canvas_pixel(canvas, x, y)
            r, g, b, a = _color_to_rgba(color)
            if _is_background_at(canvas, x, y, color):
                a = 0
            pixels[x, y] = (r, g, b, a)

    if scale > 1:
        image = image.resize(
            (width * scale, height * scale),
            resample=Image.Resampling.NEAREST,
        )
    _save_image_atomic(image, path)
