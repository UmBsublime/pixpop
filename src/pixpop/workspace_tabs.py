"""Tab management helpers for the workspace."""

from __future__ import annotations

from typing import Callable

from textual.css.query import NoMatches
from textual.widgets import TabbedContent, TabPane, Tabs


class TabManager:
    """Wrapper around TabbedContent to centralize tab operations."""

    def __init__(
        self,
        get_tabbed_content: Callable[[], TabbedContent],
        get_tabs: Callable[[], Tabs],
    ) -> None:
        self._get_tabbed_content = get_tabbed_content
        self._get_tabs = get_tabs

    def _tabbed_content(self) -> TabbedContent:
        return self._get_tabbed_content()

    def _tabs_widget(self) -> Tabs:
        return self._get_tabs()

    def list_panes(self) -> list[TabPane]:
        """Return all tab panes in order."""
        return list(self._tabbed_content().query(TabPane))

    def active_pane(self) -> TabPane | None:
        """Return the active pane if available."""
        tabbed = self._tabbed_content()
        if not tabbed.active:
            return None
        try:
            return tabbed.active_pane
        except NoMatches:
            # Active ID refers to a pane that no longer exists.
            return None

    def active_index(self) -> int:
        """Return the active tab index, or 0 if none."""
        panes = self.list_panes()
        active_pane = self.active_pane()
        if active_pane in panes:
            return panes.index(active_pane)
        return 0

    def active_name(self) -> str | None:
        """Return the active pane title if available."""
        active_pane = self.active_pane()
        if active_pane is None:
            return None
        title = getattr(active_pane, "title", None)
        if isinstance(title, str) and title:
            return title
        return None

    def add_pane(self, pane: TabPane, *, activate: bool = False) -> None:
        """Add a pane to the tab container."""
        tabbed = self._tabbed_content()
        tabbed.add_pane(pane)
        if activate:
            tabbed.active = pane.id

    def remove_pane(self, pane_id: str) -> None:
        """Remove a pane by ID."""
        self._tabbed_content().remove_pane(pane_id)

    def clear(self) -> None:
        """Remove all panes and reset active tab."""
        tabbed = self._tabbed_content()
        tabbed.active = None
        for pane in self.list_panes():
            tabbed.remove_pane(pane.id)

    def set_active_by_id(self, pane_id: str) -> None:
        """Set the active tab by pane ID."""
        self._tabbed_content().active = pane_id

    def set_active_by_index(self, index: int) -> None:
        """Set the active tab by index."""
        panes = self.list_panes()
        if not panes:
            return
        target_index = min(max(index, 0), len(panes) - 1)
        self._tabbed_content().active = panes[target_index].id

    def set_active_by_name(self, name: str | None) -> bool:
        """Set the active tab by label, returning True if found."""
        if not name:
            return False
        for pane in self.list_panes():
            if pane.title == name:
                self._tabbed_content().active = pane.id
                return True
        return False

    def set_tab_label(self, pane: TabPane, name: str) -> None:
        """Apply a label to the tab and pane."""
        # get_tab lives on TabbedContent (it queries the internal ContentTabs).
        try:
            tab = self._tabbed_content().get_tab(pane.id)
        except NoMatches, ValueError:
            # Tab strip entry not mounted yet, or pane id is missing.
            tab = None
        if tab is not None:
            tab.label = name
        pane.title = name
