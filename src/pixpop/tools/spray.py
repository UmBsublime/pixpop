"""Spray paint tool for aerosol-style drawing."""

import math
import random

from pixpop.constants import (
    DEFAULT_SPRAY_DENSITY,
    MAX_SPRAY_DENSITY,
    MIN_SPRAY_DENSITY,
)
from pixpop.tools.base import Tool

# Minimum cursor travel between spray applications.
SPRAY_STEP_PIXELS = 5.0

# Pixel-count divisor per density level: 1 (lightest) to 5 (heaviest).
DENSITY_DIVISORS: dict[int, int] = {1: 16, 2: 12, 3: 8, 4: 6, 5: 4}


class SprayTool(Tool):
    """Spray paint tool that scatters pixels within circular brush radius."""

    def __init__(self):
        self.last_spray_pos: tuple[int, int] | None = None
        self.density = DEFAULT_SPRAY_DENSITY

    @property
    def name(self) -> str:
        return "spray"

    def on_mouse_down(self, canvas, x: int, y: int, button: int = 1) -> None:
        """Start spraying at position."""
        self.last_spray_pos = (x, y)
        self._apply_spray(canvas, x, y)

    def on_mouse_move(self, canvas, x: int, y: int, button: int = 1) -> None:
        """Continue spraying while dragging based on fixed distance."""
        if self.last_spray_pos is None:
            self.last_spray_pos = (x, y)
            return

        # Calculate distance from last spray position
        last_x, last_y = self.last_spray_pos
        distance = math.sqrt((x - last_x) ** 2 + (y - last_y) ** 2)

        if distance >= SPRAY_STEP_PIXELS:
            # Interpolate spray positions along the movement path
            steps = int(distance / SPRAY_STEP_PIXELS)
            for step in range(1, steps + 1):
                t = step / (steps + 1)
                interp_x = int(last_x + (x - last_x) * t)
                interp_y = int(last_y + (y - last_y) * t)
                self._apply_spray(canvas, interp_x, interp_y)
            self._apply_spray(canvas, x, y)
            self.last_spray_pos = (x, y)

    def on_mouse_up(self, canvas, x: int, y: int, button: int = 1) -> None:
        """Stop spraying and reset position tracking."""
        self.last_spray_pos = None

    def can_drag(self) -> bool:
        return True

    def set_density(self, density: int) -> None:
        """Set spray density, clamped to the supported range."""
        self.density = max(MIN_SPRAY_DENSITY, min(MAX_SPRAY_DENSITY, density))

    def _get_density_divisor(self, density: int) -> int:
        """Get the divisor used to calculate spray pixel count."""
        return DENSITY_DIVISORS.get(density, DENSITY_DIVISORS[DEFAULT_SPRAY_DENSITY])

    def _apply_spray(self, canvas, x: int, y: int) -> None:
        """Apply spray effect at position with uniform circular distribution.

        Pixels are scattered randomly within a circular brush radius area.
        Density is configurable based on spray_density setting.

        Args:
            canvas: The PaintCanvas instance.
            x: Center X coordinate.
            y: Center Y coordinate.
        """
        # Spray radius progression: size 1 = 2, then +2 for each size
        radius = 2 + (canvas.brush_size - 1) * 2

        density = max(MIN_SPRAY_DENSITY, min(MAX_SPRAY_DENSITY, self.density))

        # Calculate number of pixels to spray based on circular area and density
        divisor = self._get_density_divisor(density)
        area = math.pi * radius * radius
        num_pixels = max(1, int(area / divisor))

        updated: set[tuple[int, int]] = set()
        for _ in range(num_pixels):
            # Generate random point in circle using polar coordinates.
            # The square root gives a uniform distribution over the disc area.
            angle = random.uniform(0, 2 * math.pi)
            r = math.sqrt(random.uniform(0, 1)) * radius

            offset_x = int(r * math.cos(angle))
            offset_y = int(r * math.sin(angle))

            px = x + offset_x
            py = y + offset_y
            if canvas.normalized:
                py = py - (py % 2)

            if canvas.is_valid_position(px, py):
                canvas.set_layer_pixel(px, py, canvas.pen_color, refresh=False)
                updated.add((px, py))
                if py + 1 < canvas.height:
                    canvas.set_layer_pixel(px, py + 1, canvas.pen_color, refresh=False)
                    updated.add((px, py + 1))

        if updated:
            canvas.refresh_composite_pixels(updated)
