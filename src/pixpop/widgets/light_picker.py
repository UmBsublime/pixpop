"""Lightness step picker widget for the light/dark tools."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label
from textual_slider import Slider

from pixpop.constants import (
    DEFAULT_LIGHT_STEP,
    MAX_LIGHT_STEP,
    MIN_LIGHT_STEP,
)
from pixpop.state import LightStepChanged
from pixpop.widgets.picker_base import PickerBase


class LightStepPicker(PickerBase):
    """Slider-based picker for the light/dark lightness step (percent)."""

    def __init__(self, workspace_id: str) -> None:
        super().__init__(
            workspace_id=workspace_id,
            picker_id="light-step-picker",
            title="Light",
        )
        self.current_step = DEFAULT_LIGHT_STEP

    def compose(self) -> ComposeResult:
        with Horizontal(classes="light-step-row"):
            yield Slider(
                MIN_LIGHT_STEP,
                MAX_LIGHT_STEP,
                value=self.current_step,
                classes="light-step-slider",
            )
            yield Label(self._label_text(), classes="light-step-value")

    def on_mount(self) -> None:
        """Suppress the initial Changed message emitted before layout."""
        self._get_slider().value = self.current_step

    def on_slider_changed(self, event: Slider.Changed) -> None:
        """Handle slider movements by selecting the new step."""
        self.select_step(event.value)

    def select_step(self, step: int, emit: bool = True) -> None:
        """Select a lightness step programmatically."""
        step = max(MIN_LIGHT_STEP, min(MAX_LIGHT_STEP, step))
        self.current_step = step
        slider = self._get_slider()
        if slider.value != step:
            slider.value = step
        self._get_value_label().update(self._label_text())
        if emit:
            self.post_message(LightStepChanged(step, sender=self))

    def _label_text(self) -> str:
        return str(self.current_step)

    def _get_slider(self) -> Slider:
        return self.query_one(Slider)

    def _get_value_label(self) -> Label:
        return self.query_one(Label)
