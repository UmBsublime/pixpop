"""Brush size picker widget."""

from __future__ import annotations

from pixpop.constants import MAX_BRUSH_SIZE, MIN_BRUSH_SIZE
from pixpop.state import BrushSizeChanged
from pixpop.widgets.single_select_picker import SingleSelectPicker

_BRUSH_SIZES = list(range(MIN_BRUSH_SIZE, MAX_BRUSH_SIZE + 1))


class BrushSizePicker(SingleSelectPicker[int]):
    """Brush size selection widget for changing pen/eraser thickness."""

    def __init__(self, workspace_id: str) -> None:
        super().__init__(
            workspace_id=workspace_id,
            picker_id="brush-size-picker",
            title="Brush Size",
            label="Brush Size:",
            values=_BRUSH_SIZES,
            label_fn=str,
            build_changed_message=lambda size: BrushSizeChanged(size, sender=self),
            default=MIN_BRUSH_SIZE,
            grid_class="brush-grid",
        )

    def set_max_size(self, max_size: int) -> None:
        """Show only buttons up to the given maximum size (per-tool limit)."""
        self.set_visible_values(range(MIN_BRUSH_SIZE, max_size + 1))

    # Backwards-compatible API used by workspace and tests.
    def select_size(self, size: int, emit: bool = True) -> None:
        """Select a brush size programmatically (e.g., from keyboard shortcuts)."""
        self.select_value(size, emit=emit)

    @property
    def current_size(self) -> int:
        return self.current_value
