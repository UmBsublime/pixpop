"""Snapshot tests for tools."""

import random

import pytest

from pixpop.canvas import PaintCanvas
from tests.snapshot_helpers import (
    SnapshotPaintApp,
    canvas_to_offset,
    middle_click,
    select_brush_size,
    select_spray_density,
    select_tool,
    set_normalized,
)

pytestmark = pytest.mark.tools


def test_circle_tool_snapshot(snap_compare) -> None:
    """Capture a snapshot after drawing normalized and non-normalized circles."""

    async def run_before(pilot) -> None:
        await pilot.pause()
        canvas = pilot.app.query_one(PaintCanvas)
        await select_tool(pilot, "circle")
        await set_normalized(pilot, False)
        await pilot.mouse_down(canvas, offset=canvas_to_offset(8, 8))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(36, 36))
        await set_normalized(pilot, True)
        await pilot.mouse_down(canvas, offset=canvas_to_offset(52, 8))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(80, 30))
        canvas.refresh()

    assert snap_compare(
        SnapshotPaintApp(), terminal_size=(120, 60), run_before=run_before
    )


def test_ellipse_tool_snapshot(snap_compare) -> None:
    """Capture a snapshot after drawing normalized and non-normalized ellipses."""

    async def run_before(pilot) -> None:
        await pilot.pause()
        canvas = pilot.app.query_one(PaintCanvas)
        await select_tool(pilot, "ellipse")
        await set_normalized(pilot, False)
        await pilot.mouse_down(canvas, offset=canvas_to_offset(8, 10))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(44, 22))
        await set_normalized(pilot, True)
        await pilot.mouse_down(canvas, offset=canvas_to_offset(28, 28))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(60, 44))
        canvas.refresh()

    assert snap_compare(
        SnapshotPaintApp(), terminal_size=(120, 60), run_before=run_before
    )


def test_line_tool_snapshot(snap_compare) -> None:
    """Capture a snapshot after drawing normalized and non-normalized lines."""

    async def run_before(pilot) -> None:
        await pilot.pause()
        canvas = pilot.app.query_one(PaintCanvas)
        await select_tool(pilot, "line")
        await set_normalized(pilot, False)
        start_x, start_y = 10, 10
        end_x, end_y = 34, 28
        await pilot.mouse_down(canvas, offset=canvas_to_offset(start_x, start_y))
        for step in range(1, 5):
            x = start_x + ((end_x - start_x) * step // 5)
            y = start_y + ((end_y - start_y) * step // 5)
            await pilot.hover(canvas, offset=canvas_to_offset(x, y))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(end_x, end_y))
        await set_normalized(pilot, True)
        start_x, start_y = 48, 10
        end_x, end_y = 72, 28
        await pilot.mouse_down(canvas, offset=canvas_to_offset(start_x, start_y))
        for step in range(1, 5):
            x = start_x + ((end_x - start_x) * step // 5)
            y = start_y + ((end_y - start_y) * step // 5)
            await pilot.hover(canvas, offset=canvas_to_offset(x, y))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(end_x, end_y))
        canvas.refresh()

    assert snap_compare(
        SnapshotPaintApp(), terminal_size=(120, 60), run_before=run_before
    )


def test_pen_tool_snapshot(snap_compare) -> None:
    """Capture a snapshot after drawing a snake-like pen stroke."""

    async def run_before(pilot) -> None:
        await pilot.pause()
        canvas = pilot.app.query_one(PaintCanvas)
        await select_tool(pilot, "pen")

        snake = [
            (10, 10),
            (14, 12),
            (18, 14),
            (22, 12),
            (26, 10),
            (30, 12),
            (34, 14),
            (38, 12),
            (42, 10),
            (46, 12),
        ]
        start_x, start_y = snake[0]
        await pilot.mouse_down(canvas, offset=canvas_to_offset(start_x, start_y))
        for x, y in snake[1:]:
            await pilot.hover(canvas, offset=canvas_to_offset(x, y))
        end_x, end_y = snake[-1]
        await pilot.mouse_up(canvas, offset=canvas_to_offset(end_x, end_y))

        canvas.refresh()

    assert snap_compare(
        SnapshotPaintApp(), terminal_size=(120, 60), run_before=run_before
    )


def test_fine_pen_tool_snapshot(snap_compare) -> None:
    """Capture a snapshot after fine-pen top/bottom strokes."""

    async def run_before(pilot) -> None:
        await pilot.pause()
        canvas = pilot.app.query_one(PaintCanvas)
        await select_tool(pilot, "fine-pen")

        await pilot.mouse_down(canvas, offset=canvas_to_offset(14, 12))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(14, 12))

        await middle_click(pilot, canvas, canvas_to_offset(18, 12))

        canvas.refresh()

    assert snap_compare(
        SnapshotPaintApp(), terminal_size=(120, 60), run_before=run_before
    )


def test_rectangle_tool_snapshot(snap_compare) -> None:
    """Capture a snapshot after drawing a rectangle."""

    async def run_before(pilot) -> None:
        await pilot.pause()
        canvas = pilot.app.query_one(PaintCanvas)
        await select_tool(pilot, "rectangle")
        await pilot.mouse_down(canvas, offset=canvas_to_offset(12, 12))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(38, 26))
        canvas.refresh()

    assert snap_compare(
        SnapshotPaintApp(), terminal_size=(120, 60), run_before=run_before
    )


def test_brush_size_snapshot(snap_compare) -> None:
    """Capture a snapshot after drawing with each brush size."""

    async def run_before(pilot) -> None:
        await pilot.pause()
        canvas = pilot.app.query_one(PaintCanvas)
        await select_tool(pilot, "pen")
        positions = [(6, 40), (16, 40), (28, 40), (42, 40), (56, 40)]

        for size, (x, y) in zip(range(1, 6), positions, strict=True):
            await select_brush_size(pilot, size)
            await pilot.mouse_down(canvas, offset=canvas_to_offset(x, y))
            await pilot.mouse_up(canvas, offset=canvas_to_offset(x, y))

        canvas.refresh()

    assert snap_compare(
        SnapshotPaintApp(), terminal_size=(120, 60), run_before=run_before
    )


def test_spray_tool_snapshot(snap_compare, monkeypatch) -> None:
    """Capture a snapshot after a deterministic spray pass."""

    rng = random.Random(123)

    def fake_uniform(a: float, b: float) -> float:
        return rng.uniform(a, b)

    monkeypatch.setattr(random, "uniform", fake_uniform)

    async def run_before(pilot) -> None:
        await pilot.pause()
        canvas = pilot.app.query_one(PaintCanvas)
        await select_tool(pilot, "spray")
        positions = [5, 15, 25, 40, 55]
        base_y = 10
        row_offset = 20
        for size in range(1, 6):
            await select_brush_size(pilot, size)
            y = base_y + (size - 1) * row_offset
            for index, density in enumerate(range(1, 6)):
                await select_spray_density(pilot, density)
                x = positions[index]
                await pilot.mouse_down(canvas, offset=canvas_to_offset(x, y))
                await pilot.mouse_up(canvas, offset=canvas_to_offset(x, y))

        canvas.refresh()

    assert snap_compare(
        SnapshotPaintApp(), terminal_size=(120, 60), run_before=run_before
    )
