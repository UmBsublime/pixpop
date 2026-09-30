"""Tests for fixed-size canvases, the new-tab size dialog, and scrolling."""

from __future__ import annotations

import asyncio
from math import ceil

import pytest

from pixpop.canvas import PaintCanvas
from pixpop.screens.new_tab_dialog import NewTabDialog
from pixpop.workspace import PaintWorkspace
from tests.snapshot_helpers import SnapshotPaintApp

pytestmark = pytest.mark.functional


def test_new_tab_dialog_creates_canvas_with_chosen_size() -> None:
    """The size entered in the dialog is applied to the new tab's canvas."""

    async def main() -> tuple[int, int]:
        app = SnapshotPaintApp()
        async with app.run_test(size=(120, 60)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            ws.action_new_tab()
            await pilot.pause()

            dialog = pilot.app.screen
            assert isinstance(dialog, NewTabDialog)
            width_input = dialog.query_one("#width-input")
            height_input = dialog.query_one("#height-input")
            width_input.value = "64"
            height_input.value = "32"
            await pilot.press("enter")
            # The pane's canvas mounts asynchronously; give it a few frames.
            for _ in range(3):
                await pilot.pause()

            canvas = ws._get_canvas()
            return canvas.width, canvas.height

    assert asyncio.run(main()) == (64, 32)


def test_new_tab_dialog_prefills_with_viewport_size() -> None:
    """Before any explicit choice, the dialog pre-fills with the clamped
    viewport fit so the default creates a scrollbar-free canvas."""

    async def main() -> tuple[str, str, tuple[int, int]]:
        app = SnapshotPaintApp()
        async with app.run_test(size=(120, 60)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            canvas = ws._get_canvas()
            expected = (
                int(canvas.content_size.width),
                int(canvas.content_size.height) * 2,
            )
            ws.action_new_tab()
            await pilot.pause()
            dialog = pilot.app.screen
            assert isinstance(dialog, NewTabDialog)
            return (
                dialog.query_one("#width-input").value,
                dialog.query_one("#height-input").value,
                expected,
            )

    width_raw, height_raw, expected = asyncio.run(main())
    assert (int(width_raw), int(height_raw)) == expected


def test_new_tab_dialog_remembers_last_size() -> None:
    """The dialog pre-fills with the last chosen size within the session."""

    async def main() -> tuple[str, str]:
        app = SnapshotPaintApp()
        async with app.run_test(size=(120, 60)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)

            ws.action_new_tab()
            await pilot.pause()
            dialog = pilot.app.screen
            dialog.query_one("#width-input").value = "48"
            dialog.query_one("#height-input").value = "24"
            await pilot.press("enter")
            await pilot.pause()

            ws.action_new_tab()
            await pilot.pause()
            dialog = pilot.app.screen
            assert isinstance(dialog, NewTabDialog)
            return (
                dialog.query_one("#width-input").value,
                dialog.query_one("#height-input").value,
            )

    assert asyncio.run(main()) == ("48", "24")


def test_new_tab_dialog_cancel_creates_no_tab() -> None:
    """Escaping the dialog leaves the tab count unchanged."""

    async def main() -> int:
        app = SnapshotPaintApp()
        async with app.run_test(size=(120, 60)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            initial_count = len(ws.get_tab_panes())

            ws.action_new_tab()
            await pilot.pause()
            assert isinstance(pilot.app.screen, NewTabDialog)
            await pilot.press("escape")
            await pilot.pause()
            return len(ws.get_tab_panes()) - initial_count

    assert asyncio.run(main()) == 0


@pytest.mark.parametrize(
    "width, height",
    [
        ("abc", "32"),  # not a number
        ("32", "xyz"),  # not a number
        ("0", "32"),  # below min
        ("32", "0"),  # below min
        ("99999", "32"),  # above max
        ("32", "99999"),  # above max
    ],
)
def test_new_tab_dialog_rejects_invalid_values(width: str, height: str) -> None:
    """Invalid dimensions keep the dialog open and show an error."""

    async def main() -> tuple[bool, str]:
        app = SnapshotPaintApp()
        async with app.run_test(size=(120, 60)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            ws.action_new_tab()
            await pilot.pause()

            dialog = pilot.app.screen
            assert isinstance(dialog, NewTabDialog)
            dialog.query_one("#width-input").value = width
            dialog.query_one("#height-input").value = height
            await pilot.press("enter")
            await pilot.pause()

            still_open = isinstance(pilot.app.screen, NewTabDialog)
            error = str(pilot.app.screen.query_one("#new-tab-error").render())
            return still_open, error

    still_open, error = asyncio.run(main())
    assert still_open
    assert error.strip()


def test_startup_canvas_fits_viewport_without_scrollbars() -> None:
    """The default (startup) canvas fills the viewport and needs no scrollbars."""

    async def main() -> tuple[bool, bool, tuple[int, int], tuple[int, int]]:
        app = SnapshotPaintApp()
        async with app.run_test(size=(120, 60)) as pilot:
            # The one-time fit is deferred by a 0.1s mount timer.
            await asyncio.sleep(0.2)
            await pilot.pause()
            canvas = pilot.app.query_one(PaintCanvas)
            return (
                canvas.show_horizontal_scrollbar,
                canvas.show_vertical_scrollbar,
                (canvas.width, canvas.height),
                (
                    int(canvas.content_size.width),
                    int(canvas.content_size.height) * 2,
                ),
            )

    h_scroll, v_scroll, canvas_size, viewport_px = asyncio.run(main())
    assert not h_scroll and not v_scroll
    assert canvas_size == viewport_px


def test_startup_canvas_size_is_clamped_to_config() -> None:
    """A viewport larger than the configured max clamps to the max size."""

    async def main() -> tuple[int, int]:
        app = SnapshotPaintApp()
        # Viewport way beyond max_canvas_width/height (1024x1024).
        async with app.run_test(size=(1600, 1200)) as pilot:
            await asyncio.sleep(0.2)
            await pilot.pause()
            canvas = pilot.app.query_one(PaintCanvas)
            return canvas.width, canvas.height

    assert asyncio.run(main()) == (1024, 1024)


def test_oversized_canvas_shows_scrollbars() -> None:
    """A canvas larger than the viewport gets scrollbars and a virtual size."""

    async def main() -> tuple[bool, bool, tuple[int, int], tuple[int, int]]:
        app = SnapshotPaintApp()
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            # Choose a canvas much larger than the 60x30 terminal via dialog.
            ws.action_new_tab()
            await pilot.pause()
            dialog = pilot.app.screen
            dialog.query_one("#width-input").value = "128"
            dialog.query_one("#height-input").value = "128"
            await pilot.press("enter")
            for _ in range(3):
                await pilot.pause()

            canvas = ws._get_canvas()
            return (
                canvas.show_horizontal_scrollbar,
                canvas.show_vertical_scrollbar,
                (canvas.width, canvas.height),
                (canvas.virtual_size.width, canvas.virtual_size.height),
            )

    h_scroll, v_scroll, canvas_size, virtual_size = asyncio.run(main())
    assert h_scroll and v_scroll
    assert canvas_size == (128, 128)
    assert virtual_size == (128, ceil(128 / 2))


def test_small_canvas_has_no_scrollbars() -> None:
    """A canvas that fits the viewport shows no scrollbars."""

    async def main() -> tuple[bool, bool]:
        app = SnapshotPaintApp()
        async with app.run_test(size=(120, 60)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            ws.action_new_tab()
            await pilot.pause()
            dialog = pilot.app.screen
            dialog.query_one("#width-input").value = "16"
            dialog.query_one("#height-input").value = "8"
            await pilot.press("enter")
            for _ in range(3):
                await pilot.pause()

            canvas = ws._get_canvas()
            return (
                canvas.show_horizontal_scrollbar,
                canvas.show_vertical_scrollbar,
            )

    assert asyncio.run(main()) == (False, False)


def test_mouse_wheel_does_not_scroll() -> None:
    """Wheel events are swallowed by the canvas."""

    async def main() -> tuple[int, int]:
        app = SnapshotPaintApp()
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            canvas = pilot.app.query_one(PaintCanvas)
            # Give the canvas room to scroll: larger than the 60x30 viewport.
            canvas.resize_preserve_content(128, 128)
            await pilot.pause()
            canvas.scroll_to(10, 10, animate=False)
            await pilot.pause()
            before = (round(canvas.scroll_offset.x), round(canvas.scroll_offset.y))

            from textual.events import MouseScrollDown, MouseScrollUp

            for event_cls in (MouseScrollDown, MouseScrollUp):
                event = event_cls(
                    widget=canvas,
                    x=1,
                    y=1,
                    delta_x=0,
                    delta_y=0,
                    button=0,
                    shift=False,
                    meta=False,
                    ctrl=False,
                )
                canvas.post_message(event)
            await pilot.pause()
            after = (round(canvas.scroll_offset.x), round(canvas.scroll_offset.y))
            return before, after

    before, after = asyncio.run(main())
    assert before == (10, 10)
    assert after == before


def test_scroll_keys_do_not_scroll() -> None:
    """Arrow/page/home/end keys must not move the canvas scroll position."""

    async def main() -> tuple[int, int]:
        app = SnapshotPaintApp()
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            canvas = pilot.app.query_one(PaintCanvas)
            canvas.resize_preserve_content(128, 128)
            canvas.focus()
            await pilot.pause()

            for key in (
                "up",
                "down",
                "left",
                "right",
                "home",
                "end",
                "pageup",
                "pagedown",
                "ctrl+pageup",
                "ctrl+pagedown",
            ):
                await pilot.press(key)
            await pilot.pause()
            return (
                round(canvas.scroll_offset.x),
                round(canvas.scroll_offset.y),
            )

    assert asyncio.run(main()) == (0, 0)


def test_screen_to_canvas_coords_with_scroll_offset() -> None:
    """Scrolled mouse positions map onto the visually underlying pixel."""

    async def main() -> tuple[tuple[int, int], tuple[int, int]]:
        app = SnapshotPaintApp()
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            canvas = pilot.app.query_one(PaintCanvas)
            canvas.resize_preserve_content(128, 128)
            await pilot.pause()

            unscrolled = canvas.screen_to_canvas_coords(50, 10)
            canvas.scroll_to(20, 5, animate=False)
            await pilot.pause()
            scrolled = canvas.screen_to_canvas_coords(50, 10)
            return unscrolled, scrolled

    unscrolled, scrolled = asyncio.run(main())
    sx, sy = scrolled
    ux, uy = unscrolled
    assert sx - ux == 20  # horizontal offset shifts x by scroll amount
    assert sy - uy == 10  # vertical offset shifts y by scroll amount * 2


def test_draw_at_scrolled_position() -> None:
    """Drawing after scrolling lands on the scrolled canvas pixel."""

    async def main() -> tuple[bool, bool]:
        app = SnapshotPaintApp()
        async with app.run_test(size=(60, 30)) as pilot:
            await pilot.pause()
            canvas = pilot.app.query_one(PaintCanvas)
            canvas.resize_preserve_content(128, 128)
            canvas.current_tool = "pen"
            canvas.brush_size = 1
            await pilot.pause()

            canvas.scroll_to(10, 5, animate=False)
            await pilot.pause()

            # Click at the canvas widget's own origin: with scroll (10, 5)
            # this maps to canvas pixel (10, 10).
            await pilot.mouse_down(canvas, offset=(1, 0))
            await pilot.mouse_up(canvas, offset=(1, 0))
            await pilot.pause()

            hit = canvas.get_composited_pixel(10, 10) is not None
            miss = canvas.get_composited_pixel(0, 0) is None
            return hit, miss

    assert asyncio.run(main()) == (True, True)


def test_session_size_survives_pending_fit_timer() -> None:
    """A session-restored canvas size must not be clobbered by the deferred
    viewport-fit timer on freshly created (default-size) tabs."""

    async def main() -> tuple[int, int]:
        from pixpop.session import apply_session_file, session_from_dict

        app = SnapshotPaintApp()
        async with app.run_test(size=(120, 60)) as pilot:
            await pilot.pause()
            ws = pilot.app.query_one(PaintWorkspace)
            session = session_from_dict(
                {
                    "format": "pixpop-session",
                    "version": 1,
                    "tabs": [
                        {
                            "name": "tiny",
                            "canvas": {"width": 20, "height": 20},
                            "active_layer_index": 0,
                            "layers": [
                                {
                                    "name": "Layer 1",
                                    "visible": True,
                                    "pixels": [],
                                }
                            ],
                            "undo": {},
                        }
                    ],
                }
            )
            apply_session_file(ws, session)
            # The fit timer fires ~0.1s after mount; wait well past it.
            await asyncio.sleep(0.3)
            for _ in range(3):
                await pilot.pause()
            canvas = ws._get_canvas()
            return canvas.width, canvas.height

    assert asyncio.run(main()) == (20, 20)


def test_terminal_resize_does_not_change_canvas_size() -> None:
    """The canvas keeps its logical size when the terminal is resized."""

    async def main() -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
        app = SnapshotPaintApp()
        async with app.run_test(size=(120, 60)) as pilot:
            await pilot.pause()
            canvas = pilot.app.query_one(PaintCanvas)
            expected = (
                int(canvas.content_size.width),
                int(canvas.content_size.height) * 2,
            )
            await asyncio.sleep(0.2)  # let the one-time fit run
            await pilot.pause()
            before = (canvas.width, canvas.height)
            await pilot.resize_terminal(80, 40)
            await asyncio.sleep(0.2)  # a stray fit timer would fire here
            await pilot.pause()
            after = (canvas.width, canvas.height)
            return expected, before, after

    expected, before, after = asyncio.run(main())
    assert before == expected
    assert after == before
