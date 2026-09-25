"""Spray density picker widget."""

from __future__ import annotations

from pixpop.constants import (
    DEFAULT_SPRAY_DENSITY,
    MAX_SPRAY_DENSITY,
    MIN_SPRAY_DENSITY,
)
from pixpop.state import SprayDensityChanged
from pixpop.widgets.single_select_picker import SingleSelectPicker

_DENSITIES = list(range(MIN_SPRAY_DENSITY, MAX_SPRAY_DENSITY + 1))


class SprayDensityPicker(SingleSelectPicker[int]):
    """Spray density selection widget for configuring spray intensity."""

    def __init__(self, workspace_id: str) -> None:
        super().__init__(
            workspace_id=workspace_id,
            picker_id="spray-density-picker",
            title="Spray Density",
            label="Spray Intensity:",
            values=_DENSITIES,
            label_fn=str,
            build_changed_message=lambda d: SprayDensityChanged(d, sender=self),
            default=DEFAULT_SPRAY_DENSITY,
            grid_class="spray-grid",
        )

    # Backwards-compatible API used by workspace and tests.
    def select_density(self, density: int, emit: bool = True) -> None:
        """Select a spray density programmatically."""
        self.select_value(density, emit=emit)

    @property
    def current_density(self) -> int:
        return self.current_value
