"""Color picker widget with color swatches."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.color import Color as TextualColor
from textual.containers import Grid
from textual.events import Click
from textual.message import Message
from textual.widgets import Select

from pixpop.config import AppConfig
from pixpop.palettes import load_palettes
from pixpop.state import PenColorChanged
from pixpop.widgets.picker_base import PickerBase
from pixpop.widgets.selectable_button_base import SelectableButtonBase


class ColorSwatch(SelectableButtonBase):
    """Custom color selection widget displaying as a colored rectangle."""

    class Selected(Message):
        """Color selection message."""

        def __init__(self, color_name: str, color: TextualColor) -> None:
            super().__init__()
            self.color_name = color_name
            self.color = color

    def __init__(self, color_name: str, color_hex: str) -> None:
        super().__init__("")
        self.color_name = color_name
        self.color_hex = color_hex
        self.color = TextualColor.parse(color_hex)

    def render(self) -> str:
        """Render the color widget as a colored block."""
        row = f"[on {self.color_hex}]    [/]"
        return f"{row}\n{row}"

    def on_click(self, event: Click) -> None:
        """Handle color selection."""
        self.post_message(self.Selected(self.color_name, self.color))


class ColorPicker(PickerBase):
    """Color selection widget with palette swatches and recent colors."""

    def __init__(
        self,
        workspace_id: str,
        config: AppConfig | None = None,
    ) -> None:
        super().__init__(
            workspace_id=workspace_id,
            picker_id="color-picker",
            title="Colors",
            label="",
        )
        cfg = config if config is not None else AppConfig()
        self._max_recent_colors = cfg.recent_colors_max
        self._default_palette_name = cfg.default_palette_name
        # Recent colors are per-picker instance (not shared across workspaces).
        self._recent_colors: list[str] = []
        self._color_widgets: list[ColorSwatch] = []
        self._recent_widgets: list[ColorSwatch] = []
        self._palettes, self._palette_labels = load_palettes()
        self._palette_name = (
            cfg.default_palette_name
            if cfg.default_palette_name in self._palettes
            else next(iter(self._palettes))
        )
        palette_entries = self._palettes.get(self._palette_name, [])
        first_hex = palette_entries[0] if palette_entries else "#d32f2f"
        self.current_color = first_hex
        self._current_color_value = TextualColor.parse(first_hex)

    def compose(self) -> ComposeResult:
        """Create color selection widgets."""
        options = [
            (self._palette_labels.get(key, key.title()), key)
            for key in self._sorted_palette_keys()
        ]
        yield Select(
            options=options,
            value=self._palette_name,
            id=f"palette-select-{self.workspace_id}",
            classes="palette-select",
        )
        with Grid(
            classes="color-grid",
            id=f"color-grid-{self.workspace_id}",
        ):
            for hex_code in self._palettes[self._palette_name]:
                color_widget = ColorSwatch(hex_code, hex_code)
                self._color_widgets.append(color_widget)
                yield color_widget
        with Grid(
            classes="recent-grid recent-section",
            id=f"recent-grid-{self.workspace_id}",
        ):
            pass

    def on_mount(self) -> None:
        self._rebuild_recent_grid()
        self._apply_selection_to_widgets()
        self.query_one(f"#palette-select-{self.workspace_id}").can_focus = False

    def _sorted_palette_keys(self) -> list[str]:
        default = self._default_palette_name
        keys = [key for key in self._palettes.keys() if key != default]
        keys.sort(key=self._palette_sort_key)
        return [default] + keys if default in self._palettes else keys

    def _palette_sort_key(self, key: str) -> tuple[int, str]:
        suffix = key.rsplit("-", 1)[-1]
        try:
            number = int(suffix)
        except ValueError:
            number = 0
        return (number, key)

    def _rebuild_grid(
        self, grid_id_suffix: str, hex_codes: list[str], target: list[ColorSwatch]
    ) -> None:
        """Rebuild a swatch grid from hex codes into the target widget list."""
        grid = self.query_one(f"#{grid_id_suffix}-{self.workspace_id}", Grid)
        grid.remove_children()
        target.clear()
        for hex_code in hex_codes:
            swatch = ColorSwatch(hex_code, hex_code)
            target.append(swatch)
            grid.mount(swatch)
        self._apply_selection_to_widgets()

    def _rebuild_palette_grid(self) -> None:
        self._rebuild_grid(
            "color-grid", self._palettes[self._palette_name], self._color_widgets
        )

    def _rebuild_recent_grid(self) -> None:
        self._rebuild_grid("recent-grid", self._recent_colors, self._recent_widgets)
        self._update_recent_visibility()

    def _update_recent_visibility(self) -> None:
        grid = self.query_one(f"#recent-grid-{self.workspace_id}", Grid)
        if self._recent_colors:
            grid.remove_class("invisible")
        else:
            grid.add_class("invisible")

    def _apply_selection_to_widgets(self) -> None:
        target_hex = self._current_color_value.hex.lower()
        for widget in self._color_widgets + self._recent_widgets:
            if widget.color_hex.lower() == target_hex:
                widget.select()
            else:
                widget.deselect()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != f"palette-select-{self.workspace_id}":
            return
        if event.value not in self._palettes:
            return
        self._palette_name = event.value
        self._rebuild_palette_grid()

    def on_color_swatch_selected(self, event: ColorSwatch.Selected) -> None:
        """Handle color selection from a swatch."""
        self.current_color = event.color_name
        self._current_color_value = event.color
        self._apply_selection_to_widgets()
        self._push_recent(event.color_name)
        self._emit(event.color_name, event.color)

    def select_color(self, color: TextualColor, emit: bool = True) -> None:
        """Programmatically select a color (for eyedropper tool).

        Args:
            color: The color to select.
            emit: Whether to emit a PenColorChanged message.
        """
        color_hex = color.hex
        self.current_color = color_hex
        self._current_color_value = color
        self._apply_selection_to_widgets()

        if emit:
            self._push_recent(color_hex)
            self._emit(color_hex, color)

    def _emit(self, color_name: str, color: TextualColor) -> None:
        """Emit a PenColorChanged message for the parent workspace."""
        self.post_message(PenColorChanged(color_name, color, sender=self))

    def get_palette_state(self) -> tuple[str, TextualColor]:
        """Return the current palette name and selected color."""
        return self._palette_name, self._current_color_value

    def set_palette_state(
        self, palette_name: str, selected_color: TextualColor, emit: bool = True
    ) -> None:
        """Set the active palette and selected color."""
        target_name = (
            palette_name
            if palette_name in self._palettes
            else self._default_palette_name
        )
        if target_name != self._palette_name:
            self._palette_name = target_name
            palette_select = self.query_one(
                f"#palette-select-{self.workspace_id}", Select
            )
            palette_select.value = target_name
            self._rebuild_palette_grid()
        self.select_color(selected_color, emit=emit)

    def _push_recent(self, color_hex: str) -> None:
        normalized = color_hex.lower()
        if any(entry.lower() == normalized for entry in self._recent_colors):
            return
        recent = [entry for entry in self._recent_colors if entry.lower() != normalized]
        recent.insert(0, normalized)
        self._recent_colors = recent[: self._max_recent_colors]
        self._rebuild_recent_grid()

    def get_recent_colors(self) -> list[str]:
        """Return a copy of the recent colors list."""
        return list(self._recent_colors)

    def add_recent_color(self, color: TextualColor) -> None:
        """Add a color to the recent list and refresh the UI."""
        self._push_recent(color.hex)

    def set_recent_colors(self, colors: list[str]) -> None:
        """Replace the recent colors list and refresh the UI."""
        seen: set[str] = set()
        normalized: list[str] = []
        for entry in colors:
            if not isinstance(entry, str):
                continue
            value = entry.strip().lower()
            if not value or value in seen:
                continue
            seen.add(value)
            normalized.append(value)
        self._recent_colors = normalized[: self._max_recent_colors]
        self._rebuild_recent_grid()
