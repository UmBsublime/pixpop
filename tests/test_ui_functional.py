"""Functional test placeholders."""

import random

import pytest

from pixpop.canvas import PaintCanvas
from pixpop.widgets import ColorPicker
from tests.snapshot_helpers import (
    SnapshotPaintApp,
    canvas_to_offset,
    middle_click,
    rename_active_layer,
    rename_active_tab,
    select_brush_size,
    select_spray_density,
    select_tool,
    set_normalized,
)

pytestmark = pytest.mark.functional


def test_functional_house_drawing_snapshot(snap_compare, monkeypatch) -> None:
    """Capture a snapshot after drawing a simple house."""
    rng = random.Random(123)

    def fake_uniform(a: float, b: float) -> float:
        return rng.uniform(a, b)

    monkeypatch.setattr(random, "uniform", fake_uniform)

    async def run_before(pilot) -> None:
        await pilot.pause()
        canvas = pilot.app.query_one(PaintCanvas)
        color_picker = pilot.app.query_one(ColorPicker)

        rename_active_tab(pilot, "ai_house")
        rename_active_layer(pilot, "main_layer")
        await pilot.pause()

        async def select_color(index: int) -> None:
            await pilot.click(color_picker._color_widgets[index])

        await set_normalized(pilot, False)

        # House body
        await select_tool(pilot, "rectangle")
        await select_brush_size(pilot, 2)
        await select_color(1)  # orange
        await pilot.mouse_down(canvas, offset=canvas_to_offset(20, 50))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(60, 76))

        # Fill house body
        await select_tool(pilot, "paint_bucket")
        await select_color(2)  # yellow
        await pilot.mouse_down(canvas, offset=canvas_to_offset(40, 64))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(40, 64))

        # Roof
        await select_tool(pilot, "line")
        await set_normalized(pilot, False)
        await select_brush_size(pilot, 2)
        await select_color(0)  # red
        await pilot.mouse_down(canvas, offset=canvas_to_offset(20, 50))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(40, 40))
        await pilot.mouse_down(canvas, offset=canvas_to_offset(40, 40))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(60, 50))

        # Cloud
        await select_tool(pilot, "ellipse")
        await set_normalized(pilot, False)
        await select_brush_size(pilot, 1)
        await select_color(4)  # blue
        await pilot.mouse_down(canvas, offset=canvas_to_offset(48, 8))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(70, 16))

        await select_tool(pilot, "circle")
        await pilot.mouse_down(canvas, offset=canvas_to_offset(46, 8))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(58, 20))
        await pilot.mouse_down(canvas, offset=canvas_to_offset(58, 6))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(72, 20))

        # Door
        await select_tool(pilot, "rectangle")
        await select_brush_size(pilot, 1)
        await select_color(7)  # brown
        await pilot.mouse_down(canvas, offset=canvas_to_offset(36, 60))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(44, 76))

        # Windows
        await select_color(4)  # blue
        await pilot.mouse_down(canvas, offset=canvas_to_offset(24, 58))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(32, 66))
        await pilot.mouse_down(canvas, offset=canvas_to_offset(48, 58))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(56, 66))

        # Path detail
        await select_tool(pilot, "pen")
        await select_brush_size(pilot, 1)
        await select_color(7)  # brown
        await pilot.mouse_down(canvas, offset=canvas_to_offset(40, 76))
        for x, y in [(40, 78), (40, 80), (40, 82)]:
            await pilot.hover(canvas, offset=canvas_to_offset(x, y))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(40, 82))

        # Fine pen details
        await select_tool(pilot, "fine-pen")
        await select_color(10)  # black
        await pilot.mouse_down(canvas, offset=canvas_to_offset(42, 70))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(42, 70))
        await middle_click(pilot, canvas, canvas_to_offset(43, 70))

        # Spray grass
        await select_tool(pilot, "spray")
        await select_brush_size(pilot, 2)
        await select_spray_density(pilot, 4)
        await select_color(3)  # green
        for x in range(12, 72, 6):
            await pilot.mouse_down(canvas, offset=canvas_to_offset(x, 84))
            await pilot.mouse_up(canvas, offset=canvas_to_offset(x, 84))

        # Erase a small highlight
        await select_tool(pilot, "eraser")
        await select_brush_size(pilot, 1)
        await pilot.mouse_down(canvas, offset=canvas_to_offset(30, 60))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(30, 60))

        canvas.refresh()

    assert snap_compare(
        SnapshotPaintApp(), terminal_size=(120, 60), run_before=run_before
    )
