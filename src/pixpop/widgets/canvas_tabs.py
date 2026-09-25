"""Canvas tab container widget."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Static, TabbedContent, TabPane, Tabs


class CanvasTabs(Static):
    """Container that hosts the tabbed canvases."""

    def __init__(self, tabs_id: str, initial_pane: TabPane) -> None:
        super().__init__()
        self._tabs_id = tabs_id
        self._initial_pane = initial_pane

    def compose(self) -> ComposeResult:
        with TabbedContent(id=self._tabs_id):
            yield self._initial_pane

    def on_mount(self) -> None:
        """Ensure tab widgets are not focusable."""
        tabbed = self.query_one(TabbedContent)
        tabbed.can_focus = False
        tabbed.query_one(Tabs).can_focus = False
