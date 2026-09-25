"""Rectangle tool for drawing rectangle outlines."""

from __future__ import annotations

from pixpop.tools.base import CanvasProtocol
from pixpop.tools.shape_tool import ShapeTool


class RectangleTool(ShapeTool):
    """Rectangle tool for drawing rectangle outlines."""

    @property
    def name(self) -> str:
        return "rectangle"

    def get_preview_pixels(
        self,
        canvas: CanvasProtocol,
        start_x: int,
        start_y: int,
        current_x: int,
        current_y: int,
    ) -> list[tuple[int, int]]:
        """Get rectangle outline pixels, clamped to canvas."""
        x1 = max(0, min(start_x, canvas.width - 1))
        x2 = max(0, min(current_x, canvas.width - 1))
        y1 = max(0, min(start_y, canvas.height - 1))
        y2 = max(0, min(current_y, canvas.height - 1))

        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)

        pixels = []

        # Top and bottom edges
        for x in range(min_x, max_x + 1):
            pixels.append((x, min_y))
            pixels.append((x, max_y))

        # Left and right edges (avoid double-counting corners)
        for y in range(min_y + 1, max_y):
            pixels.append((min_x, y))
            pixels.append((max_x, y))

        return pixels
