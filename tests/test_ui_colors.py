"""Snapshot tests for color selection."""

import asyncio

import pytest
from textual_colorpicker import ColorPicker as TextualColorPicker
from textual_colorpicker.color_inputs import HexInput

from pixpop.canvas import PaintCanvas
from pixpop.screens.color_picker_dialog import ColorPickerDialog
from pixpop.widgets import PalettePicker
from pixpop.workspace import PaintWorkspace
from tests.snapshot_helpers import SnapshotPaintApp, canvas_to_offset, select_tool

pytestmark = pytest.mark.colors


def test_color_picker_snapshot(snap_compare) -> None:
    """Capture a snapshot after selecting colors and drawing blocks."""

    async def run_before(pilot) -> None:
        await pilot.pause()
        canvas = pilot.app.query_one(PaintCanvas)
        await select_tool(pilot, "pen")
        color_picker = pilot.app.query_one(PalettePicker)
        block_width = 4
        block_height = 2
        gap_x = 1
        gap_y = 2
        start_x = 8
        start_y = 12
        per_row = 5

        for index, color_widget in enumerate(color_picker._color_widgets[:4]):
            await pilot.click(color_widget)
            row = index // per_row
            col = index % per_row
            origin_x = start_x + col * (block_width + gap_x)
            origin_y = start_y + row * (block_height + gap_y) * 2
            for dx in range(block_width):
                for dy in range(block_height):
                    x = origin_x + dx
                    y = origin_y + dy * 2
                    await pilot.mouse_down(canvas, offset=canvas_to_offset(x, y))
                    await pilot.mouse_up(canvas, offset=canvas_to_offset(x, y))
        canvas.refresh()

    assert snap_compare(
        SnapshotPaintApp(), terminal_size=(120, 60), run_before=run_before
    )


def test_color_picker_dialog_defaults_to_pen_color() -> None:
    """The picker modal opens with the current pen color preselected."""

    async def main() -> tuple[str, str]:
        app = SnapshotPaintApp()
        async with app.run_test(size=(120, 60)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            pen_hex = ws._state.pen_color.hex.lower()

            ws.action_open_color_picker()
            await pilot.pause()
            assert isinstance(pilot.app.screen, ColorPickerDialog)
            dialog = pilot.app.screen
            initial_hex = dialog.query_one(TextualColorPicker).color.hex.lower()

            await pilot.press("escape")
            await pilot.pause()
            return pen_hex, initial_hex

    pen_hex, initial_hex = asyncio.run(main())
    assert pen_hex == initial_hex


def test_color_picker_dialog_confirm_applies_color() -> None:
    """Enter applies the picked color, updates recents, and closes the modal."""

    async def main() -> tuple[str, bool]:
        app = SnapshotPaintApp()
        async with app.run_test(size=(120, 60)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)

            ws.action_open_color_picker()
            await pilot.pause()
            assert isinstance(pilot.app.screen, ColorPickerDialog)
            # Set via HexInput: assigning ColorPicker.color directly routes
            # through the widget's HSV reactive, which can quantize the value.
            pilot.app.screen.query_one(HexInput).value = "#3366CC"
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            color_picker = ws._get_color_picker()
            in_recents = "#3366cc" in [
                entry.lower() for entry in color_picker.get_recent_colors()
            ]
            return ws._state.pen_color.hex.lower(), in_recents

    pen_hex, in_recents = asyncio.run(main())
    assert pen_hex == "#3366cc"
    assert in_recents


def test_color_picker_dialog_cancel_keeps_color() -> None:
    """Escape cancels without changing the pen color or recents."""

    async def main() -> tuple[str, str, list[str], list[str]]:
        app = SnapshotPaintApp()
        async with app.run_test(size=(120, 60)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            before_hex = ws._state.pen_color.hex.lower()
            before_recents = ws._get_color_picker().get_recent_colors()

            ws.action_open_color_picker()
            await pilot.pause()
            assert isinstance(pilot.app.screen, ColorPickerDialog)
            pilot.app.screen.query_one(HexInput).value = "#3366CC"
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

            return (
                before_hex,
                ws._state.pen_color.hex.lower(),
                before_recents,
                ws._get_color_picker().get_recent_colors(),
            )

    before_hex, after_hex, before_recents, after_recents = asyncio.run(main())
    assert before_hex == after_hex
    assert before_recents == after_recents


def test_color_picker_dialog_does_not_restyle_sidebar() -> None:
    """The modal's ColorPicker widget must not leak styles onto PalettePicker.

    Regression test: textual_colorpicker.ColorPicker ships DEFAULT_CSS with a
    bare `ColorPicker` type selector, which also matched the sidebar widget
    when it was named ColorPicker (squeezing the palette Select). The sidebar
    widget is now named PalettePicker; this test locks that in.
    """

    async def main() -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
        app = SnapshotPaintApp()
        async with app.run_test(size=(120, 60)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            sidebar = pilot.app.query_one(PalettePicker)
            before = tuple(sidebar.outer_size)  # type: ignore[attr-defined]

            ws.action_open_color_picker()
            await pilot.pause()
            during = tuple(sidebar.outer_size)  # type: ignore[attr-defined]

            await pilot.press("escape")
            await pilot.pause()
            after = tuple(sidebar.outer_size)  # type: ignore[attr-defined]
            return before, during, after

    before, during, after = asyncio.run(main())
    assert before == during == after
    assert before[0] > 20  # full sidebar width, not squeezed to content


def test_sidebar_picker_type_names_do_not_collide() -> None:
    """PalettePicker must not share a CSS type name with the library widget."""
    from textual_colorpicker import ColorPicker as LibraryColorPicker

    assert PalettePicker.__name__ != LibraryColorPicker.__name__
