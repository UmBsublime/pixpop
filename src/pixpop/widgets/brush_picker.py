"""Brush size picker widget."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label
from textual_slider import Slider

from pixpop.constants import DEFAULT_BRUSH_SIZE, MAX_BRUSH_SIZE, MIN_BRUSH_SIZE
from pixpop.state import BrushSizeChanged
from pixpop.widgets.picker_base import PickerBase


class BrushSizePicker(PickerBase):
    """Slider-based picker for pen/eraser/etc. brush thickness."""

    def __init__(self, workspace_id: str) -> None:
        super().__init__(
            workspace_id=workspace_id,
            picker_id="brush-size-picker",
            title="Brush Size",
        )
        self.current_size = DEFAULT_BRUSH_SIZE
        self._max_size = MAX_BRUSH_SIZE

    def compose(self) -> ComposeResult:
        with Horizontal(classes="brush-size-row"):
            yield Slider(
                MIN_BRUSH_SIZE,
                self._max_size,
                value=self.current_size,
                classes="brush-size-slider",
            )
            yield Label(self._label_text(), classes="brush-size-value")

    def on_mount(self) -> None:
        """Suppress the initial Changed message emitted before layout."""
        self._get_slider().value = self.current_size

    def on_slider_changed(self, event: Slider.Changed) -> None:
        """Handle slider movements by selecting the new size.

        Only forward user-driven changes: when the slider value already
        matches the picker's current size, the event is an echo of our own
        programmatic ``slider.value`` assignment, so ignore it.
        """
        if event.value != self.current_size:
            self.select_size(event.value)

    def select_size(self, size: int, emit: bool = True) -> None:
        """Select a brush size programmatically (e.g., from keyboard shortcuts)."""
        size = max(MIN_BRUSH_SIZE, min(self._max_size, size))
        self.current_size = size
        slider = self._get_slider()
        if slider.value != size:
            slider.value = size
        self._get_value_label().update(self._label_text())
        if emit:
            self.post_message(BrushSizeChanged(size, sender=self))

    def set_max_size(self, max_size: int) -> None:
        """Set the per-tool upper brush size limit shown by the slider."""
        self._max_size = max(MIN_BRUSH_SIZE, min(MAX_BRUSH_SIZE, max_size))
        slider = self._get_slider()
        if slider.max != self._max_size:
            slider.max = self._max_size
        # Re-clamp the current selection against the new limit.
        self.select_size(self.current_size, emit=False)

    def _label_text(self) -> str:
        return str(self.current_size)

    def _get_slider(self) -> Slider:
        return self.query_one(Slider)

    def _get_value_label(self) -> Label:
        return self.query_one(Label)
