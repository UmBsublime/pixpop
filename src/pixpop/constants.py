"""Shared constants for pixpop — single source of truth for magic values."""

from __future__ import annotations

from enum import StrEnum


class ToolName(StrEnum):
    """Canonical tool identifiers (match keys in the tool registry)."""

    PEN = "pen"
    CELL = "cell"
    SPRAY = "spray"
    PAINT_BUCKET = "paint_bucket"
    ERASER = "eraser"
    RECTANGLE = "rectangle"
    LINE = "line"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    LIGHT = "light"
    DARK = "dark"


# Mouse buttons as reported by Textual mouse events.
BUTTON_LEFT = 1
BUTTON_MIDDLE = 2
BUTTON_RIGHT = 3

# Brush size limits.
MIN_BRUSH_SIZE = 1
MAX_BRUSH_SIZE = 10
DEFAULT_BRUSH_SIZE = 2
# Shape tools (line/rectangle/circle/ellipse) get a lower brush size ceiling.
MAX_SHAPE_BRUSH_SIZE = 5

# Spray tool density limits.
MIN_SPRAY_DENSITY = 1
MAX_SPRAY_DENSITY = 5
DEFAULT_SPRAY_DENSITY = 3

# Light/dark tool lightness step limits (percent of HSL lightness).
MIN_LIGHT_STEP = 1
MAX_LIGHT_STEP = 10
DEFAULT_LIGHT_STEP = 5
DEFAULT_LIGHT_ACCUMULATE = False

# Shared overlay redraw rate for brush cursor and shape previews.
OVERLAY_FPS_LIMIT = 20.0
