"""Base class for drag-to-draw shape tools (line, rectangle, circle, ellipse)."""

from __future__ import annotations

from abc import abstractmethod

from pixpop.tools.base import CanvasProtocol, Tool


class ShapeTool(Tool):
    """Template-method base for shape tools with live preview.

    Subclasses implement only the geometry: given the drag start and current
    position, return the outline pixels. The base class owns the full
    mouse lifecycle and the shared draw-through-brush commit.
    """

    def __init__(self) -> None:
        self.start_pos: tuple[int, int] | None = None

    def on_mouse_down(
        self, canvas: CanvasProtocol, x: int, y: int, button: int = 1
    ) -> None:
        """Record the drag start position."""
        self.start_pos = (x, y)

    def on_mouse_up(
        self, canvas: CanvasProtocol, x: int, y: int, button: int = 1
    ) -> None:
        """Commit the shape defined by the drag from start to current."""
        if self.start_pos is None:
            return
        pixels = self.get_preview_pixels(
            canvas, self.start_pos[0], self.start_pos[1], x, y
        )
        for px, py in pixels:
            canvas.draw_cell(px, py, canvas.pen_color)
        self.start_pos = None

    def supports_preview(self) -> bool:
        return True

    @abstractmethod
    def get_preview_pixels(
        self,
        canvas: CanvasProtocol,
        start_x: int,
        start_y: int,
        current_x: int,
        current_y: int,
    ) -> list[tuple[int, int]]:
        """Return the outline pixels for the shape (geometry lives here)."""
