"""Session export utilities."""

from __future__ import annotations

import gzip
import json
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from textual.color import Color
from textual.widgets import TabPane

from pixpop._io import atomic_write
from pixpop.canvas import PaintCanvas
from pixpop.session.model import (
    CanvasSize,
    LayerSnapshot,
    PaletteState,
    SessionFile,
    SnapshotState,
    TabSession,
    ToolState,
    UndoState,
)

if TYPE_CHECKING:
    from pixpop.workspace import PaintWorkspace


def build_session_file(workspace: PaintWorkspace) -> SessionFile:
    """Build a SessionFile from the current workspace state."""
    panes = workspace.get_tab_panes()
    active_tab_index = workspace.get_active_tab_index()
    active_tab_name = workspace.get_active_tab_name()

    palette_name, selected_color = workspace.get_palette_state()
    recent_colors = workspace.get_recent_colors()
    palette = PaletteState(
        name=palette_name,
        selected_color=_color_to_hex(selected_color),
        recent_colors=recent_colors,
    )
    current_tool, brush_size, spray_density, normalized = (
        workspace.get_tool_state_values()
    )
    tool_state = ToolState(
        current_tool=current_tool,
        brush_size=brush_size,
        spray_density=spray_density,
        normalized=normalized,
    )

    tab_sessions = [_build_tab_session(pane) for pane in panes]
    if active_tab_name is None:
        if panes and 0 <= active_tab_index < len(panes):
            active_tab_name = _get_tab_label(panes[active_tab_index])

    created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return SessionFile(
        active_tab_index=active_tab_index,
        active_tab_name=active_tab_name,
        palette=palette,
        tool_state=tool_state,
        tabs=tab_sessions,
        created_at=created_at,
    )


def write_session_file(session: SessionFile, path: Path) -> None:
    """Serialize a SessionFile to disk as gzipped JSON (atomically)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(session.to_dict(), indent=2, sort_keys=False)

    def _write(temp_path: Path) -> None:
        with gzip.open(temp_path, "wt", encoding="utf-8") as handle:
            handle.write(payload)

    atomic_write(path, _write)


def _build_tab_session(pane: TabPane) -> TabSession:
    canvas = pane.query_one(PaintCanvas)
    layers = _build_layers(canvas)
    undo = _build_undo_state(canvas)
    tab_name = _get_tab_label(pane)
    return TabSession(
        name=tab_name,
        canvas=CanvasSize(width=canvas.width, height=canvas.height),
        active_layer_index=canvas.active_layer_index,
        layers=layers,
        undo=undo,
    )


def _build_layers(canvas: PaintCanvas) -> list[LayerSnapshot]:
    layers: list[LayerSnapshot] = []
    for layer in canvas.layers:
        pixels = _serialize_pixels(layer.pixels.items())
        layers.append(
            LayerSnapshot(
                name=layer.name,
                visible=layer.visible,
                pixels=pixels,
            )
        )
    return layers


def _serialize_pixels(
    items: Iterable[tuple[tuple[int, int], Color]],
) -> list[tuple[int, int, str]]:
    pixels: list[tuple[int, int, str]] = []
    for (x, y), color in sorted(items):
        pixels.append((x, y, _color_to_hex(color)))
    return pixels


def _build_undo_state(canvas: PaintCanvas) -> UndoState:
    undo_stack = [_snapshot_from_raw(raw) for raw in canvas.undo_manager.undo_stack]
    redo_stack = [_snapshot_from_raw(raw) for raw in canvas.undo_manager.redo_stack]
    return UndoState(
        max_history=canvas.undo_manager.max_history,
        undo_stack=undo_stack,
        redo_stack=redo_stack,
    )


def _snapshot_from_raw(raw: object) -> SnapshotState:
    return SnapshotState.from_dict(raw)


def _get_tab_label(pane: TabPane) -> str:
    title = _normalize_label(getattr(pane, "title", None))
    if title:
        return title
    label_attr = _normalize_label(getattr(pane, "label", None))
    if label_attr:
        return label_attr
    return "Canvas"


def _color_to_hex(color: Color) -> str:
    return color.hex.lower()


def _normalize_label(value: object) -> str | None:
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    plain = getattr(value, "plain", None)
    if isinstance(plain, str):
        normalized = plain.strip()
        return normalized or None
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
