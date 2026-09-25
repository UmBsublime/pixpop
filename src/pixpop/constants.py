"""Shared constants for pixpop — single source of truth for magic values."""

from __future__ import annotations

from enum import StrEnum


class ToolName(StrEnum):
    """Canonical tool identifiers (match keys in the tool registry)."""

    PEN = "pen"
    FINE_PEN = "fine-pen"
    SPRAY = "spray"
    PAINT_BUCKET = "paint_bucket"
    ERASER = "eraser"
    RECTANGLE = "rectangle"
    LINE = "line"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"


# Mouse buttons as reported by Textual mouse events.
BUTTON_LEFT = 1
BUTTON_MIDDLE = 2
BUTTON_RIGHT = 3

# Brush size limits.
MIN_BRUSH_SIZE = 1
MAX_BRUSH_SIZE = 5

# Spray tool density limits.
MIN_SPRAY_DENSITY = 1
MAX_SPRAY_DENSITY = 5
DEFAULT_SPRAY_DENSITY = 3

# Shared overlay redraw rate for brush cursor and shape previews.
OVERLAY_FPS_LIMIT = 20.0
