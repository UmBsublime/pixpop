"""Base class for continuous freehand tools (pen, eraser, fine pen)."""

from __future__ import annotations

from abc import abstractmethod

from pixpop.tools.base import CanvasProtocol, Tool


class ContinuousTool(Tool):
    """Base for tools that paint continuously while dragging.

    Subclasses implement _paint() only; mouse down/move both paint.
    """

    def on_mouse_down(
        self, canvas: CanvasProtocol, x: int, y: int, button: int = 1
    ) -> None:
        """Paint at the press position."""
        self._paint(canvas, x, y, button)

    def on_mouse_move(
        self, canvas: CanvasProtocol, x: int, y: int, button: int = 1
    ) -> None:
        """Paint while dragging."""
        self._paint(canvas, x, y, button)

    def can_drag(self) -> bool:
        return True

    @abstractmethod
    def _paint(self, canvas: CanvasProtocol, x: int, y: int, button: int = 1) -> None:
        """Apply the tool's effect at (x, y)."""
