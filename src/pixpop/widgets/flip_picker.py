"""Flip picker widget."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label

from pixpop.state import StateChanged
from pixpop.widgets.picker_base import PickerBase

INDICATOR_DOT = "\u25cf"


class FlipOptionButton(Button):
    """Button for a flip option."""

    class Pressed(StateChanged):
        """Flip option pressed message."""

        def __init__(self, mode: str) -> None:
            super().__init__()
            self.mode = mode

    def __init__(self, mode: str) -> None:
        super().__init__(INDICATOR_DOT)
        self.mode = mode
        self.can_focus = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle flip option press."""
        self.post_message(self.Pressed(self.mode))


class FlipPicker(PickerBase):
    """Flip action widget; emits FlipPressed with the chosen mode."""

    class FlipPressed(StateChanged):
        """Flip action message."""

        def __init__(self, mode: str, sender=None) -> None:
            super().__init__(sender)
            self.mode = mode

    MODES = [
        ("vertical", "Vertical"),
        ("horizontal", "Horizontal"),
        ("layer-vertical", "Layer Vertical"),
        ("layer-horizontal", "Layer Horizontal"),
    ]

    def __init__(self, workspace_id: str) -> None:
        super().__init__(
            workspace_id=workspace_id,
            picker_id="flip-picker",
            title="Flip",
            label="Flip:",
        )

    def compose(self) -> ComposeResult:
        """Create flip mode selection buttons."""
        with Vertical(classes="flip-panel"):
            for mode, label in self.MODES:
                with Horizontal(classes="flip-row"):
                    indicator = FlipOptionButton(mode)
                    indicator.add_class("flip-indicator")
                    yield indicator
                    yield Label(label, classes="flip-label")

    def on_flip_option_button_pressed(self, event: FlipOptionButton.Pressed) -> None:
        """Emit flip action for the pressed button."""
        self.post_message(self.FlipPressed(event.mode, sender=self))
