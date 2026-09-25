"""Base picker widget with shared styling and visibility behavior."""

from textual.widgets import Static


class PickerBase(Static):
    """Shared base class for picker widgets."""

    def __init__(
        self,
        workspace_id: str,
        picker_id: str,
        title: str,
        label: str | None = None,
    ) -> None:
        super().__init__(label or "")
        self.workspace_id = workspace_id
        self.id = f"{picker_id}-{workspace_id}"
        self.border_title = title
        self.border_title_align = "left"
        self.add_class("picker-panel")

    def set_visible(self, visible: bool) -> None:
        """Toggle picker visibility without removing it from layout."""
        if visible:
            self.remove_class("invisible")
        else:
            self.add_class("invisible")
