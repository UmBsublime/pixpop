"""Rename dialog screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, Static


class RenameDialog(ModalScreen[str | None]):
    """Generic modal rename dialog.

    Enter submits via the Input's own Submitted message; Escape cancels.
    """

    CSS_PATH = "../styles/screens/rename_dialog.tcss"

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, title: str, value: str) -> None:
        super().__init__()
        self._title = title
        self._value = value

    def compose(self) -> ComposeResult:
        with Static(id="rename-dialog"):
            yield Static(self._title, id="rename-title")
            yield Input(
                value=self._value,
                id="rename-input",
                classes="rename-input",
            )
            yield Static(
                "Enter to confirm, Esc to cancel",
                id="rename-hint",
            )

    def on_mount(self) -> None:
        input_widget = self.query_one("#rename-input", Input)
        input_widget.focus()
        input_widget.action_select_all()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "rename-input":
            return
        value = event.input.value.strip()
        if not value:
            self.dismiss(None)
            return
        self.dismiss(value)
