"""Session import utilities."""

from __future__ import annotations

import gzip
import json
from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING

from textual.color import Color
from textual.widgets import TabPane

from pixpop.canvas import PaintCanvas
from pixpop.constants import (
    MAX_BRUSH_SIZE,
    MAX_SPRAY_DENSITY,
    MIN_BRUSH_SIZE,
    MIN_SPRAY_DENSITY,
)
from pixpop.session.model import (
    SessionFile,
    SessionLoadError,
    TabSession,
    UndoState,
    session_from_dict,
)
from pixpop.tools import get_tool_names_and_labels

if TYPE_CHECKING:
    from pixpop.workspace import PaintWorkspace

# Guard against decompression bombs: refuse session files whose JSON payload
# expands beyond this size.
MAX_SESSION_JSON_BYTES = 64 * 1024 * 1024


def load_session_file(path: Path) -> SessionFile:
    """Load a SessionFile from disk.

    Raises:
        SessionLoadError: If the file cannot be read, decompressed, parsed,
            or fails format/version validation.
    """
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            payload = json.load(_LimitedReader(handle, MAX_SESSION_JSON_BYTES))
    except SessionLoadError:
        raise
    except (OSError, EOFError, ValueError) as exc:
        # OSError/EOFError: gzip + IO failures; ValueError: JSONDecodeError.
        raise SessionLoadError(f"Cannot load session file {path}: {exc}") from exc
    return session_from_dict(payload)


class _LimitedReader:
    """Text reader wrapper that raises once a character budget is exceeded.

    The budget counts decoded characters (json.load consumes text); it is a
    proxy for the decompressed byte size and guards against gzip bombs.
    """

    def __init__(self, handle, limit: int) -> None:
        self._handle = handle
        self._remaining = limit

    def read(self, size: int = -1) -> str:
        chunk = self._handle.read(size)
        self._remaining -= len(chunk)
        if self._remaining < 0:
            raise SessionLoadError("Session file exceeds maximum allowed size.")
        return chunk


def apply_session_file(workspace: PaintWorkspace, session: SessionFile) -> None:
    """Apply a SessionFile to the current workspace.

    The session is fully validated before any workspace state is mutated, so
    a malformed session cannot leave the workspace half-applied. Tab panes are
    created immediately, but per-tab canvas state is applied after Textual has
    mounted the new widgets (canvases don't exist in the DOM until then).

    Raises:
        SessionLoadError: If any session value is invalid.
    """
    _validate_session(session)

    _apply_shared_state(workspace, session)
    workspace.clear_tabs()

    tab_sessions = session.tabs or [None]  # None -> a single default tab
    for index, tab in enumerate(tab_sessions):
        name = tab.name if tab is not None else "Canvas"
        pane = workspace.add_tab_with_name(name)
        if index == 0:
            workspace.set_active_tab_by_index(0)
        workspace.set_tab_label(pane, name)

    def apply_to_mounted() -> None:
        """Apply canvas-level state once new panes are in the DOM."""
        panes = workspace.get_tab_panes()
        if len(panes) != len(tab_sessions):
            workspace.app.notify(
                "Session load failed: tab/pane mismatch after rebuild.",
                title="Load",
                severity="error",
            )
            return
        try:
            for pane, tab in zip(panes, tab_sessions, strict=True):
                canvases = pane.query(PaintCanvas)
                if not canvases:
                    continue
                canvas = canvases.first()
                workspace.apply_shared_state_to_canvas(canvas)
                if tab is not None:
                    _apply_tab_state(pane, tab)
        except Exception as exc:
            workspace.app.notify(
                f"Session load failed: {exc}", title="Load", severity="error"
            )
            return
        if panes:
            if not workspace.set_active_tab_by_name(session.active_tab_name):
                workspace.set_active_tab_by_index(session.active_tab_index)
        workspace.refresh_after_session_load()

    workspace.call_after_refresh(apply_to_mounted)


def _validate_session(session: SessionFile) -> None:
    """Raise SessionLoadError if any session value cannot be applied."""
    try:
        Color.parse(session.palette.selected_color)
        for color in session.palette.recent_colors:
            Color.parse(color)
    except ValueError as exc:
        raise SessionLoadError(f"Invalid color in session: {exc}") from exc

    # Tool state must be valid before it is applied to pickers/canvas, which
    # raise ValueError on unknown names or out-of-range values.
    valid_tools = {name for name, _ in get_tool_names_and_labels()}
    tool = session.tool_state.current_tool
    if tool not in valid_tools:
        raise SessionLoadError(
            f"Unknown tool in session: {tool!r} (expected one of {sorted(valid_tools)})."
        )
    if not MIN_BRUSH_SIZE <= session.tool_state.brush_size <= MAX_BRUSH_SIZE:
        raise SessionLoadError(
            f"Brush size {session.tool_state.brush_size} is outside the "
            f"supported range {MIN_BRUSH_SIZE}..{MAX_BRUSH_SIZE}."
        )
    if not (MIN_SPRAY_DENSITY <= session.tool_state.spray_density <= MAX_SPRAY_DENSITY):
        raise SessionLoadError(
            f"Spray density {session.tool_state.spray_density} is outside the "
            f"supported range {MIN_SPRAY_DENSITY}..{MAX_SPRAY_DENSITY}."
        )

    for tab in session.tabs:
        if tab.undo.max_history < 1:
            raise SessionLoadError(
                f"Tab {tab.name!r} has invalid undo max_history "
                f"{tab.undo.max_history} (must be >= 1)."
            )
        for layer in tab.layers:
            for x, y, _ in layer.pixels:
                if not (0 <= x < tab.canvas.width and 0 <= y < tab.canvas.height):
                    raise SessionLoadError(
                        f"Pixel ({x}, {y}) in layer {layer.name!r} is outside "
                        f"the canvas bounds {tab.canvas.width}x{tab.canvas.height}."
                    )


def _apply_shared_state(workspace: PaintWorkspace, session: SessionFile) -> None:
    workspace.set_tool_state_values(
        session.tool_state.current_tool,
        session.tool_state.brush_size,
        session.tool_state.spray_density,
        session.tool_state.normalized,
    )
    selected_color = Color.parse(session.palette.selected_color)
    workspace.set_pen_color(selected_color)
    workspace.set_palette_state(session.palette.name, selected_color)
    workspace.set_recent_colors(session.palette.recent_colors)


def _apply_tab_state(pane: TabPane, tab: TabSession) -> None:
    canvas = pane.query_one(PaintCanvas)
    canvas.clear(width=tab.canvas.width, height=tab.canvas.height)
    snapshot = {
        "layers": [layer.to_dict() for layer in tab.layers],
        "active_layer_index": tab.active_layer_index,
    }
    canvas.restore_snapshot(snapshot)
    _apply_undo_state(canvas, tab.undo)


def _apply_undo_state(canvas: PaintCanvas, undo_state: UndoState) -> None:
    max_history = undo_state.max_history
    canvas.undo_manager.max_history = max_history
    canvas.undo_manager.undo_stack = deque(
        [snapshot.to_dict() for snapshot in undo_state.undo_stack],
        maxlen=max_history,
    )
    canvas.undo_manager.redo_stack = deque(
        [snapshot.to_dict() for snapshot in undo_state.redo_stack],
        maxlen=max_history,
    )
