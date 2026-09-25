"""Session file format models for pixpop."""

from __future__ import annotations

from dataclasses import dataclass, field

from pixpop.tools import get_default_tool_name

DEFAULT_CANVAS_WIDTH = 100
DEFAULT_CANVAS_HEIGHT = 50
DEFAULT_PALETTE_NAME = "default"
DEFAULT_SELECTED_COLOR = "#d32f2f"
DEFAULT_MAX_HISTORY = 50
DEFAULT_BRUSH_SIZE = 1
DEFAULT_SPRAY_DENSITY = 3
SESSION_FORMAT = "pixpop-session"
SESSION_VERSION = 1

# Sanity bounds for dimensions loaded from files.
MIN_CANVAS_DIMENSION = 1
MAX_CANVAS_DIMENSION = 4096


class SessionLoadError(ValueError):
    """Raised when a session file is invalid or unsupported."""


def _coerce_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default


def _coerce_int(value: object, default: int) -> int:
    if isinstance(value, int):
        return value
    return default


def _coerce_str(value: object, default: str) -> str:
    if isinstance(value, str):
        return value
    return default


def _coerce_color(value: object, default: str) -> str:
    if isinstance(value, str) and value:
        return value
    return default


def _coerce_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    return {}


def _coerce_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    return []


def _coerce_color_list(value: object) -> list[str]:
    colors: list[str] = []
    for entry in _coerce_list(value):
        color = _coerce_color(entry, "")
        if color:
            colors.append(color)
    return colors


@dataclass
class CanvasSize:
    """Canvas dimensions."""

    width: int = DEFAULT_CANVAS_WIDTH
    height: int = DEFAULT_CANVAS_HEIGHT

    def to_dict(self) -> dict[str, int]:
        return {"width": self.width, "height": self.height}

    @classmethod
    def from_dict(cls, data: object) -> CanvasSize:
        raw = _coerce_dict(data)
        width = _coerce_dimension(raw.get("width"), DEFAULT_CANVAS_WIDTH)
        height = _coerce_dimension(raw.get("height"), DEFAULT_CANVAS_HEIGHT)
        return cls(width=width, height=height)


@dataclass
class LayerSnapshot:
    """Serializable layer snapshot."""

    name: str
    visible: bool
    pixels: list[tuple[int, int, str]]

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "visible": self.visible,
            "pixels": [[x, y, color] for x, y, color in self.pixels],
        }

    @classmethod
    def from_dict(cls, data: object) -> LayerSnapshot:
        raw = _coerce_dict(data)
        name = _coerce_str(raw.get("name"), "Layer")
        visible = _coerce_bool(raw.get("visible"), True)
        pixels = _parse_pixels(raw.get("pixels"))
        return cls(name=name, visible=visible, pixels=pixels)


@dataclass
class SnapshotState:
    """Undo/redo snapshot payload."""

    layers: list[LayerSnapshot] = field(default_factory=list)
    active_layer_index: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "layers": [layer.to_dict() for layer in self.layers],
            "active_layer_index": self.active_layer_index,
        }

    @classmethod
    def from_dict(cls, data: object) -> SnapshotState:
        raw = _coerce_dict(data)
        layers = _parse_layers(raw.get("layers"))
        active_layer_index = _coerce_int(raw.get("active_layer_index"), 0)
        return cls(layers=layers, active_layer_index=active_layer_index)


@dataclass
class UndoState:
    """Undo/redo stack state for a tab."""

    max_history: int = DEFAULT_MAX_HISTORY
    undo_stack: list[SnapshotState] = field(default_factory=list)
    redo_stack: list[SnapshotState] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "max_history": self.max_history,
            "undo_stack": [snapshot.to_dict() for snapshot in self.undo_stack],
            "redo_stack": [snapshot.to_dict() for snapshot in self.redo_stack],
        }

    @classmethod
    def from_dict(cls, data: object) -> UndoState:
        raw = _coerce_dict(data)
        max_history = _coerce_int(raw.get("max_history"), DEFAULT_MAX_HISTORY)
        undo_stack = _parse_snapshots(raw.get("undo_stack"))
        redo_stack = _parse_snapshots(raw.get("redo_stack"))
        return cls(
            max_history=max_history,
            undo_stack=undo_stack,
            redo_stack=redo_stack,
        )


@dataclass
class ToolState:
    """Shared tool state for the session."""

    current_tool: str = field(default_factory=get_default_tool_name)
    brush_size: int = DEFAULT_BRUSH_SIZE
    spray_density: int = DEFAULT_SPRAY_DENSITY
    normalized: bool = False
    extras: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "current_tool": self.current_tool,
            "brush_size": self.brush_size,
            "spray_density": self.spray_density,
            "normalized": self.normalized,
        }
        if self.extras:
            payload["extras"] = self.extras
        return payload

    @classmethod
    def from_dict(cls, data: object) -> ToolState:
        raw = _coerce_dict(data)
        current_tool = _coerce_str(raw.get("current_tool"), get_default_tool_name())
        brush_size = _coerce_int(raw.get("brush_size"), DEFAULT_BRUSH_SIZE)
        spray_density = _coerce_int(raw.get("spray_density"), DEFAULT_SPRAY_DENSITY)
        normalized = _coerce_bool(raw.get("normalized"), False)
        extras = _coerce_dict(raw.get("extras"))
        return cls(
            current_tool=current_tool,
            brush_size=brush_size,
            spray_density=spray_density,
            normalized=normalized,
            extras=extras,
        )


@dataclass
class PaletteState:
    """Shared palette state for the session."""

    name: str = DEFAULT_PALETTE_NAME
    selected_color: str = DEFAULT_SELECTED_COLOR
    recent_colors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "name": self.name,
            "selected_color": self.selected_color,
        }
        if self.recent_colors:
            payload["recent_colors"] = self.recent_colors
        return payload

    @classmethod
    def from_dict(cls, data: object) -> PaletteState:
        raw = _coerce_dict(data)
        name = _coerce_str(raw.get("name"), DEFAULT_PALETTE_NAME)
        selected_color = _coerce_color(
            raw.get("selected_color"), DEFAULT_SELECTED_COLOR
        )
        recent_colors = _coerce_color_list(raw.get("recent_colors"))
        return cls(
            name=name,
            selected_color=selected_color,
            recent_colors=recent_colors,
        )


@dataclass
class TabSession:
    """Serializable tab state."""

    name: str
    canvas: CanvasSize
    active_layer_index: int
    layers: list[LayerSnapshot]
    undo: UndoState

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "canvas": self.canvas.to_dict(),
            "active_layer_index": self.active_layer_index,
            "layers": [layer.to_dict() for layer in self.layers],
            "undo": self.undo.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: object) -> TabSession:
        raw = _coerce_dict(data)
        name = _coerce_str(raw.get("name"), "Canvas")
        canvas = CanvasSize.from_dict(raw.get("canvas"))
        active_layer_index = _coerce_int(raw.get("active_layer_index"), 0)
        layers = _parse_layers(raw.get("layers"))
        undo = UndoState.from_dict(raw.get("undo"))
        return cls(
            name=name,
            canvas=canvas,
            active_layer_index=active_layer_index,
            layers=layers,
            undo=undo,
        )


@dataclass
class SessionFile:
    """Top-level session file structure."""

    format: str = SESSION_FORMAT
    version: int = SESSION_VERSION
    app_version: str | None = None
    created_at: str | None = None
    active_tab_index: int = 0
    active_tab_name: str | None = None
    palette: PaletteState = field(default_factory=PaletteState)
    tool_state: ToolState = field(default_factory=ToolState)
    tabs: list[TabSession] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "format": self.format,
            "version": self.version,
            "active_tab_index": self.active_tab_index,
            "active_tab_name": self.active_tab_name,
            "palette": self.palette.to_dict(),
            "tool_state": self.tool_state.to_dict(),
            "tabs": [tab.to_dict() for tab in self.tabs],
        }
        if self.app_version is not None:
            payload["app_version"] = self.app_version
        if self.created_at is not None:
            payload["created_at"] = self.created_at
        return payload

    @classmethod
    def from_dict(cls, data: object) -> SessionFile:
        raw = _coerce_dict(data)
        format_value = _coerce_str(raw.get("format"), SESSION_FORMAT)
        version = _coerce_int(raw.get("version"), SESSION_VERSION)
        app_version = raw.get("app_version")
        if not isinstance(app_version, str):
            app_version = None
        created_at = raw.get("created_at")
        if not isinstance(created_at, str):
            created_at = None
        active_tab_index = _coerce_int(raw.get("active_tab_index"), 0)
        active_tab_name = raw.get("active_tab_name")
        if not isinstance(active_tab_name, str):
            active_tab_name = None
        palette = PaletteState.from_dict(raw.get("palette"))
        tool_state = ToolState.from_dict(raw.get("tool_state"))
        tabs = _parse_tabs(raw.get("tabs"))
        return cls(
            format=format_value,
            version=version,
            app_version=app_version,
            created_at=created_at,
            active_tab_index=active_tab_index,
            active_tab_name=active_tab_name,
            palette=palette,
            tool_state=tool_state,
            tabs=tabs,
        )


def _coerce_dimension(value: object, default: int) -> int:
    """Coerce a canvas dimension, rejecting out-of-range values.

    Dimensions outside the supported bounds indicate a corrupt or hostile
    file, so we fail loudly rather than silently resizing the user's art.
    """
    dimension = _coerce_int(value, default)
    if not MIN_CANVAS_DIMENSION <= dimension <= MAX_CANVAS_DIMENSION:
        raise SessionLoadError(
            f"Canvas dimension {dimension} is outside the supported range "
            f"{MIN_CANVAS_DIMENSION}..{MAX_CANVAS_DIMENSION}."
        )
    return dimension


def _parse_pixels(data: object) -> list[tuple[int, int, str]]:
    pixels: list[tuple[int, int, str]] = []
    for entry in _coerce_list(data):
        if not isinstance(entry, (list, tuple)) or len(entry) != 3:
            continue
        x, y, color = entry
        if not isinstance(x, int) or not isinstance(y, int):
            continue
        if not isinstance(color, str):
            continue
        pixels.append((x, y, color))
    return pixels


def _parse_layers(data: object) -> list[LayerSnapshot]:
    layers: list[LayerSnapshot] = []
    for entry in _coerce_list(data):
        layers.append(LayerSnapshot.from_dict(entry))
    return layers


def _parse_snapshots(data: object) -> list[SnapshotState]:
    snapshots: list[SnapshotState] = []
    for entry in _coerce_list(data):
        snapshots.append(SnapshotState.from_dict(entry))
    return snapshots


def _parse_tabs(data: object) -> list[TabSession]:
    tabs: list[TabSession] = []
    for entry in _coerce_list(data):
        tabs.append(TabSession.from_dict(entry))
    return tabs


def session_to_dict(session: SessionFile) -> dict[str, object]:
    """Serialize a SessionFile to a JSON-ready dictionary."""
    return session.to_dict()


def session_from_dict(data: object) -> SessionFile:
    """Deserialize a SessionFile from a JSON dictionary.

    Raises:
        SessionLoadError: If the payload is not a mapping, has an unknown
            format identifier, or a newer unsupported version.
    """
    if not isinstance(data, dict):
        raise SessionLoadError("Session payload is not a JSON object.")
    format_value = data.get("format")
    if format_value != SESSION_FORMAT:
        raise SessionLoadError(f"Unrecognized session format: {format_value!r}.")
    version = _coerce_int(data.get("version"), SESSION_VERSION)
    if version > SESSION_VERSION:
        raise SessionLoadError(
            f"Session version {version} is newer than supported "
            f"version {SESSION_VERSION}."
        )
    return SessionFile.from_dict(data)
