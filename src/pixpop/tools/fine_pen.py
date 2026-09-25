"""Fine pen tool for single-pixel drawing."""

from __future__ import annotations

from pixpop.constants import BUTTON_MIDDLE, BUTTON_RIGHT
from pixpop.tools.base import CanvasProtocol
from pixpop.tools.continuous_tool import ContinuousTool


class FinePenTool(ContinuousTool):
    """Fine pen tool for drawing single/half pixels."""

    @property
    def name(self) -> str:
        return "fine-pen"

    def _paint(self, canvas: CanvasProtocol, x: int, y: int, button: int = 1) -> None:
        if not canvas.is_valid_position(x, y):
            return
        if button == BUTTON_MIDDLE:
            updated: list[tuple[int, int]] = []
            for target_y in (y, y + 1):
                if canvas.is_valid_position(x, target_y):
                    canvas.set_layer_pixel(x, target_y, canvas.pen_color, refresh=False)
                    updated.append((x, target_y))
            if updated:
                canvas.refresh_composite_pixels(updated)
            return

        target_y = y + 1 if button == BUTTON_RIGHT else y
        if not canvas.is_valid_position(x, target_y):
            return
        canvas.set_layer_pixel(x, target_y, canvas.pen_color)
