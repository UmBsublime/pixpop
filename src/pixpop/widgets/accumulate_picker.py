"""Accumulate toggle picker widget for the light/dark tools."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Label

from pixpop.constants import DEFAULT_LIGHT_ACCUMULATE
from pixpop.state import LightAccumulateChanged
from pixpop.widgets.normalize_picker import NormalizedToggleButton
from pixpop.widgets.picker_base import PickerBase


class LightAccumulatePicker(PickerBase):
    """Toggle whether light/dark strokes re-apply to visited pixels."""

    def __init__(self, workspace_id: str) -> None:
        super().__init__(
            workspace_id=workspace_id,
            picker_id="light-accumulate-picker",
            title="Accumulate",
        )
        self._value = DEFAULT_LIGHT_ACCUMULATE

    def compose(self) -> ComposeResult:
        with Vertical(classes="accumulate-panel"):
            with Horizontal(classes="accumulate-row"):
                indicator = NormalizedToggleButton(self._value)
                indicator.add_class("accumulate-indicator")
                yield indicator
                yield Label("Accumulate", classes="accumulate-label")

    def _get_toggle_button(self) -> NormalizedToggleButton:
        return self.query_one(NormalizedToggleButton)

    def on_button_pressed(self, event) -> None:
        if not isinstance(event.button, NormalizedToggleButton):
            return
        self.set_value(not self._value)

    def set_value(self, value: bool, emit: bool = True) -> None:
        """Set the accumulate toggle state."""
        self._value = value
        self._get_toggle_button().set_enabled(value)
        if emit:
            self.post_message(LightAccumulateChanged(value, sender=self))
