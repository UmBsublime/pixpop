"""Paint bucket tool for flood fill operations."""

from collections import deque

from textual.color import Color

from pixpop.tools.base import Tool


class PaintBucketTool(Tool):
    """Paint bucket tool for flood fill operations."""

    @property
    def name(self) -> str:
        return "paint_bucket"

    def on_mouse_down(self, canvas, x: int, y: int, button: int = 1) -> None:
        """Perform flood fill at position."""
        self._flood_fill(canvas, x, y, canvas.pen_color)

    def _flood_fill(
        self, canvas, start_x: int, start_y: int, fill_color: Color
    ) -> None:
        """Fill an area with specified color using flood fill algorithm."""
        if not canvas.is_valid_position(start_x, start_y):
            return

        target_color = canvas.get_layer_pixel(start_x, start_y)
        if target_color == fill_color:
            return

        queue = deque([(start_x, start_y)])
        visited = set()
        updated = set()

        while queue:
            cx, cy = queue.popleft()

            if (cx, cy) in visited or not canvas.is_valid_position(cx, cy):
                continue

            current_color = canvas.get_layer_pixel(cx, cy)
            if current_color != target_color:
                continue

            canvas.set_layer_pixel(cx, cy, fill_color, refresh=False)
            updated.add((cx, cy))
            visited.add((cx, cy))

            # Neighbors are bounds-checked at dequeue time.
            queue.append((cx + 1, cy))
            queue.append((cx - 1, cy))
            queue.append((cx, cy + 1))
            queue.append((cx, cy - 1))

        if updated:
            canvas.refresh_composite_pixels(updated)
