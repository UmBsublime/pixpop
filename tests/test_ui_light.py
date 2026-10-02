"""Tests and snapshots for the light/dark lightness tools."""

from __future__ import annotations

import asyncio

import pytest
from textual.color import Color

from pixpop.canvas import PaintCanvas
from pixpop.constants import DEFAULT_LIGHT_STEP, MAX_LIGHT_STEP, MIN_LIGHT_STEP
from pixpop.tools.light_tool import DarkTool, LightTool
from pixpop.widgets import LightAccumulatePicker, LightStepPicker
from tests.snapshot_helpers import SnapshotPaintApp, canvas_to_offset, select_tool

pytestmark = pytest.mark.tools


class MockCanvas:
    """Minimal canvas stand-in implementing the tool-facing protocol."""

    def __init__(self, width: int = 20, height: int = 20) -> None:
        self.width = width
        self.height = height
        self.brush_size = 1
        self.pixels: dict[tuple[int, int], Color] = {}

    def is_valid_position(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_layer_pixel(self, x: int, y: int, index: int | None = None):
        return self.pixels.get((x, y))

    def set_layer_pixel(self, x, y, color, index=None, refresh=True) -> None:
        if color is None:
            self.pixels.pop((x, y), None)
        else:
            self.pixels[(x, y)] = color

    def refresh_composite_pixels(self, pixels) -> None:
        pass


BASE = Color(128, 64, 64)  # hsl l ≈ 0.376


class TestLightnessTools:
    def test_light_tool_lightens(self) -> None:
        canvas = MockCanvas()
        canvas.pixels[(5, 5)] = BASE
        tool = LightTool()
        tool.set_step(DEFAULT_LIGHT_STEP)
        tool.on_mouse_down(canvas, 5, 5)
        result = canvas.pixels[(5, 5)]
        assert result.hsl.l == pytest.approx(BASE.hsl.l + 0.05, abs=0.01)

    def test_dark_tool_darkens(self) -> None:
        canvas = MockCanvas()
        canvas.pixels[(5, 5)] = BASE
        tool = DarkTool()
        tool.set_step(DEFAULT_LIGHT_STEP)
        tool.on_mouse_down(canvas, 5, 5)
        result = canvas.pixels[(5, 5)]
        assert result.hsl.l == pytest.approx(BASE.hsl.l - 0.05, abs=0.01)

    def test_transparent_pixel_untouched(self) -> None:
        canvas = MockCanvas()
        LightTool().on_mouse_down(canvas, 5, 5)
        DarkTool().on_mouse_down(canvas, 5, 5)
        assert canvas.pixels == {}

    def test_lightness_clamped_at_white(self) -> None:
        canvas = MockCanvas()
        canvas.pixels[(0, 0)] = Color(250, 250, 250)
        tool = LightTool()
        tool.set_step(MAX_LIGHT_STEP)
        for _ in range(5):
            tool.on_mouse_down(canvas, 0, 0)
        assert canvas.pixels[(0, 0)].hsl.l == pytest.approx(1.0, abs=0.01)

    def test_lightness_clamped_at_black(self) -> None:
        canvas = MockCanvas()
        canvas.pixels[(0, 0)] = Color(5, 5, 5)
        tool = DarkTool()
        tool.set_step(MAX_LIGHT_STEP)
        for _ in range(5):
            tool.on_mouse_down(canvas, 0, 0)
        assert canvas.pixels[(0, 0)].hsl.l == pytest.approx(0.0, abs=0.01)

    def test_brush_size_footprint(self) -> None:
        canvas = MockCanvas()
        canvas.brush_size = 2
        for dx in range(2):
            for dy in range(2):
                canvas.pixels[(4 + dx, 4 + dy)] = BASE
        canvas.pixels[(8, 8)] = BASE  # outside footprint
        LightTool().on_mouse_down(canvas, 4, 4)
        for dx in range(2):
            for dy in range(2):
                assert canvas.pixels[(4 + dx, 4 + dy)].hsl.l > BASE.hsl.l
        assert canvas.pixels[(8, 8)] == BASE

    def test_accumulate_on_reapplies_while_dragging(self) -> None:
        canvas = MockCanvas()
        canvas.pixels[(5, 5)] = BASE
        tool = LightTool()
        tool.set_step(DEFAULT_LIGHT_STEP)
        tool.set_accumulate(True)
        tool.on_mouse_down(canvas, 5, 5)
        first = canvas.pixels[(5, 5)].hsl.l
        # Drag away and back over the same pixel.
        tool.on_mouse_move(canvas, 6, 5)
        tool.on_mouse_move(canvas, 5, 5)
        second = canvas.pixels[(5, 5)].hsl.l
        assert second > first

    def test_accumulate_off_applies_once_per_stroke(self) -> None:
        canvas = MockCanvas()
        canvas.pixels[(5, 5)] = BASE
        tool = LightTool()
        tool.set_step(DEFAULT_LIGHT_STEP)
        tool.set_accumulate(False)
        tool.on_mouse_down(canvas, 5, 5)
        first = canvas.pixels[(5, 5)]
        tool.on_mouse_move(canvas, 6, 5)
        tool.on_mouse_move(canvas, 5, 5)
        assert canvas.pixels[(5, 5)] == first
        # A new stroke (mouse up/down) adjusts again.
        tool.on_mouse_up(canvas, 5, 5)
        tool.on_mouse_down(canvas, 5, 5)
        assert canvas.pixels[(5, 5)].hsl.l > first.hsl.l

    def test_set_step_clamped(self) -> None:
        tool = LightTool()
        tool.set_step(0)
        assert tool.step == MIN_LIGHT_STEP
        tool.set_step(999)
        assert tool.step == MAX_LIGHT_STEP

    def test_out_of_bounds_ignored(self) -> None:
        canvas = MockCanvas()
        canvas.pixels[(0, 0)] = BASE
        canvas.brush_size = 3
        LightTool().on_mouse_down(canvas, -2, -2)
        # Only the in-bounds corner pixel is touched; no crash.
        assert canvas.pixels[(0, 0)].hsl.l > BASE.hsl.l


def test_light_tool_snapshot(snap_compare) -> None:
    """Capture a snapshot after lightening/darkening painted pixels."""

    async def run_before(pilot) -> None:
        await pilot.pause()
        canvas = pilot.app.query_one(PaintCanvas)
        # Paint two rows of pixels to adjust.
        await select_tool(pilot, "pen")
        for x in range(8, 24, 2):
            await pilot.mouse_down(canvas, offset=canvas_to_offset(x, 20))
            await pilot.mouse_up(canvas, offset=canvas_to_offset(x, 20))
            await pilot.mouse_down(canvas, offset=canvas_to_offset(x, 30))
            await pilot.mouse_up(canvas, offset=canvas_to_offset(x, 30))
        # Lighten the top row.
        await select_tool(pilot, "light")
        for x in range(8, 24, 2):
            await pilot.mouse_down(canvas, offset=canvas_to_offset(x, 20))
            await pilot.mouse_up(canvas, offset=canvas_to_offset(x, 20))
        # Darken the bottom row.
        await select_tool(pilot, "dark")
        for x in range(8, 24, 2):
            await pilot.mouse_down(canvas, offset=canvas_to_offset(x, 30))
            await pilot.mouse_up(canvas, offset=canvas_to_offset(x, 30))
        await select_tool(pilot, "pen")
        canvas.refresh()

    assert snap_compare(
        SnapshotPaintApp(), terminal_size=(120, 60), run_before=run_before
    )


class TestLightPickerVisibility:
    """The light sections only show for light/dark tools."""

    def test_sections_hidden_by_default(self) -> None:
        async def main() -> None:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                step = app.query_one(LightStepPicker)
                accumulate = app.query_one(LightAccumulatePicker)
                assert step.has_class("invisible")
                assert accumulate.has_class("invisible")

        asyncio.run(main())

    def test_sections_visible_for_light_and_dark(self) -> None:
        async def main() -> None:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                step = app.query_one(LightStepPicker)
                accumulate = app.query_one(LightAccumulatePicker)
                for tool_name in ("light", "dark"):
                    await select_tool(pilot, tool_name)
                    assert not step.has_class("invisible")
                    assert not accumulate.has_class("invisible")
                await select_tool(pilot, "pen")
                assert step.has_class("invisible")
                assert accumulate.has_class("invisible")

        asyncio.run(main())

    def test_step_propagates_to_both_tools(self) -> None:
        async def main() -> None:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                await select_tool(pilot, "light")
                app.query_one(LightStepPicker).select_step(8)
                await pilot.pause()
                canvas = app.query_one(PaintCanvas)
                assert canvas.tools["light"].step == 8
                assert canvas.tools["dark"].step == 8

        asyncio.run(main())

    def test_accumulate_propagates_to_both_tools(self) -> None:
        async def main() -> None:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                await select_tool(pilot, "light")
                app.query_one(LightAccumulatePicker).set_value(False)
                await pilot.pause()
                canvas = app.query_one(PaintCanvas)
                assert canvas.tools["light"].accumulate is False
                assert canvas.tools["dark"].accumulate is False

        asyncio.run(main())
