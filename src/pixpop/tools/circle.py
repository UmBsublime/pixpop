"""Circle tool for drawing circular outlines."""

from __future__ import annotations

from pixpop.tools.base import CanvasProtocol, snap_to_normalized
from pixpop.tools.shape_tool import ShapeTool


class CircleTool(ShapeTool):
    """Circle tool using Bresenham's midpoint circle algorithm."""

    @property
    def name(self) -> str:
        return "circle"

    def get_preview_pixels(
        self,
        canvas: CanvasProtocol,
        start_x: int,
        start_y: int,
        current_x: int,
        current_y: int,
    ) -> list[tuple[int, int]]:
        """Get circle outline pixels for the drag-defined bounding box."""
        params = self._circle_params(start_x, start_y, current_x, current_y)
        if params is None:
            return []
        cx, cy, radius = params
        pixels = self._circle_outline(canvas, cx, cy, radius)
        if not canvas.normalized:
            return pixels
        return snap_to_normalized(canvas, pixels, center_y=cy)

    @staticmethod
    def _circle_params(
        start_x: int, start_y: int, current_x: int, current_y: int
    ) -> tuple[int, int, int] | None:
        """Calculate circle center and radius from the anchored bounding box."""
        dx = current_x - start_x
        dy = current_y - start_y
        size = min(abs(dx), abs(dy))
        if size <= 0:
            return None

        left = start_x if dx >= 0 else start_x - size
        top = start_y if dy >= 0 else start_y - size

        radius = size // 2
        cx = left + radius
        cy = top + radius
        return (cx, cy, radius)

    @staticmethod
    def _circle_outline(
        canvas: CanvasProtocol, cx: int, cy: int, radius: int
    ) -> list[tuple[int, int]]:
        """Bresenham midpoint circle outline, filtered to canvas bounds."""
        pixels = []
        x = 0
        y = radius
        d = 3 - 2 * radius

        while x <= y:
            points = [
                (cx + x, cy + y),
                (cx - x, cy + y),
                (cx + x, cy - y),
                (cx - x, cy - y),
                (cx + y, cy + x),
                (cx - y, cy + x),
                (cx + y, cy - x),
                (cx - y, cy - x),
            ]
            for px, py in points:
                if canvas.is_valid_position(px, py):
                    pixels.append((px, py))

            if d < 0:
                d = d + 4 * x + 6
            else:
                d = d + 4 * (x - y) + 10
                y -= 1
            x += 1

        return pixels
