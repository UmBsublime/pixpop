"""Generic single-select grid picker used by brush/spray/tool pickers."""

from __future__ import annotations

from typing import Callable, Generic, Iterable, TypeVar

from textual.app import ComposeResult
from textual.containers import Grid
from textual.events import Click
from textual.message import Message

from pixpop.widgets.picker_base import PickerBase
from pixpop.widgets.selectable_button_base import SelectableButtonBase

T = TypeVar("T")


class ValueButton(SelectableButtonBase, Generic[T]):
    """A selectable button carrying an arbitrary value."""

    class Selected(Message):
        """Posted when the button is clicked."""

        def __init__(self, button: "ValueButton") -> None:
            super().__init__()
            self.button = button

    def __init__(self, value: T, label: str) -> None:
        super().__init__(label)
        self.value = value
        self.add_class("value-button")

    def on_click(self, event: Click) -> None:
        self.post_message(self.Selected(self))


class SingleSelectPicker(PickerBase, Generic[T]):
    """A grid of buttons where exactly one value is selected.

    Subclasses (or callers) provide the values, a label function, and a
    ``build_changed_message`` factory that turns a selected value into the
    picker-specific ``*Changed`` message to emit.
    """

    def __init__(
        self,
        workspace_id: str,
        picker_id: str,
        title: str,
        label: str,
        values: list[T],
        label_fn: Callable[[T], str],
        build_changed_message: Callable[[T], Message],
        default: T,
        grid_class: str,
        button_tooltip: Callable[[T], str] | None = None,
    ) -> None:
        super().__init__(
            workspace_id=workspace_id, picker_id=picker_id, title=title, label=label
        )
        self._values = values
        self._label_fn = label_fn
        self._build_changed_message = build_changed_message
        self._button_tooltip = button_tooltip
        self._grid_class = grid_class
        self.current_value = default
        self._buttons: list[ValueButton[T]] = [
            ValueButton(value, self._label_fn(value)) for value in values
        ]

    def compose(self) -> ComposeResult:
        """Create the grid of value buttons."""
        with Grid(classes=self._grid_class):
            for button in self._buttons:
                if self._button_tooltip is not None:
                    button.tooltip = self._button_tooltip(button.value)
                yield button

    def on_mount(self) -> None:
        """Apply the initial selection once buttons are in the DOM."""
        self._apply_selection(self.current_value)

    def on_value_button_selected(self, event: ValueButton.Selected) -> None:
        """Handle a button click by selecting its value."""
        self.select_value(event.button.value)

    def set_visible_values(self, values: Iterable[T]) -> None:
        """Show only the buttons whose value is in the given set.

        Buttons for other values are hidden and removed from layout; the
        remaining buttons reflow within the grid.
        """
        visible = set(values)
        for button in self._buttons:
            button.display = button.value in visible
        self._apply_selection(self.current_value)

    def select_value(self, value: T, emit: bool = True) -> None:
        """Select a value programmatically.

        Args:
            value: The value to select.
            emit: Whether to emit the changed message.

        Raises:
            ValueError: If the value is not one of the picker's values.
        """
        if value not in self._values:
            raise ValueError(f"Unknown value for {self.border_title!r}: {value!r}")
        self._apply_selection(value)
        self.current_value = value
        if emit:
            self.post_message(self._build_changed_message(value))

    def _apply_selection(self, value: T) -> None:
        for button in self._buttons:
            if button.value == value:
                button.select()
            else:
                button.deselect()
