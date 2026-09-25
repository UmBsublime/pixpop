"""Message classes for state change events."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.color import Color
from textual.message import Message

if TYPE_CHECKING:
    from textual.widget import Widget


class StateChanged(Message):
    """Base for state-change messages, carrying the emitting widget.

    The workspace uses ``sender`` to scope events to the workspace instance
    that produced them (multiple workspaces can coexist).
    """

    def __init__(self, sender: Widget | None = None) -> None:
        super().__init__()
        self.sender: Widget | None = sender


class PenColorChanged(StateChanged):
    """Message emitted when pen color selection changes."""

    def __init__(
        self, color_name: str, color: Color, sender: Widget | None = None
    ) -> None:
        super().__init__(sender)
        self.color_name = color_name
        self.color = color


class ToolChanged(StateChanged):
    """Message emitted when the active tool changes."""

    def __init__(self, tool_name: str, sender: Widget | None = None) -> None:
        super().__init__(sender)
        self.tool_name = tool_name


class BrushSizeChanged(StateChanged):
    """Message emitted when brush size changes."""

    def __init__(self, size: int, sender: Widget | None = None) -> None:
        super().__init__(sender)
        self.size = size


class SprayDensityChanged(StateChanged):
    """Message emitted when spray density changes."""

    def __init__(self, density: int, sender: Widget | None = None) -> None:
        super().__init__(sender)
        self.density = density


class NormalizedChanged(StateChanged):
    """Message emitted when normalized toggle changes."""

    def __init__(self, value: bool, sender: Widget | None = None) -> None:
        super().__init__(sender)
        self.value = value
