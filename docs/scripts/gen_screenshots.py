"""Generate documentation screenshots by driving the app with a Textual pilot.

Run from the repository root:

    uv run python docs/scripts/gen_screenshots.py

SVGs are written to docs/assets/images/ and committed to the repo so the
docs build does not need to regenerate them.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from textual.color import Color
from textual.geometry import Offset

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tests.snapshot_helpers import (  # noqa: E402
    SnapshotPaintApp,
    canvas_to_offset,
    middle_click,
    rename_active_layer,
    rename_active_tab,
    select_tool,
)

from pixpop.canvas import PaintCanvas  # noqa: E402
from pixpop.widgets import LayerPicker, ToolPicker  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "assets" / "images"
TERMINAL_SIZE = (110, 36)


def save(app: SnapshotPaintApp, name: str) -> None:
    """Write an SVG screenshot of the current screen."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / name
    path.write_text(app.export_screenshot(simplify=True), encoding="utf-8")
    print(f"wrote {path.relative_to(REPO_ROOT)}")


def scene_stamp(app: SnapshotPaintApp) -> None:
    """Draw a simple scene directly on the active layer (fast, deterministic)."""
    canvas = app.query_one(PaintCanvas)
    grass = Color.parse("#5d8a4a")
    sky = Color.parse("#3a6ea5")
    sun = Color.parse("#e0b341")

    width, height = canvas.width, canvas.height
    horizon = int(height * 0.62)

    # Sky and grass bands.
    for y in range(height):
        color = sky if y < horizon else grass
        for x in range(width):
            canvas.set_layer_pixel(x, y, color)

    # Blocky sun in the top-right corner.
    radius = 7
    cx, cy = width - 16, 12
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius**2:
                canvas.set_layer_pixel(x, y, sun)

    canvas.refresh_composite()


async def shot_help() -> None:
    """Help dialog showing every keybinding."""
    app = SnapshotPaintApp()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.press("?")
        await pilot.pause()
        save(app, "help-dialog.svg")


async def shot_tools() -> None:
    """Tool picker with the line tool selected and a stroke in progress."""
    app = SnapshotPaintApp()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        scene_stamp(app)
        await select_tool(pilot, "line")

        canvas = app.query_one(PaintCanvas)
        start = canvas_to_offset(10, 30)
        end = canvas_to_offset(60, 12)
        await pilot.hover(canvas, offset=start)
        await pilot.mouse_down(canvas, offset=start)
        await pilot.hover(canvas, offset=Offset((start[0] + end[0]) // 2, (start[1] + end[1]) // 2))
        await pilot.hover(canvas, offset=end)
        await pilot.pause()

        # Hover the tool picker so the tooltip column is visible.
        tool_picker = app.query_one(ToolPicker)
        await pilot.hover(tool_picker, offset=Offset(2, 2))
        await pilot.pause()
        save(app, "tools-line.svg")


async def shot_layers() -> None:
    """Multiple layers with one hidden."""
    app = SnapshotPaintApp()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        scene_stamp(app)
        rename_active_tab(pilot, "sprite.pix")

        canvas = app.query_one(PaintCanvas)
        rename_active_layer(pilot, "background")

        await pilot.press("/")  # new layer
        await pilot.pause()
        rename_active_layer(pilot, "outline")
        for x in range(20, 44):
            canvas.set_layer_pixel(x, 8, Color.parse("#1f1714"))
            canvas.set_layer_pixel(x, 24, Color.parse("#1f1714"))
        for y in range(8, 25):
            canvas.set_layer_pixel(20, y, Color.parse("#1f1714"))
            canvas.set_layer_pixel(43, y, Color.parse("#1f1714"))
        canvas.refresh_composite()

        await pilot.press("/")  # new layer
        await pilot.pause()
        rename_active_layer(pilot, "fill")

        # Middle-click inside the frame: fine pen paints both pixels of a cell.
        await middle_click(pilot, canvas, canvas_to_offset(26, 14))
        await middle_click(pilot, canvas, canvas_to_offset(30, 14))
        await middle_click(pilot, canvas, canvas_to_offset(26, 18))
        await middle_click(pilot, canvas, canvas_to_offset(30, 18))

        # Hide the outline layer so the picker shows a visibility toggle.
        canvas.set_layer_visibility(1, False)
        canvas.set_active_layer(0)
        layer_picker = app.query_one(LayerPicker)
        layer_picker.set_layers(canvas.get_layers(), canvas.active_layer_index)
        await pilot.pause()
        save(app, "layers.svg")


async def main() -> None:
    await shot_help()
    await shot_tools()
    await shot_layers()


if __name__ == "__main__":
    asyncio.run(main())
