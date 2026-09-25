"""Normalized toggle picker widget."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label

from pixpop.state import NormalizedChanged
from pixpop.widgets.picker_base import PickerBase

INDICATOR_DOT = "\u25cf"


class NormalizedToggleButton(Button):
    """Toggle button for normalized snapping."""

    def __init__(self, enabled: bool) -> None:
        super().__init__(INDICATOR_DOT)
        self.enabled = enabled
        self.set_enabled(enabled)
        self.can_focus = False

    def set_enabled(self, enabled: bool) -> None:
        """Apply the enabled/disabled visual state."""
        self.enabled = enabled
        self.remove_class("-enabled")
        self.remove_class("-disabled")
        self.add_class("-enabled" if enabled else "-disabled")


class NormalizedPicker(PickerBase):
    """Normalized toggle widget to control line/circle/ellipse/spray snapping."""

    def __init__(self, workspace_id: str, value: bool) -> None:
        super().__init__(
            workspace_id=workspace_id,
            picker_id="normalized-picker",
            title="Normalized",
        )
        self._value = value

    def compose(self) -> ComposeResult:
        with Vertical(classes="normalized-panel"):
            with Horizontal(classes="normalized-row"):
                indicator = NormalizedToggleButton(self._value)
                indicator.add_class("normalized-indicator")
                yield indicator
                yield Label("Normalized", classes="normalized-label")

    def _get_toggle_button(self) -> NormalizedToggleButton:
        return self.query_one(NormalizedToggleButton)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if not isinstance(event.button, NormalizedToggleButton):
            return
        self.set_value(not self._value)

    def set_value(self, value: bool, emit: bool = True) -> None:
        """Set the normalized toggle state."""
        self._value = value
        self._get_toggle_button().set_enabled(value)
        if emit:
            self.post_message(NormalizedChanged(value, sender=self))
