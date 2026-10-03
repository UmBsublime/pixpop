"""Color picker dialog screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.color import Color
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static
from textual_colorpicker import ColorPicker


class ColorPickerDialog(ModalScreen[Color | None]):
    """Modal color picker, defaulting to the current pen color.

    Enter confirms the picked color; Escape cancels. Enter is a priority
    binding: the picker's inner Inputs bind Enter themselves (and swallow
    their Submitted messages), which would otherwise shadow this binding.
    """

    CSS_PATH = "../styles/screens/color_picker_dialog.tcss"

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        Binding("enter", "confirm", "Confirm", priority=True),
    ]

    def __init__(self, color: Color) -> None:
        super().__init__()
        self._color = color.clamped

    def compose(self) -> ComposeResult:
        with Vertical(id="color-picker-dialog"):
            yield Static("Pick a color", id="color-picker-title")
            yield ColorPicker(self._color)
            yield Static(
                "Enter to confirm, Esc to cancel",
                id="color-picker-hint",
            )

    def on_color_picker_changed(self, event: ColorPicker.Changed) -> None:
        """Track the latest picked color."""
        self._color = event.color

    def action_confirm(self) -> None:
        self.dismiss(self._color)

    def action_cancel(self) -> None:
        self.dismiss(None)
