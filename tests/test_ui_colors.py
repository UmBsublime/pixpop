"""Snapshot tests for color selection."""

import pytest

from pixpop.canvas import PaintCanvas
from pixpop.widgets import ColorPicker
from tests.snapshot_helpers import SnapshotPaintApp, canvas_to_offset, select_tool

pytestmark = pytest.mark.colors


def test_color_picker_snapshot(snap_compare) -> None:
    """Capture a snapshot after selecting colors and drawing blocks."""

    async def run_before(pilot) -> None:
        await pilot.pause()
        canvas = pilot.app.query_one(PaintCanvas)
        await select_tool(pilot, "pen")
        color_picker = pilot.app.query_one(ColorPicker)
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
