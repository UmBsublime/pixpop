"""Functional test placeholders."""

import asyncio
import random

import pytest

from pixpop.canvas import PaintCanvas
from pixpop.widgets import CanvasTabs, ColorPicker
from pixpop.workspace import PaintWorkspace
from tests.snapshot_helpers import (
    SnapshotPaintApp,
    canvas_to_offset,
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

        # Single-pixel pen details (size 1 replaces the old fine pen)
        await select_tool(pilot, "pen")
        await select_brush_size(pilot, 1)
        await select_color(10)  # black
        await pilot.mouse_down(canvas, offset=canvas_to_offset(42, 70))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(42, 70))
        await pilot.mouse_down(canvas, offset=canvas_to_offset(43, 70))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(43, 70))

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


def test_fullscreen_toggle() -> None:
    """Pressing f maximizes the canvas tabs; pressing f again restores them."""

    async def main() -> None:
        app = SnapshotPaintApp()
        async with app.run_test(size=(120, 60)) as pilot:
            await pilot.pause()
            canvas_tabs = app.query_one(CanvasTabs)

            assert app.screen.maximized is None
            await pilot.press("f")
            assert app.screen.maximized is canvas_tabs
            await pilot.press("f")
            assert app.screen.maximized is None

    asyncio.run(main())


async def _active_canvas(app, pilot) -> PaintCanvas:
    """Return the currently visible canvas, waiting for it to lay out."""
    for _ in range(20):
        await pilot.pause()
        for canvas in app.query(PaintCanvas):
            if canvas.region.width > 0:
                return canvas
    raise AssertionError("no visible canvas found")


async def _open_small_canvas_tab(pilot, workspace) -> PaintCanvas:
    """Create/activate a 40x20 tab and return its laid-out canvas."""
    pane = workspace._create_tab_with_name("small", width=40, height=20)
    workspace._tabs_manager.add_pane(pane, activate=True)
    return await _active_canvas(pilot.app, pilot)


def test_small_canvas_centered_in_viewport() -> None:
    """A canvas smaller than the viewport renders centered within the tab."""

    async def main() -> None:
        app = SnapshotPaintApp()
        async with app.run_test(size=(120, 60)) as pilot:
            await pilot.pause()
            workspace = app.query_one(PaintWorkspace)
            canvas = await _open_small_canvas_tab(pilot, workspace)

            viewport = canvas.scrollable_content_region
            margin_x = (viewport.width - 40) // 2
            margin_y = (viewport.height - 10) // 2
            assert margin_x > 0
            assert margin_y > 0
            assert canvas._centering_offset_cells() == (margin_x, margin_y)

            # The viewport centre maps to the canvas centre...
            centre = canvas.screen_to_canvas_coords(
                canvas.region.x + 1 + viewport.width // 2,
                viewport.y + viewport.height // 2,
            )
            assert centre == (20, 10)
            # ...and the content corner lands in the margin, out of bounds.
            corner = canvas.screen_to_canvas_coords(canvas.region.x + 1, viewport.y)
            assert corner == (-margin_x, -margin_y * 2)
            assert not canvas.is_valid_position(*corner)

            # render_line pads the left of each canvas row and leaves the
            # top/bottom margin rows empty (widget background shows through).
            assert canvas.render_line(margin_y - 1).text == ""
            assert canvas.render_line(margin_y).text.startswith(" " * margin_x)

    asyncio.run(main())


def test_centered_canvas_mouse_input() -> None:
    """Margin clicks are ignored; canvas clicks hit the right pixel."""

    async def main() -> None:
        app = SnapshotPaintApp()
        async with app.run_test(size=(120, 60)) as pilot:
            await pilot.pause()
            workspace = app.query_one(PaintWorkspace)
            canvas = await _open_small_canvas_tab(pilot, workspace)
            viewport = canvas.scrollable_content_region

            # Click in the top margin: nothing is painted.
            await pilot.mouse_down(canvas, offset=(viewport.width // 2 + 1, 0))
            await pilot.mouse_up(canvas, offset=(viewport.width // 2 + 1, 0))
            assert all(
                canvas.get_composited_pixel(x, y) is None
                for x in range(40)
                for y in range(20)
            )

            # Click in the viewport centre: paints canvas centre (20, 10).
            await pilot.mouse_down(
                canvas, offset=(viewport.width // 2 + 1, viewport.height // 2)
            )
            await pilot.mouse_up(
                canvas, offset=(viewport.width // 2 + 1, viewport.height // 2)
            )
            pixel = canvas.get_composited_pixel(20, 10)
            assert pixel is not None
            assert pixel.r > 150

    asyncio.run(main())


def test_centering_reacts_to_fullscreen_and_scrolling() -> None:
    """Margins track viewport changes; scrollable canvases are not centered."""

    async def main() -> None:
        app = SnapshotPaintApp()
        async with app.run_test(size=(120, 60)) as pilot:
            await pilot.pause()
            workspace = app.query_one(PaintWorkspace)
            canvas = await _open_small_canvas_tab(pilot, workspace)

            before = canvas._centering_offset_cells()
            await pilot.press("f")
            await _active_canvas(app, pilot)
            after = canvas._centering_offset_cells()
            assert after[0] > before[0]  # fullscreen widens the viewport

            await pilot.press("f")
            await _active_canvas(app, pilot)
            assert canvas._centering_offset_cells() == before

            # A canvas larger than the viewport scrolls from the top-left.
            pane = workspace._create_tab_with_name("big", width=200, height=200)
            workspace._tabs_manager.add_pane(pane, activate=True)
            big = await _active_canvas(app, pilot)
            assert big.width == 200
            assert big._centering_offset_cells() == (0, 0)

    asyncio.run(main())
