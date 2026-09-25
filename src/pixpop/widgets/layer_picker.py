"""Layer picker widget."""

from __future__ import annotations

from contextlib import contextmanager

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label, ListItem, ListView

from pixpop.state import StateChanged
from pixpop.widgets.picker_base import PickerBase

INDICATOR_DOT = "\u25cf"


class LayerVisibilityButton(Button):
    """Visibility toggle for a layer."""

    def __init__(self, index: int, visible: bool) -> None:
        super().__init__(INDICATOR_DOT)
        self.layer_index = index
        self.layer_visible = visible
        self.set_visible_state(visible)
        self.can_focus = False

    def set_visible_state(self, visible: bool) -> None:
        """Apply the visible/hidden visual state."""
        self.layer_visible = visible
        self.remove_class("-visible")
        self.remove_class("-hidden")
        self.add_class("-visible" if visible else "-hidden")


class LayerItem(ListItem):
    """List item representing a single layer."""

    def __init__(self, index: int, name: str, visible: bool) -> None:
        super().__init__()
        self.layer_index = index
        self.layer_name = name
        self.layer_visible = visible
        self.can_focus = False

    def compose(self) -> ComposeResult:
        with Horizontal(classes="layer-row"):
            indicator = LayerVisibilityButton(self.layer_index, self.layer_visible)
            indicator.add_class("layer-visible-indicator")
            yield indicator
            yield Label(self.layer_name, classes="layer-label")


class LayerPicker(PickerBase):
    """Layer selection and visibility panel."""

    class LayerSelected(StateChanged):
        """Message emitted when a layer is selected."""

        def __init__(self, index: int, sender=None) -> None:
            super().__init__(sender)
            self.index = index

    class LayerVisibilityToggled(StateChanged):
        """Message emitted when a layer visibility changes."""

        def __init__(self, index: int, visible: bool, sender=None) -> None:
            super().__init__(sender)
            self.index = index
            self.visible = visible

    def __init__(self, workspace_id: str) -> None:
        super().__init__(
            workspace_id=workspace_id,
            picker_id="layer-picker",
            title="Layers",
        )
        self._suppress_events = False

    @contextmanager
    def _events_suppressed(self):
        """Context manager to suppress selection events during bulk updates."""
        self._suppress_events = True
        try:
            yield
        finally:
            self._suppress_events = False

    def compose(self) -> ComposeResult:
        with Vertical(classes="layer-panel"):
            yield ListView(
                id=f"layer-list-{self.workspace_id}",
                classes="layer-list",
            )

    def set_layers(self, layers: list[tuple[str, bool]], active_index: int) -> None:
        """Replace the list of layers shown in the UI."""
        list_view = self.query_one(f"#layer-list-{self.workspace_id}", ListView)
        with self._events_suppressed():
            list_view.clear()
            for index, (name, visible) in enumerate(layers):
                item = LayerItem(index=index, name=name, visible=visible)
                if index == active_index:
                    item.add_class("active-layer")
                list_view.append(item)
            if layers:
                list_view.index = max(0, min(active_index, len(layers) - 1))
                list_view.highlighted = list_view.index

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle list selection changes."""
        if self._suppress_events:
            return
        if event.list_view.id != f"layer-list-{self.workspace_id}":
            return
        item = event.item
        if not isinstance(item, LayerItem):
            return
        self.post_message(self.LayerSelected(item.layer_index, sender=self))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Toggle visibility when pressing the indicator button."""
        if self._suppress_events:
            return
        if not isinstance(event.button, LayerVisibilityButton):
            return
        self.post_message(
            self.LayerVisibilityToggled(
                event.button.layer_index, not event.button.layer_visible, sender=self
            )
        )
