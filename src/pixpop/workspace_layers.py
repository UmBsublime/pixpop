"""Layer management helpers for the workspace."""

from __future__ import annotations

from typing import Callable

from pixpop.canvas import PaintCanvas


class LayerController:
    """Wrapper around PaintCanvas to centralize layer operations."""

    def __init__(
        self,
        get_canvas: Callable[[], PaintCanvas],
        sync_layers: Callable[[PaintCanvas | None], None],
    ) -> None:
        self._get_canvas = get_canvas
        self._sync_layers = sync_layers

    def _canvas(self) -> PaintCanvas:
        return self._get_canvas()

    def get_layers(self) -> list[tuple[str, bool]]:
        """Return layers as (name, visible) tuples."""
        return self._canvas().get_layers()

    def add_layer(self) -> bool:
        """Add a new layer and sync UI."""
        canvas = self._canvas()
        if not canvas.add_layer():
            return False
        self._sync_layers(canvas)
        return True

    def remove_active_layer(self) -> bool:
        """Remove the active layer and sync UI."""
        canvas = self._canvas()
        if not canvas.remove_layer(canvas.active_layer_index):
            return False
        self._sync_layers(canvas)
        return True

    def set_active(self, index: int) -> None:
        """Set the active layer and sync UI."""
        canvas = self._canvas()
        canvas.set_active_layer(index)
        self._sync_layers(canvas)

    def set_visibility(self, index: int, visible: bool) -> None:
        """Set layer visibility and sync UI."""
        canvas = self._canvas()
        canvas.set_layer_visibility(index, visible)
        self._sync_layers(canvas)

    def toggle_visibility(self, index: int | None = None) -> None:
        """Toggle layer visibility and sync UI."""
        canvas = self._canvas()
        if index is None:
            index = canvas.active_layer_index
        canvas.toggle_layer_visibility(index)
        self._sync_layers(canvas)

    def rename(self, index: int, name: str) -> None:
        """Rename a layer and sync UI."""
        canvas = self._canvas()
        canvas.rename_layer(index, name)
        self._sync_layers(canvas)

    def move_up(self, index: int | None = None) -> bool:
        """Move a layer up and sync UI."""
        canvas = self._canvas()
        if index is None:
            index = canvas.active_layer_index
        if not canvas.move_layer_up(index):
            return False
        self._sync_layers(canvas)
        return True

    def move_down(self, index: int | None = None) -> bool:
        """Move a layer down and sync UI."""
        canvas = self._canvas()
        if index is None:
            index = canvas.active_layer_index
        if not canvas.move_layer_down(index):
            return False
        self._sync_layers(canvas)
        return True

    def cycle_up(self) -> None:
        """Select the previous layer and sync UI."""
        self._cycle(-1)

    def cycle_down(self) -> None:
        """Select the next layer and sync UI."""
        self._cycle(1)

    def _cycle(self, delta: int) -> None:
        """Move the active layer selection by delta, clamped to bounds.

        Layer cycling intentionally clamps at the edges rather than wrapping
        (unlike tab cycling) so repeated presses don't "spin" the list.
        """
        canvas = self._canvas()
        layers = canvas.get_layers()
        if len(layers) <= 1:
            return
        next_index = min(max(canvas.active_layer_index + delta, 0), len(layers) - 1)
        if next_index == canvas.active_layer_index:
            return
        canvas.set_active_layer(next_index)
        self._sync_layers(canvas)
