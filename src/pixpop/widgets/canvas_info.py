"""Canvas info widget displaying cursor coordinates and canvas size."""

from __future__ import annotations

from textual.reactive import reactive
from textual.widgets import Static


class CanvasInfo(Static):
    """Widget that shows cursor coordinates and canvas size."""

    cursor_pos: tuple[int, int] | None = reactive(None, repaint=True)
    canvas_size: tuple[int, int] = reactive((0, 0), repaint=True)

    def __init__(self, workspace_id: str) -> None:
        super().__init__()
        self.workspace_id = workspace_id
        self.id = f"canvas-info-{workspace_id}"
        self.border_title = "Canvas Info"
        self.border_title_align = "left"

    def update_cursor(self, x: int, y: int) -> None:
        """Update the cursor coordinates displayed."""
        self.cursor_pos = (x, y)

    def update_canvas_size(self, width: int, height: int) -> None:
        """Update the canvas size displayed."""
        self.canvas_size = (width, height)

    def render(self) -> str:
        """Render the canvas information text."""
        if self.cursor_pos is None:
            cursor_text = "--, --"
        else:
            x, y = self.cursor_pos
            cursor_text = f"{x}, {y}"
        width, height = self.canvas_size
        return f"XY: {cursor_text}\nSize: {width} x {height}"
