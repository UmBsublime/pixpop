"""Ellipse tool for drawing elliptical outlines."""

from __future__ import annotations

from pixpop.tools.base import CanvasProtocol, snap_to_normalized
from pixpop.tools.shape_tool import ShapeTool


class EllipseTool(ShapeTool):
    """Ellipse tool using the midpoint ellipse algorithm (Foley & van Dam)."""

    @property
    def name(self) -> str:
        return "ellipse"

    def get_preview_pixels(
        self,
        canvas: CanvasProtocol,
        start_x: int,
        start_y: int,
        current_x: int,
        current_y: int,
    ) -> list[tuple[int, int]]:
        """Get ellipse outline pixels for the drag-defined bounding box."""
        params = self._ellipse_params(start_x, start_y, current_x, current_y)
        if params is None:
            return []
        cx, cy, rx, ry = params
        pixels = self._ellipse_outline(canvas, cx, cy, rx, ry)
        if not canvas.normalized:
            return pixels
        return snap_to_normalized(canvas, pixels)

    @staticmethod
    def _ellipse_params(
        start_x: int, start_y: int, current_x: int, current_y: int
    ) -> tuple[int, int, int, int] | None:
        """Calculate ellipse center and radii from the anchored bounding box."""
        dx = current_x - start_x
        dy = current_y - start_y
        width = abs(dx)
        height = abs(dy)
        if width <= 0 or height <= 0:
            return None

        rx = width // 2
        ry = height // 2
        left = start_x if dx >= 0 else start_x - width
        top = start_y if dy >= 0 else start_y - height
        cx = left + rx
        cy = top + ry
        return (cx, cy, rx, ry)

    @staticmethod
    def _ellipse_outline(
        canvas: CanvasProtocol, cx: int, cy: int, rx: int, ry: int
    ) -> list[tuple[int, int]]:
        """Midpoint ellipse outline (both regions), filtered to canvas bounds."""
        pixels = []
        x = 0
        y = ry
        rx_sq = rx * rx
        ry_sq = ry * ry

        def add_quadrants(px: int, py: int) -> None:
            for qx, qy in (
                (cx + px, cy + py),
                (cx - px, cy + py),
                (cx + px, cy - py),
                (cx - px, cy - py),
            ):
                if canvas.is_valid_position(qx, qy):
                    pixels.append((qx, qy))

        # Region 1: slope > -1
        d1 = ry_sq - rx_sq * ry + 0.25 * rx_sq
        dx = 2 * ry_sq * x
        dy = 2 * rx_sq * y
        while dx < dy:
            add_quadrants(x, y)
            if d1 < 0:
                x += 1
                dx += 2 * ry_sq
                d1 += dx + ry_sq
            else:
                x += 1
                y -= 1
                dx += 2 * ry_sq
                dy -= 2 * rx_sq
                d1 += dx - dy + ry_sq

        # Region 2: slope <= -1
        d2 = ry_sq * (x + 0.5) * (x + 0.5) + rx_sq * (y - 1) * (y - 1) - rx_sq * ry_sq
        while y >= 0:
            add_quadrants(x, y)
            if d2 > 0:
                y -= 1
                dy -= 2 * rx_sq
                d2 += rx_sq - dy
            else:
                y -= 1
                x += 1
                dx += 2 * ry_sq
                dy -= 2 * rx_sq
                d2 += dx - dy + rx_sq

        return pixels
