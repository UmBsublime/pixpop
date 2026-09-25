"""Eraser tool for clearing pixels."""

from __future__ import annotations

from pixpop.tools.base import CanvasProtocol
from pixpop.tools.continuous_tool import ContinuousTool


class EraserTool(ContinuousTool):
    """Eraser tool for clearing pixels."""

    @property
    def name(self) -> str:
        return "eraser"

    def is_eraser(self) -> bool:
        return True

    def _paint(self, canvas: CanvasProtocol, x: int, y: int, button: int = 1) -> None:
        canvas.draw_cell(x, y, None, is_erase=True)
