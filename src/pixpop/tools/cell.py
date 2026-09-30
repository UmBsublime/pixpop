"""Cell tool for painting whole terminal cells."""

from __future__ import annotations

from pixpop.tools.base import CanvasProtocol
from pixpop.tools.continuous_tool import ContinuousTool


class CellTool(ContinuousTool):
    """Cell tool: paints both pixels of the terminal cell under the cursor.

    Brush size does not apply; the canvas supplies the 1x2 cell footprint.
    """

    @property
    def name(self) -> str:
        return "cell"

    def _paint(self, canvas: CanvasProtocol, x: int, y: int, button: int = 1) -> None:
        canvas.draw_cell(x, y, canvas.pen_color)
