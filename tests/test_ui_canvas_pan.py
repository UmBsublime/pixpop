"""Tests for canvas panning (ctrl+drag and space+drag gestures)."""

from __future__ import annotations

import asyncio

import pytest
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.events import Key, MouseMove, MouseUp
from textual.widgets import Footer, Header

from pixpop.canvas import PaintCanvas
from pixpop.config import AppConfig
from pixpop.workspace import PaintWorkspace
from tests.snapshot_helpers import SnapshotPaintApp

pytestmark = pytest.mark.functional


def _make_app(pan_direction: str = "grab") -> SnapshotPaintApp:
    """Build the test app with a specific pan direction.

    The workspace is constructed with an explicit config so pan direction is
    under test control; everything else uses the default snapshot app.
    """
    config = AppConfig(canvas_pan_direction=pan_direction)

    class ConfiguredPaintApp(SnapshotPaintApp):
        def compose(self) -> ComposeResult:
            yield Header(show_clock=False)
            with Vertical():
                yield PaintWorkspace(config=config)
            yield Footer()

    return ConfiguredPaintApp()


async def _ctrl_drag(
    pilot,
    canvas: PaintCanvas,
    start: tuple[int, int],
    *moves: tuple[int, int],
) -> None:
    """Simulate ctrl+press at start, then ctrl+drag through moves, release."""
    await pilot.mouse_down(canvas, offset=start, control=True)
    for move in moves:
        await pilot._post_mouse_events(
            [MouseMove], canvas, offset=move, button=1, control=True
        )
    await pilot.mouse_up(
        canvas, offset=moves[-1] if moves else start, control=True
    )
    await pilot.pause()


async def _big_canvas(pilot, workspace: PaintWorkspace) -> PaintCanvas:
    """Give the active canvas room to scroll and return it."""
    canvas = workspace._get_canvas()
    canvas.resize_preserve_content(200, 200)
    await pilot.pause()
    return canvas


def test_ctrl_drag_pans_grab_direction() -> None:
    """Grab mode: dragging right/down moves the view left/up (content follows
    the cursor)."""

    async def main() -> tuple[int, int]:
        app = _make_app("grab")
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            canvas = await _big_canvas(pilot, ws)
            assert canvas.scroll_offset == (0, 0)

            # Drag 8 cells right, 4 cells down -> scroll moves -8, -4; start
            # scrolled so the result stays within bounds.
            canvas.scroll_to(40, 20, animate=False)
            await pilot.pause()
            await _ctrl_drag(pilot, canvas, (10, 10), (18, 14))
            return (
                round(canvas.scroll_offset.x),
                round(canvas.scroll_offset.y),
            )

    assert asyncio.run(main()) == (32, 16)  # 40-8, 20-4


def test_ctrl_drag_pans_stick_direction() -> None:
    """Stick mode: dragging right/down moves the view right/down."""

    async def main() -> tuple[int, int]:
        app = _make_app("stick")
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            canvas = await _big_canvas(pilot, ws)
            assert canvas.scroll_offset == (0, 0)

            await _ctrl_drag(pilot, canvas, (5, 5), (15, 9))
            return (
                round(canvas.scroll_offset.x),
                round(canvas.scroll_offset.y),
            )

    assert asyncio.run(main()) == (10, 4)  # 0+10, 0+4


def test_ctrl_click_suppresses_drawing() -> None:
    """A ctrl+click with no movement draws nothing and writes no undo entry."""

    async def main() -> tuple[int, int]:
        app = _make_app()
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            canvas = await _big_canvas(pilot, ws)
            canvas.current_tool = "pen"
            canvas.brush_size = 1
            undo_depth = len(canvas.undo_manager.undo_stack)

            await _ctrl_drag(pilot, canvas, (5, 5))
            layer = canvas.layers[canvas.active_layer_index]
            return len(layer.pixels), len(canvas.undo_manager.undo_stack) - undo_depth

    assert asyncio.run(main()) == (0, 0)


def test_pan_then_draw_still_works() -> None:
    """Normal drawing is unaffected after a pan gesture ends."""

    async def main() -> tuple[int, int]:
        app = _make_app()
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            canvas = await _big_canvas(pilot, ws)
            canvas.current_tool = "pen"
            canvas.brush_size = 1

            # Stick-free default is "grab": drag left to scroll right.
            await _ctrl_drag(pilot, canvas, (15, 5), (5, 5))
            assert canvas.scroll_offset.x > 0

            # Regular (unmodified) click still draws.
            await pilot.mouse_down(canvas, offset=(5, 5))
            await pilot.mouse_up(canvas, offset=(5, 5))
            await pilot.pause()
            layer = canvas.layers[canvas.active_layer_index]
            return len(layer.pixels), round(canvas.scroll_offset.x)

    pixels, _ = asyncio.run(main())
    assert pixels > 0


def test_pan_beyond_widget_edge_keeps_scrolling() -> None:
    """Mouse capture keeps the pan alive when the drag leaves the canvas."""

    async def main() -> tuple[int, int]:
        app = _make_app("stick")
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            canvas = await _big_canvas(pilot, ws)

            # Start a pan inside the canvas, then drag way past its right edge
            # (screen-absolute coordinates, no widget targeting).
            await pilot.mouse_down(canvas, offset=(5, 5), control=True)
            await pilot._post_mouse_events(
                [MouseMove], None, offset=(59, 5), button=1, control=True
            )
            await pilot._post_mouse_events(
                [MouseUp], None, offset=(59, 5), button=1, control=True
            )
            await pilot.pause()
            return (
                round(canvas.scroll_offset.x),
                round(canvas.scroll_offset.y),
            )

    x, y = asyncio.run(main())
    assert x > 0
    assert y == 0


def test_pointer_shape_during_pan() -> None:
    """The pointer switches to 'grabbing' while panning, then resets."""

    async def main() -> tuple[str, str, bool]:
        app = _make_app()
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            canvas = await _big_canvas(pilot, ws)

            await pilot.mouse_down(canvas, offset=(5, 5), control=True)
            await pilot.pause()
            during = str(canvas.styles.pointer)
            captured = app.mouse_captured is canvas
            await pilot.mouse_up(canvas, offset=(5, 5), control=True)
            await pilot.pause()
            after = str(canvas.styles.pointer)
            return during, after, captured

    during, after, captured = asyncio.run(main())
    assert during == "grabbing"
    assert after == "default"
    assert captured


def test_pan_clamps_at_canvas_bounds() -> None:
    """Panning past the scrollable area clamps at the max scroll offset."""

    async def main() -> tuple[int, int, int, int]:
        app = _make_app("stick")
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            canvas = await _big_canvas(pilot, ws)

            # Repeatedly drag to the bottom-right within the visible screen;
            # each drag should keep scrolling until clamped at max.
            for _ in range(30):
                await _ctrl_drag(pilot, canvas, (5, 5), (20, 20))
                if (
                    round(canvas.scroll_offset.x) >= canvas.max_scroll_x
                    and round(canvas.scroll_offset.y) >= canvas.max_scroll_y
                ):
                    break
            return (
                round(canvas.scroll_offset.x),
                round(canvas.scroll_offset.y),
                canvas.max_scroll_x,
                canvas.max_scroll_y,
            )

    x, y, max_x, max_y = asyncio.run(main())
    assert max_x > 0 and max_y > 0
    assert x == max_x
    assert y == max_y


# --- Space+drag gesture (universal: works under tmux and every terminal) ---


async def _space_drag(
    pilot,
    canvas: PaintCanvas,
    start: tuple[int, int],
    *moves: tuple[int, int],
) -> None:
    """Arm panning via a space key press, then drag with no modifiers."""
    canvas.focus()
    canvas.post_message(Key("space", " "))
    await pilot.pause()
    await pilot.mouse_down(canvas, offset=start)
    for move in moves:
        await pilot._post_mouse_events([MouseMove], canvas, offset=move, button=1)
    await pilot.mouse_up(canvas, offset=moves[-1] if moves else start)
    await pilot.pause()


def test_space_drag_pans_grab_direction() -> None:
    """Space-armed drag pans like ctrl+drag (grab: content follows cursor)."""

    async def main() -> tuple[int, int]:
        app = _make_app("grab")
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            canvas = await _big_canvas(pilot, ws)
            canvas.scroll_to(40, 20, animate=False)
            await pilot.pause()

            await _space_drag(pilot, canvas, (10, 10), (18, 14))
            return (
                round(canvas.scroll_offset.x),
                round(canvas.scroll_offset.y),
            )

    assert asyncio.run(main()) == (32, 16)  # 40-8, 20-4


def test_space_drag_pans_stick_direction() -> None:
    """Space-armed drag respects the stick direction setting."""

    async def main() -> tuple[int, int]:
        app = _make_app("stick")
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            canvas = await _big_canvas(pilot, ws)

            await _space_drag(pilot, canvas, (5, 5), (15, 9))
            return (
                round(canvas.scroll_offset.x),
                round(canvas.scroll_offset.y),
            )

    assert asyncio.run(main()) == (10, 4)


def test_space_armed_click_suppresses_drawing() -> None:
    """A click while space-armed draws nothing and writes no undo entry."""

    async def main() -> tuple[int, int]:
        app = _make_app()
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            canvas = await _big_canvas(pilot, ws)
            canvas.current_tool = "pen"
            canvas.brush_size = 1
            undo_depth = len(canvas.undo_manager.undo_stack)

            await _space_drag(pilot, canvas, (5, 5))
            layer = canvas.layers[canvas.active_layer_index]
            return len(layer.pixels), len(canvas.undo_manager.undo_stack) - undo_depth

    assert asyncio.run(main()) == (0, 0)


def test_stale_armed_click_draws() -> None:
    """A space press that has gone stale (no repeats — space released) does
    not suppress drawing on the next click."""

    async def main() -> int:
        from pixpop.canvas import _PAN_ARM_TIMEOUT

        app = _make_app()
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            canvas = await _big_canvas(pilot, ws)
            canvas.current_tool = "pen"
            canvas.brush_size = 1
            canvas.focus()

            canvas.post_message(Key("space", " "))
            await pilot.pause()
            # Space released: repeats stop, freshness window lapses.
            await asyncio.sleep(_PAN_ARM_TIMEOUT + 0.1)

            await pilot.mouse_down(canvas, offset=(5, 5))
            await pilot.mouse_up(canvas, offset=(5, 5))
            await pilot.pause()
            layer = canvas.layers[canvas.active_layer_index]
            return len(layer.pixels)

    assert asyncio.run(main()) > 0


def test_space_pointer_feedback() -> None:
    """Pointer is 'grab' while armed, 'grabbing' mid-drag, 'default' after."""

    async def main() -> tuple[str, str, str]:
        app = _make_app()
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            canvas = await _big_canvas(pilot, ws)

            canvas.focus()
            canvas.post_message(Key("space", " "))
            await pilot.pause()
            armed = str(canvas.styles.pointer)

            await pilot.mouse_down(canvas, offset=(8, 8))
            await pilot.pause()
            dragging = str(canvas.styles.pointer)
            await pilot.mouse_up(canvas, offset=(8, 8))
            await pilot.pause()
            after = str(canvas.styles.pointer)
            return armed, dragging, after

    assert asyncio.run(main()) == ("grab", "grabbing", "default")


def test_space_key_repeat_does_not_break_pan() -> None:
    """Repeated space presses (key auto-repeat) still pan correctly."""

    async def main() -> tuple[int, int]:
        app = _make_app("stick")
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            canvas = await _big_canvas(pilot, ws)

            canvas.focus()
            for _ in range(3):  # held space auto-repeat
                canvas.post_message(Key("space", " "))
            await pilot.pause()
            await pilot.mouse_down(canvas, offset=(5, 5))
            await pilot._post_mouse_events(
                [MouseMove], canvas, offset=(15, 5), button=1
            )
            await pilot.mouse_up(canvas, offset=(15, 5))
            await pilot.pause()
            return (
                round(canvas.scroll_offset.x),
                round(canvas.scroll_offset.y),
            )

    assert asyncio.run(main()) == (10, 0)


def test_unarmed_click_still_draws() -> None:
    """Without a space press, a normal click draws (regression guard)."""

    async def main() -> int:
        app = _make_app()
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            canvas = await _big_canvas(pilot, ws)
            canvas.current_tool = "pen"
            canvas.brush_size = 1
            canvas.focus()
            await pilot.pause()

            await pilot.mouse_down(canvas, offset=(5, 5))
            await pilot.mouse_up(canvas, offset=(5, 5))
            await pilot.pause()
            layer = canvas.layers[canvas.active_layer_index]
            return len(layer.pixels)

    assert asyncio.run(main()) > 0


def test_drag_after_space_released_draws() -> None:
    """User bug: mouse released while space held, then space released — the
    next drag must draw, not pan. Trailing auto-repeat presses arriving
    after the mouse release keep the arm fresh only while space is held;
    once repeats stop, the arm goes stale and cannot start a pan."""

    async def main() -> tuple[int, int, int]:
        from pixpop.canvas import _PAN_ARM_TIMEOUT

        app = _make_app("stick")
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            canvas = await _big_canvas(pilot, ws)
            canvas.current_tool = "pen"
            canvas.brush_size = 1
            canvas.focus()

            # Space-pan: press space, drag, release mouse while space held.
            canvas.post_message(Key("space", " "))
            await pilot.pause()
            await pilot.mouse_down(canvas, offset=(5, 5))
            await pilot._post_mouse_events(
                [MouseMove], canvas, offset=(15, 5), button=1
            )
            await pilot.mouse_up(canvas, offset=(15, 5))
            scroll_after_pan = round(canvas.scroll_offset.x)
            assert scroll_after_pan > 0

            # Trailing auto-repeat as space is released, then repeats stop.
            canvas.post_message(Key("space", " "))
            await pilot.pause()
            # Space is now released: let the freshness window lapse.
            await asyncio.sleep(_PAN_ARM_TIMEOUT + 0.1)

            # Next drag, no space held: must draw, not pan.
            pixels_before = len(canvas.layers[canvas.active_layer_index].pixels)
            await pilot.mouse_down(canvas, offset=(3, 3))
            await pilot._post_mouse_events(
                [MouseMove], canvas, offset=(6, 3), button=1
            )
            await pilot.mouse_up(canvas, offset=(6, 3))
            await pilot.pause()
            layer = canvas.layers[canvas.active_layer_index]
            return (
                scroll_after_pan,
                len(layer.pixels) - pixels_before,
                round(canvas.scroll_offset.x),
            )

    scroll_after_pan, drawn, scroll_after_draw = asyncio.run(main())
    assert drawn > 0  # the drag drew pixels
    assert scroll_after_draw == scroll_after_pan  # and did not pan


def test_repeat_pans_while_space_held() -> None:
    """Holding space and doing several drags in a row pans each time —
    auto-repeat presses keep the arm fresh across mouse-ups."""

    async def main() -> list[int]:
        app = _make_app("stick")
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            canvas = await _big_canvas(pilot, ws)
            canvas.focus()
            await pilot.pause()

            scroll_positions: list[int] = []
            canvas.post_message(Key("space", " "))
            await pilot.pause()
            for _ in range(3):
                # Simulate held-space auto-repeat between drags.
                canvas.post_message(Key("space", " "))
                await pilot.mouse_down(canvas, offset=(5, 5))
                await pilot._post_mouse_events(
                    [MouseMove], canvas, offset=(10, 5), button=1
                )
                await pilot.mouse_up(canvas, offset=(10, 5))
                await pilot.pause()
                scroll_positions.append(round(canvas.scroll_offset.x))
            return scroll_positions

    positions = asyncio.run(main())
    # Each drag pans further: strictly increasing scroll offsets.
    assert positions == sorted(positions)
    assert len(set(positions)) == len(positions)
