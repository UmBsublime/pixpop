"""Pen tool for freehand drawing."""

from __future__ import annotations

from pixpop.tools.base import CanvasProtocol
from pixpop.tools.continuous_tool import ContinuousTool


class PenTool(ContinuousTool):
    """Pen tool for freehand drawing."""

    @property
    def name(self) -> str:
        return "pen"

    def _paint(self, canvas: CanvasProtocol, x: int, y: int, button: int = 1) -> None:
        canvas.draw_cell(x, y, canvas.pen_color)
