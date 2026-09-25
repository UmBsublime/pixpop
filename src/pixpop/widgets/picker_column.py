"""Picker column widget for tool controls."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical

from pixpop.config import AppConfig
from pixpop.widgets.brush_picker import BrushSizePicker
from pixpop.widgets.canvas_info import CanvasInfo
from pixpop.widgets.color_picker import ColorPicker
from pixpop.widgets.flip_picker import FlipPicker
from pixpop.widgets.layer_picker import LayerPicker
from pixpop.widgets.normalize_picker import NormalizedPicker
from pixpop.widgets.spray_picker import SprayDensityPicker
from pixpop.widgets.tool_picker import ToolPicker


class PickerColumn(Vertical):
    """Column of pickers used to control tools and drawing state."""

    def __init__(
        self,
        workspace_id: str,
        normalized_value: bool,
        config: AppConfig | None = None,
    ) -> None:
        super().__init__(classes="picker-column")
        self._workspace_id = workspace_id
        self._normalized_value = normalized_value
        self._config = config if config is not None else AppConfig()

    def compose(self) -> ComposeResult:
        yield ColorPicker(workspace_id=self._workspace_id, config=self._config)
        yield ToolPicker(workspace_id=self._workspace_id)
        yield BrushSizePicker(workspace_id=self._workspace_id)
        yield SprayDensityPicker(workspace_id=self._workspace_id)
        yield NormalizedPicker(
            workspace_id=self._workspace_id,
            value=self._normalized_value,
        )
        yield FlipPicker(workspace_id=self._workspace_id)
        yield LayerPicker(workspace_id=self._workspace_id)
        yield CanvasInfo(workspace_id=self._workspace_id)
