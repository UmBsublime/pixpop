"""Canvas size dialog for new tabs."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, Static

from pixpop.config import AppConfig


class NewTabDialog(ModalScreen[tuple[int, int] | None]):
    """Modal dialog asking for the new canvas's size in pixels.

    Enter submits via either Input's Submitted message; Escape cancels.
    Values are validated against the configured min/max canvas sizes.
    """

    CSS_PATH = "../styles/screens/new_tab_dialog.tcss"

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, width: int, height: int, config: AppConfig) -> None:
        super().__init__()
        self._width = width
        self._height = height
        self._config = config

    def compose(self) -> ComposeResult:
        with Static(id="new-tab-dialog"):
            yield Static("New canvas", id="new-tab-title")
            yield Static("Width (px)", classes="new-tab-label")
            yield Input(
                value=str(self._width),
                id="width-input",
                classes="new-tab-input",
            )
            yield Static("Height (px)", classes="new-tab-label")
            yield Input(
                value=str(self._height),
                id="height-input",
                classes="new-tab-input",
            )
            yield Static("", id="new-tab-error")
            yield Static(
                "Enter to confirm, Esc to cancel",
                id="new-tab-hint",
            )

    def on_mount(self) -> None:
        width_input = self.query_one("#width-input", Input)
        width_input.focus()
        width_input.action_select_all()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id not in ("width-input", "height-input"):
            return
        width_raw = self.query_one("#width-input", Input).value.strip()
        height_raw = self.query_one("#height-input", Input).value.strip()
        try:
            width = int(width_raw)
            height = int(height_raw)
        except ValueError:
            self._show_error("Width and height must be whole numbers.")
            return
        cfg = self._config
        if not (cfg.min_canvas_width <= width <= cfg.max_canvas_width):
            self._show_error(
                f"Width must be between {cfg.min_canvas_width} and "
                f"{cfg.max_canvas_width}."
            )
            return
        if not (cfg.min_canvas_height <= height <= cfg.max_canvas_height):
            self._show_error(
                f"Height must be between {cfg.min_canvas_height} and "
                f"{cfg.max_canvas_height}."
            )
            return
        self.dismiss((width, height))

    def _show_error(self, message: str) -> None:
        self.query_one("#new-tab-error", Static).update(message)
