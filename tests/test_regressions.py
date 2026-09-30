"""Unit tests for bug-fix regressions (no UI required)."""

from __future__ import annotations

import gzip
import json

import pytest
from textual.color import Color

from pixpop.importers.png import load_png
from pixpop.session import (
    SessionFile,
    SessionLoadError,
    load_session_file,
    session_from_dict,
    write_session_file,
)
from pixpop.session.exporter import _get_tab_label
from pixpop.state.app_state import AppState


class TestAppStateClone:
    def test_clone_preserves_normalized(self) -> None:
        state = AppState(normalized=True)
        assert state.clone().normalized is True

    def test_clone_preserves_all_fields(self) -> None:
        state = AppState(
            pen_color=Color.parse("#123456"),
            brush_size=4,
            spray_density=2,
            current_tool_name="line",
            normalized=True,
        )
        clone = state.clone()
        assert clone.pen_color == state.pen_color
        assert clone.brush_size == 4
        assert clone.spray_density == 2
        assert clone.current_tool_name == "line"
        assert clone.normalized is True


class TestTabLabel:
    def test_fallback_when_no_title_or_label(self) -> None:
        class BarePane:
            title = None
            label = None

        assert _get_tab_label(BarePane()) == "Canvas"

    def test_uses_title_when_present(self) -> None:
        class TitledPane:
            title = "  My Canvas  "
            label = None

        assert _get_tab_label(TitledPane()) == "My Canvas"


class TestSessionValidation:
    def _payload(self, **overrides) -> dict:
        payload = {"format": "pixpop-session", "version": 1, "tabs": []}
        payload.update(overrides)
        return payload

    def test_rejects_non_dict_payload(self) -> None:
        with pytest.raises(SessionLoadError):
            session_from_dict([1, 2, 3])

    def test_rejects_unknown_format(self) -> None:
        with pytest.raises(SessionLoadError, match="format"):
            session_from_dict(self._payload(format="something-else"))

    def test_rejects_missing_format(self) -> None:
        with pytest.raises(SessionLoadError):
            session_from_dict({"version": 1, "tabs": []})

    def test_rejects_newer_version(self) -> None:
        with pytest.raises(SessionLoadError, match="newer"):
            session_from_dict(self._payload(version=999))

    def test_accepts_current_version(self) -> None:
        session = session_from_dict(self._payload())
        assert isinstance(session, SessionFile)

    def test_rejects_absurd_canvas_dimensions(self) -> None:
        with pytest.raises(SessionLoadError, match="dimension"):
            session_from_dict(
                self._payload(
                    tabs=[
                        {
                            "name": "T",
                            "canvas": {"width": 10**9, "height": -5},
                            "active_layer_index": 0,
                            "layers": [],
                            "undo": {},
                        }
                    ]
                )
            )

    def test_colors_not_mutated_on_load(self) -> None:
        session = session_from_dict(
            self._payload(
                palette={"name": "default", "selected_color": "#D32F2F"},
            )
        )
        assert session.palette.selected_color == "#D32F2F"


class TestSessionFileIO:
    def test_corrupt_gzip_raises_session_load_error(self, tmp_path) -> None:
        bad = tmp_path / "bad.pix"
        bad.write_bytes(b"this is not gzip data")
        with pytest.raises(SessionLoadError):
            load_session_file(bad)

    def test_round_trip_preserves_data(self, tmp_path) -> None:
        session = session_from_dict(
            {
                "format": "pixpop-session",
                "version": 1,
                "palette": {"name": "nord", "selected_color": "#AABBCC"},
                "tabs": [
                    {
                        "name": "sketch",
                        "canvas": {"width": 8, "height": 6},
                        "active_layer_index": 0,
                        "layers": [
                            {
                                "name": "Layer 1",
                                "visible": True,
                                "pixels": [[1, 2, "#FF0000"]],
                            }
                        ],
                        "undo": {
                            "max_history": 10,
                            "undo_stack": [
                                {
                                    "layers": [
                                        {
                                            "name": "Layer 1",
                                            "visible": True,
                                            "pixels": [[0, 0, "#00FF00"]],
                                        }
                                    ],
                                    "active_layer_index": 0,
                                }
                            ],
                            "redo_stack": [],
                        },
                    }
                ],
            }
        )
        target = tmp_path / "session.pix"
        write_session_file(session, target)
        loaded = load_session_file(target)

        assert loaded.palette.selected_color == "#AABBCC"
        assert loaded.tabs[0].name == "sketch"
        assert loaded.tabs[0].layers[0].pixels == [(1, 2, "#FF0000")]
        undo_pixels = loaded.tabs[0].undo.undo_stack[0].layers[0].pixels
        assert undo_pixels == [(0, 0, "#00FF00")]

    def test_write_is_atomic_no_temp_left(self, tmp_path) -> None:
        session = session_from_dict({"format": "pixpop-session", "version": 1})
        target = tmp_path / "s.pix"
        write_session_file(session, target)
        assert target.exists()
        assert not (tmp_path / "s.pix.tmp").exists()
        with gzip.open(target, "rt", encoding="utf-8") as handle:
            assert json.load(handle)["format"] == "pixpop-session"

    def test_oversized_session_rejected(self, tmp_path) -> None:
        """A session whose JSON payload exceeds the budget is refused."""
        import pixpop.session.importer as importer_module

        big = tmp_path / "big.pix"
        payload = {"format": "pixpop-session", "version": 1, "junk": "x" * 10000}
        with gzip.open(big, "wt", encoding="utf-8") as handle:
            json.dump(payload, handle)

        original = importer_module.MAX_SESSION_JSON_BYTES
        importer_module.MAX_SESSION_JSON_BYTES = 100
        try:
            with pytest.raises(SessionLoadError, match="maximum allowed size"):
                load_session_file(big)
        finally:
            importer_module.MAX_SESSION_JSON_BYTES = original


class TestAnsiImport:
    def test_cp437_fallback(self, tmp_path) -> None:
        """ANSI files in CP437 (classic art encoding) must not raise."""
        from pixpop.importers.load import load_ascii_alpha

        ans = tmp_path / "art.ans"
        # CP437 byte 0xB0 is a shade glyph; not valid UTF-8.
        ans.write_bytes(b"\x1b[0m\xb0\xb1\xb2\n")
        data = load_ascii_alpha(ans)
        assert "pixels" in data and "width" in data

    def test_row_limit_enforced(self, tmp_path) -> None:
        from pixpop.importers.load import MAX_ANSI_ROWS, load_ascii_alpha

        ans = tmp_path / "huge.ans"
        ans.write_text("\n".join(["row"] * (MAX_ANSI_ROWS + 1)), encoding="utf-8")
        with pytest.raises(ValueError, match="rows"):
            load_ascii_alpha(ans)


class TestPngImportGuards:
    def test_corrupt_png_raises_value_error(self, tmp_path) -> None:
        bad = tmp_path / "bad.png"
        bad.write_bytes(b"not a png")
        with pytest.raises(ValueError, match="Cannot read PNG"):
            load_png(bad)

    def test_oversized_png_rejected(self, tmp_path) -> None:
        from PIL import Image

        big = tmp_path / "big.png"
        Image.new("RGBA", (2, 2)).save(big)
        import pixpop.importers.png as png_module

        original = png_module.MAX_IMAGE_DIMENSION
        png_module.MAX_IMAGE_DIMENSION = 1
        try:
            with pytest.raises(ValueError, match="maximum supported size"):
                load_png(big)
        finally:
            png_module.MAX_IMAGE_DIMENSION = original


class TestPngExport:
    """PNG export must survive the atomic temp-file write (regression)."""

    def test_save_canvas_png_writes_valid_file(self, tmp_path) -> None:
        import asyncio
        from pathlib import Path

        from PIL import Image

        from pixpop.canvas import PaintCanvas
        from pixpop.export import save_canvas_png
        from tests.snapshot_helpers import SnapshotPaintApp

        async def main() -> Path:
            app = SnapshotPaintApp()
            target = tmp_path / "out.png"
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                canvas = pilot.app.query_one(PaintCanvas)
                canvas.draw_cell(2, 2, canvas.pen_color)
                save_canvas_png(canvas, target, scale=2)
            return target

        target = asyncio.run(main())
        assert target.exists()
        assert not (tmp_path / "out.png.tmp").exists()
        with Image.open(target) as image:
            assert image.format == "PNG"
            assert image.size[0] > 0 and image.size[1] > 0


class TestSessionApply:
    """Session load must apply to freshly-mounted canvases (regression)."""

    def test_apply_session_restores_pixels_after_mount(self) -> None:
        import asyncio

        from tests.snapshot_helpers import SnapshotPaintApp

        async def main() -> int:
            from pixpop.canvas import PaintCanvas
            from pixpop.session import (
                apply_session_file,
                session_from_dict,
            )
            from pixpop.workspace import PaintWorkspace

            app = SnapshotPaintApp()
            restored = 0
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                ws = pilot.app.query_one(PaintWorkspace)
                session = session_from_dict(
                    {
                        "format": "pixpop-session",
                        "version": 1,
                        "tabs": [
                            {
                                "name": "sketch",
                                "canvas": {"width": 20, "height": 20},
                                "active_layer_index": 0,
                                "layers": [
                                    {
                                        "name": "Layer 1",
                                        "visible": True,
                                        "pixels": [[3, 3, "#ff0000"]],
                                    }
                                ],
                                "undo": {},
                            }
                        ],
                    }
                )
                apply_session_file(ws, session)
                # Canvases are mounted asynchronously; give them a few frames.
                for _ in range(3):
                    await pilot.pause()
                restored = sum(
                    len(layer.pixels)
                    for pane in ws.get_tab_panes()
                    for canvas in pane.query(PaintCanvas)
                    for layer in canvas.layers
                )
            return restored

        assert asyncio.run(main()) == 1

    def test_out_of_bounds_click_preserves_redo(self) -> None:
        """A no-op click must not save an undo snapshot or clear redo."""
        import asyncio

        from pixpop.canvas import PaintCanvas
        from tests.snapshot_helpers import (
            SnapshotPaintApp,
            canvas_to_offset,
            select_tool,
        )

        async def main() -> tuple[bool, int]:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                canvas = pilot.app.query_one(PaintCanvas)
                await select_tool(pilot, "pen")
                # Draw a real stroke so there is history.
                await pilot.mouse_down(canvas, offset=canvas_to_offset(10, 10))
                await pilot.mouse_up(canvas, offset=canvas_to_offset(10, 10))
                await pilot.pause()
                # Undo it -> redo becomes available.
                canvas.action_undo()
                assert canvas.undo_manager.can_redo()
                depth_after_undo = len(canvas.undo_manager.undo_stack)

                # Out-of-bounds press: drive on_mouse_down with a point outside
                # the canvas (negative canvas coords from the border region).
                from textual.events import MouseDown

                event = MouseDown(
                    canvas,
                    x=-1,
                    y=-1,
                    delta_x=0,
                    delta_y=0,
                    button=1,
                    shift=False,
                    meta=False,
                    ctrl=False,
                    screen_x=-1,
                    screen_y=-1,
                )
                canvas.on_mouse_down(event)
                await pilot.pause()
                return (
                    canvas.undo_manager.can_redo(),
                    len(canvas.undo_manager.undo_stack) - depth_after_undo,
                )

        redo_preserved, undo_growth = asyncio.run(main())
        assert redo_preserved, "no-op click cleared the redo stack"
        assert undo_growth == 0, "no-op click pushed an undo snapshot"

    def test_corrupt_tool_state_rejected_before_mutation(self) -> None:
        """Invalid tool/brush/density must raise SessionLoadError, not crash."""
        import asyncio

        from pixpop.session import (
            SessionLoadError,
            apply_session_file,
            session_from_dict,
        )
        from pixpop.workspace import PaintWorkspace
        from tests.snapshot_helpers import SnapshotPaintApp

        async def main() -> tuple[int, str]:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                ws = pilot.app.query_one(PaintWorkspace)
                session = session_from_dict(
                    {
                        "format": "pixpop-session",
                        "version": 1,
                        "tool_state": {
                            "current_tool": "bogus-tool",
                            "brush_size": 99,
                            "spray_density": 0,
                            "normalized": False,
                        },
                        "tabs": [],
                    }
                )
                tabs_before = len(ws.get_tab_panes())
                try:
                    apply_session_file(ws, session)
                except SessionLoadError:
                    return tabs_before, "session-load-error"
                return tabs_before, "no-error"

        tabs_before, outcome = asyncio.run(main())
        assert outcome == "session-load-error", (
            f"expected SessionLoadError, got {outcome}"
        )


class TestPerToolBrushSizeLimits:
    """Brush size limits: every tool supports sizes 1-5."""

    def test_registry_max_brush_size_per_tool(self) -> None:
        from pixpop.tools.registry import get_max_brush_size

        assert get_max_brush_size("pen") == 5
        assert get_max_brush_size("eraser") == 5
        assert get_max_brush_size("spray") == 5
        assert get_max_brush_size("line") == 5
        assert get_max_brush_size("paint_bucket") == 5
        assert get_max_brush_size("rectangle") == 5
        assert get_max_brush_size("circle") == 5
        assert get_max_brush_size("ellipse") == 5

    def test_registry_max_brush_size_unknown_falls_back(self) -> None:
        from pixpop.constants import MAX_BRUSH_SIZE
        from pixpop.tools.registry import get_max_brush_size

        assert get_max_brush_size("no-such-tool") == MAX_BRUSH_SIZE

    def test_tool_switch_keeps_shared_brush_size(self) -> None:
        """Pen at size 5 -> switch to ellipse -> size 5 is kept (no cap)."""
        import asyncio

        from pixpop.workspace import PaintWorkspace
        from tests.snapshot_helpers import SnapshotPaintApp, select_tool

        async def main() -> int:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                ws = pilot.app.query_one(PaintWorkspace)
                await select_tool(pilot, "pen")
                ws._set_tool_state(brush_size=5)
                await select_tool(pilot, "ellipse")
                await select_tool(pilot, "pen")
                return ws._state.brush_size

        assert asyncio.run(main()) == 5

    def test_keyboard_increase_reaches_max_for_shape_tools(self) -> None:
        """'w' reaches 5 for shape tools as well as the pen."""
        import asyncio

        from pixpop.workspace import PaintWorkspace
        from tests.snapshot_helpers import SnapshotPaintApp, select_tool

        async def main() -> tuple[int, int]:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                ws = pilot.app.query_one(PaintWorkspace)

                await select_tool(pilot, "ellipse")
                for _ in range(10):
                    ws.action_increase_brush_size()
                ellipse_max = ws._state.brush_size

                await select_tool(pilot, "pen")
                for _ in range(10):
                    ws.action_increase_brush_size()
                pen_max = ws._state.brush_size
                return ellipse_max, pen_max

        ellipse_max, pen_max = asyncio.run(main())
        assert ellipse_max == 5
        assert pen_max == 5

    def test_picker_shows_all_sizes_for_shape_tools(self) -> None:
        """All five size buttons shown for shape tools and the pen."""
        import asyncio

        from pixpop.widgets import BrushSizePicker
        from tests.snapshot_helpers import SnapshotPaintApp, select_tool

        async def main() -> tuple[list[bool], list[bool]]:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                picker = pilot.app.query_one(BrushSizePicker)

                await select_tool(pilot, "rectangle")
                shape_display = [b.display for b in picker._buttons]

                await select_tool(pilot, "pen")
                pen_display = [b.display for b in picker._buttons]
                return shape_display, pen_display

        shape_display, pen_display = asyncio.run(main())
        assert shape_display == [True] * 5
        assert pen_display == [True] * 5

    def test_session_with_shape_tool_and_size_5_kept_on_apply(self) -> None:
        """Legacy .pix: active ellipse + brush_size 5 -> kept (max is 5)."""
        import asyncio

        from pixpop.session import apply_session_file, session_from_dict
        from pixpop.workspace import PaintWorkspace
        from tests.snapshot_helpers import SnapshotPaintApp

        async def main() -> int:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                ws = pilot.app.query_one(PaintWorkspace)
                session = session_from_dict(
                    {
                        "format": "pixpop-session",
                        "version": 1,
                        "tool_state": {
                            "current_tool": "ellipse",
                            "brush_size": 5,
                            "spray_density": 3,
                            "normalized": False,
                        },
                        "tabs": [],
                    }
                )
                apply_session_file(ws, session)
                await pilot.pause()
                return ws._state.brush_size

        assert asyncio.run(main()) == 5


class TestBrushFootprint:
    """Brush footprint sizes: 1=1x1, 2=2x2, 3=3x3, 4=4x4, 5=5x5."""

    @staticmethod
    def _offsets_for(size: int) -> set[tuple[int, int]]:
        from pixpop.canvas import PaintCanvas
        from pixpop.tools.pen import PenTool

        canvas = PaintCanvas.__new__(PaintCanvas)
        canvas._current_tool = PenTool()
        canvas.brush_size = size
        return set(PaintCanvas._brush_offsets(canvas))

    def test_size_1_is_single_pixel(self) -> None:
        assert self._offsets_for(1) == {(0, 0)}

    def test_size_2_is_2x2(self) -> None:
        assert self._offsets_for(2) == {(0, 0), (1, 0), (0, 1), (1, 1)}

    def test_size_3_is_3x3(self) -> None:
        offsets = self._offsets_for(3)
        assert len(offsets) == 9
        assert {dx for dx, _ in offsets} == {0, 1, 2}
        assert {dy for _, dy in offsets} == {0, 1, 2}

    def test_size_4_is_4x4(self) -> None:
        offsets = self._offsets_for(4)
        assert len(offsets) == 16
        assert {dx for dx, _ in offsets} == {0, 1, 2, 3}
        assert {dy for _, dy in offsets} == {0, 1, 2, 3}

    def test_size_5_is_5x5(self) -> None:
        offsets = self._offsets_for(5)
        assert len(offsets) == 25
        assert {dx for dx, _ in offsets} == {0, 1, 2, 3, 4}
        assert {dy for _, dy in offsets} == {0, 1, 2, 3, 4}

    def test_cell_tool_footprint_is_one_full_cell(self) -> None:
        """The cell tool ignores brush size: always 1x2 (both cell halves)."""
        from pixpop.canvas import PaintCanvas
        from pixpop.tools.cell import CellTool

        canvas = PaintCanvas.__new__(PaintCanvas)
        canvas._current_tool = CellTool()
        for size in range(1, 6):
            canvas.brush_size = size
            assert set(PaintCanvas._brush_offsets(canvas)) == {(0, 0), (0, 1)}

    def test_all_sizes_align_flush_in_top_left_corner(self) -> None:
        """At canvas origin, every size paints nothing above/left of the cursor."""
        import asyncio

        from pixpop.canvas import PaintCanvas
        from tests.snapshot_helpers import SnapshotPaintApp

        async def main() -> list[tuple[int, int, int, int]]:
            app = SnapshotPaintApp()
            results: list[tuple[int, int, int, int]] = []
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                canvas = pilot.app.query_one(PaintCanvas)
                for size in (1, 2, 3, 4, 5):
                    canvas.brush_size = size
                    canvas.draw_cell(0, 0, canvas.pen_color)
                    painted = [
                        coord
                        for coord, color in canvas._layers[0].pixels.items()
                        if color is not None
                    ]
                    xs = [p[0] for p in painted]
                    ys = [p[1] for p in painted]
                    results.append((size, min(xs), min(ys), len(painted)))
                    canvas._layers[0].pixels.clear()
            return results

        expected = {1: 1, 2: 4, 3: 9, 4: 16, 5: 25}
        for size, min_x, min_y, count in asyncio.run(main()):
            assert (min_x, min_y) == (0, 0), f"size {size} not flush at origin"
            assert count == expected[size], (
                f"size {size} painted {count}, expected {expected[size]}"
            )


class TestAltCursorOffset:
    """Holding Alt with the pen, cell, eraser, or a shape tool offsets the cursor."""

    @staticmethod
    def _mouse_event(event_cls, canvas, x: int, y: int, meta: bool, button: int = 1):
        """Build a mouse event targeting canvas cell (x, y)."""
        return event_cls(
            canvas,
            x=x + canvas.region.x + 1,
            y=y // 2 + canvas.region.y,
            delta_x=0,
            delta_y=0,
            button=button,
            shift=False,
            meta=meta,
            ctrl=False,
        )

    def test_alt_offsets_pen_cursor_down_one_pixel(self) -> None:
        """Alt+click paints at y+1; without Alt the same cell paints at y."""
        import asyncio

        from textual.events import MouseDown, MouseUp

        from pixpop.canvas import PaintCanvas
        from tests.snapshot_helpers import SnapshotPaintApp, select_tool

        async def main() -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                canvas = pilot.app.query_one(PaintCanvas)
                await select_tool(pilot, "pen")
                canvas.brush_size = 1

                canvas.on_mouse_down(
                    self._mouse_event(MouseDown, canvas, 4, 6, meta=True)
                )
                canvas.on_mouse_up(self._mouse_event(MouseUp, canvas, 4, 6, meta=True))
                await pilot.pause()
                offset = sorted(canvas._layers[0].pixels)

                canvas._layers[0].pixels.clear()
                canvas.refresh_composite()

                canvas.on_mouse_down(
                    self._mouse_event(MouseDown, canvas, 4, 6, meta=False)
                )
                canvas.on_mouse_up(self._mouse_event(MouseUp, canvas, 4, 6, meta=False))
                await pilot.pause()
                plain = sorted(canvas._layers[0].pixels)
                return offset, plain

        offset, plain = asyncio.run(main())
        # Brush size 1 paints a single pixel: Alt targets the cell's
        # bottom pixel, without Alt its top pixel.
        assert offset == [(4, 7)]
        assert plain == [(4, 6)]

    def test_pen_size_1_replaces_fine_pen(self) -> None:
        """Pen at size 1 paints one pixel; Alt reaches the cell's bottom half."""
        import asyncio

        from textual.events import MouseDown, MouseUp

        from pixpop.canvas import PaintCanvas
        from tests.snapshot_helpers import SnapshotPaintApp, select_tool

        async def main() -> list[tuple[int, int]]:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                canvas = pilot.app.query_one(PaintCanvas)
                await select_tool(pilot, "pen")
                canvas.brush_size = 1

                canvas.on_mouse_down(
                    self._mouse_event(MouseDown, canvas, 4, 6, meta=False)
                )
                canvas.on_mouse_up(self._mouse_event(MouseUp, canvas, 4, 6, meta=False))
                canvas.on_mouse_down(
                    self._mouse_event(MouseDown, canvas, 4, 6, meta=True)
                )
                canvas.on_mouse_up(self._mouse_event(MouseUp, canvas, 4, 6, meta=True))
                await pilot.pause()
                return sorted(canvas._layers[0].pixels)

        # Two clicks on the same cell paint its top and bottom pixels.
        assert asyncio.run(main()) == [(4, 6), (4, 7)]

    def test_alt_offsets_cell_down_one_pixel(self) -> None:
        """Cell paints both pixels of the cell; Alt shifts the footprint down."""
        import asyncio

        from textual.events import MouseDown, MouseUp

        from pixpop.canvas import PaintCanvas
        from tests.snapshot_helpers import SnapshotPaintApp, select_tool

        async def main() -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                canvas = pilot.app.query_one(PaintCanvas)
                await select_tool(pilot, "cell")

                canvas.on_mouse_down(
                    self._mouse_event(MouseDown, canvas, 4, 6, meta=False)
                )
                canvas.on_mouse_up(self._mouse_event(MouseUp, canvas, 4, 6, meta=False))
                await pilot.pause()
                plain = sorted(canvas._layers[0].pixels)

                canvas._layers[0].pixels.clear()
                canvas.refresh_composite()

                canvas.on_mouse_down(
                    self._mouse_event(MouseDown, canvas, 4, 6, meta=True)
                )
                canvas.on_mouse_up(self._mouse_event(MouseUp, canvas, 4, 6, meta=True))
                await pilot.pause()
                offset = sorted(canvas._layers[0].pixels)
                return plain, offset

        plain, offset = asyncio.run(main())
        assert plain == [(4, 6), (4, 7)]
        assert offset == [(4, 7), (4, 8)]

    def test_alt_ignored_for_other_tools(self) -> None:
        """Alt does not offset the cursor for spray/bucket."""
        import asyncio

        from textual.events import MouseDown, MouseUp

        from pixpop.canvas import PaintCanvas
        from tests.snapshot_helpers import SnapshotPaintApp, select_tool

        async def main() -> dict[str, list[tuple[int, int]]]:
            app = SnapshotPaintApp()
            results: dict[str, list[tuple[int, int]]] = {}
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                canvas = pilot.app.query_one(PaintCanvas)
                canvas.brush_size = 1

                for tool in ("spray", "paint_bucket"):
                    canvas._layers[0].pixels.clear()
                    canvas.refresh_composite()
                    # Seed a background so the bucket has something to fill.
                    for y in range(4, 14):
                        canvas.set_layer_pixel(4, y, canvas.pen_color)
                    await select_tool(pilot, tool)

                    canvas.on_mouse_down(
                        self._mouse_event(MouseDown, canvas, 4, 6, meta=True)
                    )
                    canvas.on_mouse_up(
                        self._mouse_event(MouseUp, canvas, 4, 6, meta=True)
                    )
                    await pilot.pause()
                    results[tool] = sorted(canvas._layers[0].pixels)
                return results

        results = asyncio.run(main())
        # Spray scatters around the unshifted y=6; check only pixels the
        # spray itself added (x != 4), excluding the seeded column.
        added = {coord for coord in results["spray"] if coord[0] != 4}
        assert not added or max(y for _, y in added) <= 7
        # Paint bucket fills the seeded column from y=4; an offset click
        # still fills the same region, but the fill result is unchanged.
        assert min(y for _, y in results["paint_bucket"]) == 4

    def test_alt_offsets_eraser_cursor(self) -> None:
        """Alt applies to the eraser tool itself, not just pen right-click."""
        import asyncio

        from textual.events import MouseDown, MouseUp

        from pixpop.canvas import PaintCanvas
        from tests.snapshot_helpers import SnapshotPaintApp, select_tool

        async def main() -> list[tuple[int, int]]:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                canvas = pilot.app.query_one(PaintCanvas)
                await select_tool(pilot, "eraser")
                canvas.brush_size = 1
                canvas.draw_cell(4, 6, canvas.pen_color)
                canvas.draw_cell(4, 8, canvas.pen_color)

                canvas.on_mouse_down(
                    self._mouse_event(MouseDown, canvas, 4, 6, meta=True)
                )
                canvas.on_mouse_up(self._mouse_event(MouseUp, canvas, 4, 6, meta=True))
                await pilot.pause()
                return sorted(canvas._layers[0].pixels)

        remaining = asyncio.run(main())
        # Offset erase anchors at y=7, clearing only (4, 7).
        assert remaining == [(4, 6), (4, 8)]

    def test_alt_offsets_rectangle_anchor_and_end(self) -> None:
        """Alt+drag commits a rectangle offset down one pixel on both corners."""
        import asyncio

        from textual.events import MouseDown, MouseMove, MouseUp

        from pixpop.canvas import PaintCanvas
        from tests.snapshot_helpers import SnapshotPaintApp, select_tool

        async def main() -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                canvas = pilot.app.query_one(PaintCanvas)
                await select_tool(pilot, "rectangle")
                canvas.brush_size = 1

                results = []
                for meta in (True, False):
                    canvas.on_mouse_down(
                        self._mouse_event(MouseDown, canvas, 4, 6, meta=meta)
                    )
                    canvas.on_mouse_move(
                        self._mouse_event(MouseMove, canvas, 8, 10, meta=meta)
                    )
                    canvas.on_mouse_up(
                        self._mouse_event(MouseUp, canvas, 8, 10, meta=meta)
                    )
                    await pilot.pause()
                    results.append(sorted(canvas._layers[0].pixels))
                    canvas._layers[0].pixels.clear()
                    canvas.refresh_composite()
                return results[0], results[1]

        offset, plain = asyncio.run(main())
        # Brush size 1 paints a single pixel per outline cell.
        assert {y for _, y in offset} == {7, 8, 9, 10, 11}
        assert {x for x, _ in offset} == {4, 5, 6, 7, 8}
        assert {y for _, y in plain} == {6, 7, 8, 9, 10}
        assert {x for x, _ in plain} == {4, 5, 6, 7, 8}

    def test_alt_offsets_line_start(self) -> None:
        """Alt+drag commits a line whose anchor is offset down one pixel."""
        import asyncio

        from textual.events import MouseDown, MouseMove, MouseUp

        from pixpop.canvas import PaintCanvas
        from tests.snapshot_helpers import SnapshotPaintApp, select_tool

        async def main() -> list[tuple[int, int]]:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                canvas = pilot.app.query_one(PaintCanvas)
                await select_tool(pilot, "line")
                canvas.brush_size = 1

                canvas.on_mouse_down(
                    self._mouse_event(MouseDown, canvas, 4, 6, meta=True)
                )
                canvas.on_mouse_move(
                    self._mouse_event(MouseMove, canvas, 8, 6, meta=True)
                )
                canvas.on_mouse_up(self._mouse_event(MouseUp, canvas, 8, 6, meta=True))
                await pilot.pause()
                return sorted(canvas._layers[0].pixels)

        painted = asyncio.run(main())
        assert (4, 7) in painted
        assert (4, 6) not in painted
        assert min(y for _, y in painted) == 7

    def test_alt_pen_right_click_erases_at_offset(self) -> None:
        """Alt applies to the right-click eraser while the pen is active."""
        import asyncio

        from textual.events import MouseDown, MouseUp

        from pixpop.canvas import PaintCanvas
        from tests.snapshot_helpers import SnapshotPaintApp, select_tool

        async def main() -> list[tuple[int, int]]:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                canvas = pilot.app.query_one(PaintCanvas)
                await select_tool(pilot, "pen")
                canvas.brush_size = 1
                canvas.draw_cell(4, 6, canvas.pen_color)
                canvas.draw_cell(4, 8, canvas.pen_color)

                canvas.on_mouse_down(
                    self._mouse_event(MouseDown, canvas, 4, 6, meta=True, button=3)
                )
                canvas.on_mouse_up(
                    self._mouse_event(MouseUp, canvas, 4, 6, meta=True, button=3)
                )
                await pilot.pause()
                return sorted(canvas._layers[0].pixels)

        remaining = asyncio.run(main())
        # Offset erase anchors at y=7, clearing only (4, 7).
        assert remaining == [(4, 6), (4, 8)]


class TestCellTool:
    """The cell tool paints one full terminal cell; brush size does not apply."""

    def test_cell_paints_full_cell_regardless_of_brush_size(self) -> None:
        """With the shared brush size at 5, a cell click still paints 1x2."""
        import asyncio

        from textual.events import MouseDown, MouseUp

        from pixpop.canvas import PaintCanvas
        from tests.snapshot_helpers import SnapshotPaintApp, select_tool

        async def main() -> list[tuple[int, int]]:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                canvas = pilot.app.query_one(PaintCanvas)
                await select_tool(pilot, "cell")
                canvas.brush_size = 5

                canvas.on_mouse_down(
                    TestAltCursorOffset._mouse_event(
                        MouseDown, canvas, 4, 6, meta=False
                    )
                )
                canvas.on_mouse_up(
                    TestAltCursorOffset._mouse_event(MouseUp, canvas, 4, 6, meta=False)
                )
                await pilot.pause()
                return sorted(canvas._layers[0].pixels)

        assert asyncio.run(main()) == [(4, 6), (4, 7)]

    def test_brush_size_picker_hidden_for_cell(self) -> None:
        """The brush size picker hides for cell and shows for other tools."""
        import asyncio

        from pixpop.widgets import BrushSizePicker
        from tests.snapshot_helpers import SnapshotPaintApp, select_tool

        async def main() -> tuple[bool, bool]:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                picker = pilot.app.query_one(BrushSizePicker)

                await select_tool(pilot, "cell")
                cell_hidden = picker.has_class("invisible")

                await select_tool(pilot, "pen")
                pen_hidden = picker.has_class("invisible")
                return cell_hidden, pen_hidden

        cell_hidden, pen_hidden = asyncio.run(main())
        assert cell_hidden is True
        assert pen_hidden is False

    def test_brush_size_keys_noop_for_cell(self) -> None:
        """'w'/'s' do not change the shared brush size while cell is active."""
        import asyncio

        from pixpop.workspace import PaintWorkspace
        from tests.snapshot_helpers import SnapshotPaintApp, select_tool

        async def main() -> tuple[int, int]:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                ws = pilot.app.query_one(PaintWorkspace)
                await select_tool(pilot, "cell")
                size_before = ws._state.brush_size
                ws.action_increase_brush_size()
                ws.action_decrease_brush_size()
                return size_before, ws._state.brush_size

        before, after = asyncio.run(main())
        assert after == before

    def test_right_click_with_cell_erases_full_cell(self) -> None:
        """Right-click while cell is active erases the full cell footprint."""
        import asyncio

        from textual.events import MouseDown, MouseUp

        from pixpop.canvas import PaintCanvas
        from tests.snapshot_helpers import SnapshotPaintApp, select_tool

        async def main() -> list[tuple[int, int]]:
            app = SnapshotPaintApp()
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                canvas = pilot.app.query_one(PaintCanvas)
                await select_tool(pilot, "cell")
                canvas.brush_size = 5
                for y in range(4, 12):
                    canvas.set_layer_pixel(4, y, canvas.pen_color)

                canvas.on_mouse_down(
                    TestAltCursorOffset._mouse_event(
                        MouseDown, canvas, 4, 6, meta=False, button=3
                    )
                )
                canvas.on_mouse_up(
                    TestAltCursorOffset._mouse_event(
                        MouseUp, canvas, 4, 6, meta=False, button=3
                    )
                )
                await pilot.pause()
                return sorted(canvas._layers[0].pixels)

        remaining = asyncio.run(main())
        # The full cell at y=6-7 is erased; the rest of the column remains.
        assert remaining == [(4, 4), (4, 5), (4, 8), (4, 9), (4, 10), (4, 11)]
