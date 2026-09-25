"""Line tool for drawing straight lines."""

from __future__ import annotations

from pixpop.tools.base import CanvasProtocol, snap_to_normalized
from pixpop.tools.shape_tool import ShapeTool


class LineTool(ShapeTool):
    """Line tool for drawing straight lines using Bresenham's algorithm."""

    @property
    def name(self) -> str:
        return "line"

    def get_preview_pixels(
        self,
        canvas: CanvasProtocol,
        start_x: int,
        start_y: int,
        current_x: int,
        current_y: int,
    ) -> list[tuple[int, int]]:
        """Get line pixels via Bresenham's algorithm, clamped to canvas."""
        x1 = max(0, min(start_x, canvas.width - 1))
        x2 = max(0, min(current_x, canvas.width - 1))
        y1 = max(0, min(start_y, canvas.height - 1))
        y2 = max(0, min(current_y, canvas.height - 1))

        pixels = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1

        if dx == 0 and dy == 0:
            return [(x, y)]

        x_inc = 1 if x2 > x1 else -1
        y_inc = 1 if y2 > y1 else -1

        if dx >= dy:
            error = dx // 2
            while True:
                pixels.append((x, y))
                if x == x2:
                    break
                x += x_inc
                error -= dy
                if error < 0:
                    y += y_inc
                    error += dx
        else:
            error = dy // 2
            while True:
                pixels.append((x, y))
                if y == y2:
                    break
                y += y_inc
                error -= dx
                if error < 0:
                    x += x_inc
                    error += dy

        if not canvas.normalized:
            return pixels
        return snap_to_normalized(canvas, pixels)
