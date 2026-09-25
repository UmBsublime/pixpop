"""Loader for PNG canvas imports."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image
from textual.color import Color

if TYPE_CHECKING:
    from pixpop.canvas import PaintCanvas

# Refuse images larger than this on either axis (decompression-bomb guard).
MAX_IMAGE_DIMENSION = 4096


def load_png(path: Path) -> dict[str, object]:
    """Parse a PNG file into drawable pixels.

    Args:
        path: Input path.

    Returns:
        Mapping with keys: pixels (list of (x, y, Color)), width, height.

    Raises:
        ValueError: If the image is corrupt or exceeds the size limit.
    """
    try:
        with Image.open(path) as image:
            width, height = image.size
            if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                raise ValueError(
                    f"Image is {width}x{height}; the maximum supported size is "
                    f"{MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION}."
                )
            rgba = image.convert("RGBA")
            data = list(rgba.getdata())
    except ValueError:
        raise
    except Exception as exc:
        # PIL raises a variety of exception types for unidentifiable/corrupt
        # images (and may raise DecompressionBombError, a subclass of
        # Exception but not ValueError, from image.size).
        raise ValueError(f"Cannot read PNG file {path}: {exc}") from exc

    pixels: list[tuple[int, int, Color]] = []
    for y in range(height):
        row_offset = y * width
        for x in range(width):
            r, g, b, a = data[row_offset + x]
            if a == 0:
                continue
            pixels.append((x, y, Color(r, g, b)))

    return {"pixels": pixels, "width": width, "height": height}


def apply_png(canvas: PaintCanvas, path: Path) -> None:
    """Load a PNG file into a canvas.

    The canvas grows (never shrinks) to fit the image; pixels outside the
    image keep their existing content.

    Args:
        canvas: PaintCanvas instance.
        path: Input path.
    """
    data = load_png(path)
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
