"""Application state dataclass for pixpop."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field

from textual.color import Color

from pixpop.tools import get_default_tool_name

DEFAULT_PEN_COLOR = "#d32f2f"


@dataclass
class AppState:
    """Centralized application state container.

    This class holds all mutable application state, making it easier to
    track changes and maintain separation of concerns between UI widgets.
    """

    pen_color: Color = field(default_factory=lambda: Color.parse(DEFAULT_PEN_COLOR))
    brush_size: int = 1
    spray_density: int = 3
    current_tool_name: str = field(default_factory=get_default_tool_name)
    normalized: bool = False

    def clone(self) -> AppState:
        """Create a deep copy of the current state."""
        return dataclasses.replace(self)
