"""Lightness adjustment tools (lighten/darken pixels)."""

from __future__ import annotations

from pixpop.constants import (
    BUTTON_LEFT,
    DEFAULT_LIGHT_ACCUMULATE,
    DEFAULT_LIGHT_STEP,
    MAX_LIGHT_STEP,
    MIN_LIGHT_STEP,
)
from pixpop.tools.base import CanvasProtocol, Tool


class LightnessTool(Tool):
    """Base for tools that shift the HSL lightness of painted pixels.

    Left-click applies ``direction * step`` (percent of HSL lightness) to
    every painted pixel under the brush footprint. Transparent pixels are
    left untouched. When ``accumulate`` is enabled, dragging re-applies the
    step to pixels already visited during the stroke; otherwise each pixel
    is adjusted at most once per stroke.
    """

    direction: int = 1

    def __init__(self) -> None:
        self.step = DEFAULT_LIGHT_STEP
        self.accumulate = DEFAULT_LIGHT_ACCUMULATE
        self._stroke_pixels: set[tuple[int, int]] = set()

    def on_mouse_down(
        self, canvas: CanvasProtocol, x: int, y: int, button: int = BUTTON_LEFT
    ) -> None:
        """Start a stroke and apply the lightness step at the press position."""
        self._stroke_pixels = set()
        self._apply(canvas, x, y)

    def on_mouse_move(
        self, canvas: CanvasProtocol, x: int, y: int, button: int = BUTTON_LEFT
    ) -> None:
        """Apply the lightness step while dragging."""
        self._apply(canvas, x, y)

    def on_mouse_up(
        self, canvas: CanvasProtocol, x: int, y: int, button: int = BUTTON_LEFT
    ) -> None:
        """End the stroke and reset per-stroke tracking."""
        self._stroke_pixels = set()

    def can_drag(self) -> bool:
        return True

    def set_step(self, step: int) -> None:
        """Set the lightness step (percent), clamped to the supported range."""
        self.step = max(MIN_LIGHT_STEP, min(MAX_LIGHT_STEP, step))

    def set_accumulate(self, accumulate: bool) -> None:
        """Enable/disable re-applying the step to visited pixels in a stroke."""
        self.accumulate = accumulate

    def _apply(self, canvas: CanvasProtocol, x: int, y: int) -> None:
        """Shift the lightness of painted pixels in the brush footprint."""
        side = max(1, canvas.brush_size)
        amount = self.direction * self.step / 100.0
        updated: set[tuple[int, int]] = set()
        for dx in range(side):
            for dy in range(side):
                px, py = x + dx, y + dy
                if not canvas.is_valid_position(px, py):
                    continue
                if not self.accumulate and (px, py) in self._stroke_pixels:
                    continue
                color = canvas.get_layer_pixel(px, py)
                if color is None:
                    continue
                canvas.set_layer_pixel(px, py, color.lighten(amount), refresh=False)
                self._stroke_pixels.add((px, py))
                updated.add((px, py))
        if updated:
            canvas.refresh_composite_pixels(updated)


class LightTool(LightnessTool):
    """Lighten painted pixels under the cursor."""

    direction = 1

    @property
    def name(self) -> str:
        return "light"


class DarkTool(LightnessTool):
    """Darken painted pixels under the cursor."""

    direction = -1

    @property
    def name(self) -> str:
        return "dark"
