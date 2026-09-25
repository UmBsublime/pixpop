"""Shared helpers for snapshot tests."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.events import MouseDown, MouseMove, MouseUp
from textual.widgets import Footer, Header, Tabs

from pixpop.app import PixPop
from pixpop.canvas import PaintCanvas
from pixpop.widgets import (
    BrushSizePicker,
    LayerPicker,
    NormalizedPicker,
    SprayDensityPicker,
    ToolPicker,
)
from pixpop.workspace import PaintWorkspace


class SnapshotPaintApp(PixPop):
    """Paint app variant with a deterministic header clock."""

    CSS_PATH = str(
        (Path(__file__).resolve().parents[1] / "src/pixpop/styles/main.tcss")
    )

    def compose(self) -> ComposeResult:
        """Create the main application layout with a stable header."""
        yield Header(show_clock=False)
        with Vertical():
            yield PaintWorkspace()
        yield Footer()


def canvas_to_offset(x: int, y: int) -> tuple[int, int]:
    """Convert canvas coordinates to pilot offset coordinates."""
    return (x + 1, (y + 2) // 2)


async def select_tool(pilot, tool_name: str) -> None:
    """Select a tool via the UI so the picker state stays in sync."""
    tool_picker = pilot.app.query_one(ToolPicker)
    tool_picker.select_tool(tool_name)
    await pilot.pause()


async def set_normalized(pilot, value: bool) -> None:
    """Set normalized toggle via the UI."""
    normalized_picker = pilot.app.query_one(NormalizedPicker)
    normalized_picker.set_value(value)
    await pilot.pause()


async def select_brush_size(pilot, size: int) -> None:
    """Select a brush size via the UI."""
    brush_picker = pilot.app.query_one(BrushSizePicker)
    brush_picker.select_size(size)
    await pilot.pause()


async def select_spray_density(pilot, density: int) -> None:
    """Select a spray density via the UI."""
    spray_picker = pilot.app.query_one(SprayDensityPicker)
    spray_picker.select_density(density)
    await pilot.pause()


def rename_active_tab(pilot, name: str) -> None:
    """Rename the active canvas tab and update the UI label."""
    tabs = pilot.app.query_one(Tabs)
    active_tab = tabs.active_tab
    if active_tab is not None:
        active_tab.label = name


def rename_active_layer(pilot, name: str) -> None:
    """Rename the active layer and refresh the layer picker UI."""
    canvas = pilot.app.query_one(PaintCanvas)
    canvas.rename_layer(canvas.active_layer_index, name)
    layer_picker = pilot.app.query_one(LayerPicker)
    layer_picker.set_layers(canvas.get_layers(), canvas.active_layer_index)


async def middle_click(pilot, widget, offset: tuple[int, int]) -> None:
    """Simulate a middle mouse click at the given widget offset."""
    await pilot._post_mouse_events(
        [MouseMove, MouseDown, MouseUp],
        widget=widget,
        offset=offset,
        button=2,
    )
