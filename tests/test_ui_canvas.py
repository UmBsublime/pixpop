"""Snapshot tests for canvas behaviors."""

import pytest

from tests.snapshot_helpers import SnapshotPaintApp

pytestmark = pytest.mark.canvas


def test_canvas_snapshot(snap_compare) -> None:
    """Capture a baseline snapshot of the default UI."""
    assert snap_compare(SnapshotPaintApp(), terminal_size=(120, 60))
