"""Snapshot tests for layers."""

import pytest

from pixpop.canvas import PaintCanvas
from pixpop.workspace import PaintWorkspace
from tests.snapshot_helpers import (
    SnapshotPaintApp,
    canvas_to_offset,
    select_tool,
)

pytestmark = pytest.mark.layers


def test_layer_visibility_snapshot(snap_compare) -> None:
    """Capture snapshots before and after hiding the only layer."""

    async def draw_shape(pilot) -> PaintWorkspace:
        await pilot.pause()
        canvas = pilot.app.query_one(PaintCanvas)
        workspace = pilot.app.query_one(PaintWorkspace)

        await select_tool(pilot, "rectangle")
        await pilot.mouse_down(canvas, offset=canvas_to_offset(10, 10))
        await pilot.mouse_up(canvas, offset=canvas_to_offset(40, 24))

        canvas.refresh()
        return workspace

    async def run_before_visible(pilot) -> None:
        await draw_shape(pilot)

    async def run_before_hidden(pilot) -> None:
        workspace = await draw_shape(pilot)
        workspace.action_toggle_layer_visibility()
        await pilot.pause()

    assert snap_compare(
        SnapshotPaintApp(), terminal_size=(120, 60), run_before=run_before_visible
    )
    assert snap_compare(
        SnapshotPaintApp(), terminal_size=(120, 60), run_before=run_before_hidden
    )
