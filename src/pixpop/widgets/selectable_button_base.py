"""Base class for selectable buttons used in picker widgets."""

from textual.widgets import Static


class SelectableButtonBase(Static):
    """Shared selection behavior for picker buttons."""

    def __init__(self, label: str) -> None:
        super().__init__(label)
        self._selected = False

    def select(self) -> None:
        """Mark this button as selected."""
        self._selected = True
        self.add_class("-selected")
        self.refresh()

    def deselect(self) -> None:
        """Mark this button as unselected."""
        self._selected = False
        self.remove_class("-selected")
        self.refresh()
