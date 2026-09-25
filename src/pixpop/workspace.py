"""Workspace widget that orchestrates canvas and UI components."""

from __future__ import annotations

import uuid

from textual.app import ComposeResult
from textual.binding import Binding
from textual.color import Color
from textual.containers import Horizontal
from textual.widgets import Static, TabbedContent, TabPane, Tabs

from pixpop.canvas import PaintCanvas
from pixpop.config import AppConfig
from pixpop.constants import (
    MIN_BRUSH_SIZE,
    ToolName,
)
from pixpop.names import get_adjective_noun_name
from pixpop.screens.help_dialog import HelpDialog
from pixpop.screens.rename_dialog import RenameDialog
from pixpop.state import (
    AppState,
    BrushSizeChanged,
    NormalizedChanged,
    PenColorChanged,
    SprayDensityChanged,
    ToolChanged,
)
from pixpop.tools import (
    get_max_brush_size,
    get_normalized_capable_tool_names,
    get_tool_names_and_labels,
)
from pixpop.widgets import (
    BrushSizePicker,
    CanvasInfo,
    CanvasTabs,
    ColorPicker,
    FlipPicker,
    LayerPicker,
    NormalizedPicker,
    PickerColumn,
    SprayDensityPicker,
    ToolPicker,
)
from pixpop.workspace_io import WorkspaceIO
from pixpop.workspace_layers import LayerController
from pixpop.workspace_tabs import TabManager

# Tools that support the normalized (even-row snapping) drawing mode.
NORMALIZED_CAPABLE_TOOLS = get_normalized_capable_tool_names()


class PaintWorkspace(Static):
    """Parent widget that configures keybindings and arranges paint canvas with tools.

    This widget orchestrates all UI components and manages application state,
    ensuring separation of concerns between pickers, canvas, and state management.
    Supports multiple instances via scoped IDs.
    """

    BINDINGS = [
        ("c", "clear_canvas", "Clear Canvas"),
        Binding("ctrl+z", "undo", "Undo", False),
        Binding("ctrl+y", "redo", "Redo", False),
        Binding("d", "cycle_tool_forward", "Next Tool", False),
        Binding("a", "cycle_tool_backward", "Prev Tool", False),
        Binding("w", "increase_brush_size", "Increase Brush", False),
        Binding("s", "decrease_brush_size", "Decrease Brush", False),
        Binding("i", "pick_color", "Pick Color", False),
        Binding("ctrl+s", "save_canvas", "Save Canvas", False),
        Binding("ctrl+e", "export_canvas", "Export Canvas", False),
        Binding("ctrl+o", "load_canvas", "Load Canvas", False),
        Binding("r", "rename_tab", "Rename Tab", False),
        Binding("t", "new_tab", "New Tab", False),
        Binding("ctrl+w", "close_tab", "Close Tab", False),
        Binding("n", "next_tab", "Next Tab", False),
        Binding("?", "show_help", "Help"),
        Binding("/", "new_layer", "New Layer", False),
        Binding("delete", "remove_layer", "Remove Layer", False),
        Binding("v", "toggle_layer_visibility", "Toggle Layer", False),
        Binding("l", "rename_layer", "Rename Layer", False),
        Binding("left", "move_layer_up", "Move Layer Up", False),
        Binding("right", "move_layer_down", "Move Layer Down", False),
        Binding("up", "cycle_layer_up", "Prev Layer", False),
        Binding("down", "cycle_layer_down", "Next Layer", False),
    ]

    _counter: int = 0

    def __init__(
        self,
        config: AppConfig | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self._config = config if config is not None else AppConfig()
        self._state = AppState()
        self._tab_counter = 0
        self._last_cursor_pos: tuple[int, int] | None = None
        # Assign unique ID for this workspace instance
        PaintWorkspace._counter += 1
        self._workspace_id = f"ws-{PaintWorkspace._counter}-{uuid.uuid4().hex[:8]}"
        self._tabs_manager = TabManager(self._get_tabs, self._get_tabs_widget)
        self._layer_controller = LayerController(
            self._get_canvas, self._sync_layers_from_canvas
        )
        self._workspace_io = WorkspaceIO(
            workspace=self,
            tabs_manager=self._tabs_manager,
            get_canvas=self._get_canvas,
            create_tab_with_name=self._create_tab_with_name,
            refresh_active_canvas=self._refresh_active_canvas,
        )

    def _scoped_id(self, widget_type: str) -> str:
        """Generate a scoped ID for child widgets."""
        return f"{widget_type}-{self._workspace_id}"

    def compose(self) -> ComposeResult:
        """Create the workspace layout with canvas and tool pickers."""
        with Horizontal():
            yield PickerColumn(
                workspace_id=self._workspace_id,
                normalized_value=self._state.normalized,
                config=self._config,
            )
            yield CanvasTabs(
                tabs_id=self._scoped_id("canvas-tabs"),
                initial_pane=self._create_new_tab(),
            )

    def _get_tabs(self) -> TabbedContent:
        """Get the tabbed canvas container."""
        return self.query_one(f"#{self._scoped_id('canvas-tabs')}", TabbedContent)

    def _get_tabs_widget(self) -> Tabs:
        """Get the tabs widget for the canvas tabs."""
        return self._get_tabs().query_one(Tabs)

    def _get_canvas(self) -> PaintCanvas:
        """Get the active paint canvas widget for this workspace."""
        tabs = self._get_tabs()
        try:
            active_pane = tabs.active_pane
        except Exception as exc:
            raise ValueError("No active canvas tab.") from exc
        if active_pane is None:
            raise ValueError("No active canvas tab.")
        return active_pane.query_one(PaintCanvas)

    def get_tab_panes(self) -> list[TabPane]:
        """Return all tab panes in order."""
        return self._tabs_manager.list_panes()

    def get_active_tab_index(self) -> int:
        """Return the active tab index, or 0 if none."""
        return self._tabs_manager.active_index()

    def get_active_tab_name(self) -> str | None:
        """Return the active tab label if available."""
        return self._tabs_manager.active_name()

    def clear_tabs(self) -> None:
        """Remove all tab panes and reset active tab."""
        self._tabs_manager.clear()

    def add_tab_with_name(self, name: str) -> TabPane:
        """Create a new tab and return its pane."""
        pane = self._create_tab_with_name(name)
        self._tabs_manager.add_pane(pane)
        return pane

    def set_tab_label(self, pane: TabPane, name: str) -> None:
        """Apply a label to the tab and pane."""
        self._tabs_manager.set_tab_label(pane, name)

    def set_active_tab_by_index(self, index: int) -> None:
        """Set the active tab by index."""
        self._tabs_manager.set_active_by_index(index)

    def set_active_tab_by_name(self, name: str | None) -> bool:
        """Set the active tab by label, returning True if found."""
        return self._tabs_manager.set_active_by_name(name)

    def get_palette_state(self) -> tuple[str, Color]:
        """Return the palette name and selected color."""
        return self._get_color_picker().get_palette_state()

    def get_recent_colors(self) -> list[str]:
        """Return the shared recent colors."""
        return self._get_color_picker().get_recent_colors()

    def set_palette_state(self, palette_name: str, selected_color: Color) -> None:
        """Apply palette selection without emitting events."""
        self._get_color_picker().set_palette_state(
            palette_name, selected_color, emit=False
        )

    def set_recent_colors(self, colors: list[str]) -> None:
        """Apply recent colors without emitting events."""
        self._get_color_picker().set_recent_colors(colors)

    def get_tool_state_values(self) -> tuple[str, int, int, bool]:
        """Return tool state values in order."""
        return (
            self._state.current_tool_name,
            self._state.brush_size,
            self._state.spray_density,
            self._state.normalized,
        )

    def set_tool_state_values(
        self, current_tool: str, brush_size: int, spray_density: int, normalized: bool
    ) -> None:
        """Apply shared tool state values."""
        self._state.current_tool_name = current_tool
        _, max_size = self._get_brush_size_limits(current_tool)
        self._state.brush_size = max(MIN_BRUSH_SIZE, min(max_size, brush_size))
        self._state.spray_density = spray_density
        self._state.normalized = normalized

    def set_pen_color(self, color: Color) -> None:
        """Apply the shared pen color."""
        self._state.pen_color = color

    def apply_shared_state_to_canvas(self, canvas: PaintCanvas) -> None:
        """Apply the shared tool state to a canvas."""
        self._apply_state_to_canvas(canvas)

    def refresh_after_session_load(self) -> None:
        """Sync UI and focus after applying session state."""
        self._sync_ui_from_state()
        self._refresh_active_canvas()

    def _get_canvas_info(self) -> CanvasInfo:
        """Get the canvas info widget for this workspace."""
        return self.query_one(f"#canvas-info-{self._workspace_id}", CanvasInfo)

    def _get_tool_picker(self) -> ToolPicker:
        """Get the tool picker widget for this workspace."""
        return self.query_one(f"#{self._scoped_id('tool-picker')}", ToolPicker)

    def _get_brush_size_picker(self) -> BrushSizePicker:
        """Get the brush size picker widget for this workspace."""
        return self.query_one(
            f"#{self._scoped_id('brush-size-picker')}", BrushSizePicker
        )

    def _get_color_picker(self) -> ColorPicker:
        """Get the color picker widget for this workspace."""
        return self.query_one(f"#{self._scoped_id('color-picker')}", ColorPicker)

    def _get_spray_density_picker(self) -> SprayDensityPicker:
        """Get the spray density picker widget for this workspace."""
        return self.query_one(
            f"#{self._scoped_id('spray-density-picker')}", SprayDensityPicker
        )

    def _get_layer_picker(self) -> LayerPicker:
        """Get the layer picker widget for this workspace."""
        return self.query_one(f"#{self._scoped_id('layer-picker')}", LayerPicker)

    def _get_normalized_picker(self) -> NormalizedPicker:
        """Get the normalized toggle picker."""
        return self.query_one(
            f"#normalized-picker-{self._workspace_id}", NormalizedPicker
        )

    def _update_brush_size_visibility(self, tool_name: str) -> None:
        """Show brush size picker only when tool supports brush sizes."""
        self._get_brush_size_picker().set_visible(tool_name != ToolName.FINE_PEN)

    def _update_spray_density_visibility(self, tool_name: str) -> None:
        """Show spray density picker only when spray tool is active."""
        self._get_spray_density_picker().set_visible(tool_name == ToolName.SPRAY)

    def _update_normalized_visibility(self, tool_name: str) -> None:
        """Show normalized toggle only for tools that support it."""
        self._get_normalized_picker().set_visible(tool_name in NORMALIZED_CAPABLE_TOOLS)

    def _get_brush_size_limits(self, tool_name: str) -> tuple[int, int]:
        """Return the (min, max) brush size range for the given tool."""
        return (MIN_BRUSH_SIZE, get_max_brush_size(tool_name))

    def _apply_state_to_canvas(self, canvas: PaintCanvas) -> None:
        """Apply shared tool state to a canvas."""
        canvas.pen_color = self._state.pen_color
        canvas.brush_size = self._state.brush_size
        canvas.current_tool = self._state.current_tool_name
        canvas.normalized = self._state.normalized
        spray = canvas.tools.get(ToolName.SPRAY)
        if spray is not None:
            spray.set_density(self._state.spray_density)

    def _apply_state_to_active_canvas(self) -> None:
        """Apply shared tool state to the active canvas."""
        try:
            canvas = self._get_canvas()
        except ValueError:
            return
        self._apply_state_to_canvas(canvas)

    def _sync_tool_ui_from_state(self) -> None:
        """Sync tool-related pickers and visibility from the current state."""
        self._get_tool_picker().select_tool(self._state.current_tool_name, emit=False)
        brush_size_picker = self._get_brush_size_picker()
        brush_size_picker.set_max_size(
            get_max_brush_size(self._state.current_tool_name)
        )
        brush_size_picker.select_size(self._state.brush_size, emit=False)
        self._get_spray_density_picker().select_density(
            self._state.spray_density, emit=False
        )
        self._get_normalized_picker().set_value(self._state.normalized, emit=False)
        self._update_brush_size_visibility(self._state.current_tool_name)
        self._update_spray_density_visibility(self._state.current_tool_name)
        self._update_normalized_visibility(self._state.current_tool_name)

    def _sync_ui_from_state(self) -> None:
        """Sync picker UI and visibility from the current state."""
        self._sync_tool_ui_from_state()
        self._get_color_picker().select_color(self._state.pen_color, emit=False)

    def _set_tool_state(
        self,
        *,
        tool_name: str | None = None,
        brush_size: int | None = None,
        spray_density: int | None = None,
        normalized: bool | None = None,
        enforce_fine_pen: bool = False,
    ) -> None:
        """Update shared tool state and propagate to UI/canvas."""
        if tool_name is not None:
            self._state.current_tool_name = tool_name
            if enforce_fine_pen and tool_name == ToolName.FINE_PEN:
                self._state.brush_size = MIN_BRUSH_SIZE
                brush_size = None
        if brush_size is not None:
            self._state.brush_size = brush_size
        # Clamp shared brush size to the active tool's per-tool limit.
        _, max_size = self._get_brush_size_limits(self._state.current_tool_name)
        self._state.brush_size = max(
            MIN_BRUSH_SIZE, min(max_size, self._state.brush_size)
        )
        if spray_density is not None:
            self._state.spray_density = spray_density
        if normalized is not None:
            self._state.normalized = normalized
        self._sync_tool_ui_from_state()
        self._apply_state_to_active_canvas()

    def _sync_layers_from_canvas(self, canvas: PaintCanvas | None = None) -> None:
        """Sync layer UI with the active canvas."""
        if canvas is None:
            canvas = self._get_canvas()
        self._get_layer_picker().set_layers(
            canvas.get_layers(), canvas.active_layer_index
        )

    def _sync_canvas_info(self, canvas: PaintCanvas) -> None:
        """Sync canvas info with the active canvas."""
        info = self._get_canvas_info()
        info.update_canvas_size(canvas.width, canvas.height)
        if self._last_cursor_pos is not None:
            x, y = self._last_cursor_pos
            info.update_cursor(x, y)

    def _refresh_canvas_cursor(self, canvas: PaintCanvas) -> None:
        """Show cursor immediately if we have a previous position."""
        if canvas.drawing or canvas.erasing:
            return
        if self._last_cursor_pos is None:
            return
        x, y = self._last_cursor_pos
        if canvas.is_valid_position(x, y):
            canvas.update_cursor(x, y)

    def _schedule_cursor_refresh(self, canvas: PaintCanvas) -> None:
        """Schedule a cursor refresh after layout settles."""
        self.call_after_refresh(lambda: self._refresh_canvas_cursor(canvas))

    def _refresh_active_canvas(
        self,
        canvas: PaintCanvas | None = None,
        *,
        schedule_cursor: bool = False,
        focus: bool = True,
    ) -> PaintCanvas:
        """Refresh the active canvas state and UI."""
        if canvas is None:
            canvas = self._get_canvas()
        self._apply_state_to_canvas(canvas)
        self._sync_layers_from_canvas(canvas)
        self._sync_canvas_info(canvas)
        if schedule_cursor:
            self._schedule_cursor_refresh(canvas)
        else:
            self._refresh_canvas_cursor(canvas)
        if focus:
            canvas.focus()
        return canvas

    def on_mount(self) -> None:
        """Sync picker visibility with the initial tool selection."""
        self._state.pen_color = self._get_color_picker().get_palette_state()[1]
        self._sync_ui_from_state()
        self._refresh_active_canvas()

    def _is_event_from_this_workspace(self, sender: object) -> bool:
        """Check if an event originated from this workspace's widgets.

        Args:
            sender: The widget that sent the event.

        Returns:
            True if the sender belongs to this workspace.
        """
        # Walk up the tree to find if sender is our descendant
        current = sender
        while current is not None:
            if current is self:
                return True
            current = current.parent
        return False

    def on_paint_canvas_cursor_moved(self, event: PaintCanvas.CursorMoved) -> None:
        """Track cursor position from the active canvas."""
        if not self._is_event_from_this_workspace(event.canvas):
            return
        self._last_cursor_pos = (event.x, event.y)
        self._get_canvas_info().update_cursor(event.x, event.y)

    def on_paint_canvas_resized(self, event: PaintCanvas.Resized) -> None:
        """Update the canvas info widget when a canvas changes size."""
        if not self._is_event_from_this_workspace(event.canvas):
            return
        try:
            active_canvas = self._get_canvas()
        except ValueError:
            return
        if event.canvas is not active_canvas:
            return
        self._get_canvas_info().update_canvas_size(event.width, event.height)

    def on_pen_color_changed(self, event: PenColorChanged) -> None:
        """Handle pen color change events from ColorPicker."""
        if not self._is_event_from_this_workspace(event.sender):
            return
        self._state.pen_color = event.color
        self._apply_state_to_active_canvas()

    def on_tool_changed(self, event: ToolChanged) -> None:
        """Handle tool change events from ToolPicker."""
        if not self._is_event_from_this_workspace(event.sender):
            return
        self._set_tool_state(
            tool_name=event.tool_name,
            enforce_fine_pen=True,
        )

    def on_brush_size_changed(self, event: BrushSizeChanged) -> None:
        """Handle brush size change events from BrushSizePicker."""
        if not self._is_event_from_this_workspace(event.sender):
            return
        self._set_tool_state(brush_size=event.size)

    def on_spray_density_changed(self, event: SprayDensityChanged) -> None:
        """Handle spray density change events from SprayDensityPicker."""
        if not self._is_event_from_this_workspace(event.sender):
            return
        self._set_tool_state(spray_density=event.density)

    def on_normalized_changed(self, event: NormalizedChanged) -> None:
        """Handle normalized toggle changes."""
        if not self._is_event_from_this_workspace(event.sender):
            return
        self._set_tool_state(normalized=event.value)

    def on_flip_picker_flip_pressed(self, event: FlipPicker.FlipPressed) -> None:
        """Handle flip actions."""
        if not self._is_event_from_this_workspace(event.sender):
            return
        canvas = self._get_canvas()
        mode = event.mode
        if mode.startswith("layer-") and not canvas.active_layer_visible:
            return
        # Axis-based naming: "vertical" flips about the vertical axis
        # (a left/right mirror), which flip_horizontal implements.
        flip_actions = {
            "vertical": canvas.flip_horizontal,
            "horizontal": canvas.flip_vertical,
            "layer-vertical": canvas.flip_active_layer_horizontal,
            "layer-horizontal": canvas.flip_active_layer_vertical,
        }
        action = flip_actions.get(mode)
        if action is None:
            return
        canvas.save_state_for_undo()
        action()

    def action_clear_canvas(self) -> None:
        """Clear the entire canvas."""
        self._get_canvas().clear_with_undo()

    def action_undo(self) -> None:
        """Undo the last drawing operation."""
        self._get_canvas().action_undo()

    def action_redo(self) -> None:
        """Redo the last undone drawing operation."""
        self._get_canvas().action_redo()

    def _create_tab_with_name(self, tab_name: str) -> TabPane:
        """Create a new tab with a PaintCanvas and label."""
        self._tab_counter += 1
        tab_id = f"canvas-{self._tab_counter}-{self._workspace_id}"
        canvas_color = self._generate_canvas_color()
        canvas = PaintCanvas(
            canvas_color=canvas_color,
            config=self._config,
            id=tab_id,
        )
        self._apply_state_to_canvas(canvas)
        pane = TabPane(tab_name, canvas, id=tab_id)
        pane.title = tab_name
        return pane

    def _create_new_tab(self) -> TabPane:
        """Create a new tab with a PaintCanvas."""
        return self._create_tab_with_name(get_adjective_noun_name())

    def _generate_canvas_color(self) -> Color:
        """Return the shared base color for the canvas background."""
        return Color.parse(self._config.background_color)

    def action_new_tab(self) -> None:
        """Create a new canvas tab."""
        new_tab = self._create_new_tab()
        self._tabs_manager.add_pane(new_tab, activate=True)
        self._refresh_active_canvas()

    def action_close_tab(self) -> None:
        """Close the current active canvas tab."""
        active_pane = self._tabs_manager.active_pane()

        if active_pane is not None:
            self._tabs_manager.remove_pane(active_pane.id)

            if not self._tabs_manager.list_panes():
                self._tab_counter = 0
                new_tab = self._create_new_tab()
                self._tabs_manager.add_pane(new_tab, activate=True)

        self._refresh_active_canvas(focus=False)

    def action_next_tab(self) -> None:
        """Switch to the next canvas tab."""
        panes = self._tabs_manager.list_panes()

        if len(panes) <= 1:
            return

        active_pane = self._tabs_manager.active_pane()
        if active_pane is None:
            return

        if active_pane in panes:
            current_idx = panes.index(active_pane)
            next_idx = (current_idx + 1) % len(panes)
            self._tabs_manager.set_active_by_id(panes[next_idx].id)
            self._refresh_active_canvas(schedule_cursor=True)

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        """Handle tab changes to refresh tool state and cursor."""
        if event.tabbed_content.id != self._scoped_id("canvas-tabs"):
            return
        canvases = event.pane.query(PaintCanvas)
        if not canvases:
            return
        self._refresh_active_canvas(canvases.first(), schedule_cursor=True)

    def action_rename_tab(self) -> None:
        """Start inline rename for the active tab."""
        tabs_widget = self._get_tabs_widget()
        active_tab = tabs_widget.active_tab
        if active_tab is None:
            return

        def handle_rename(value: str | None, tab=active_tab) -> None:
            if value is None:
                return
            tab.label = value
            active_pane = self._tabs_manager.active_pane()
            if active_pane is not None:
                self._tabs_manager.set_tab_label(active_pane, value)
            self._get_canvas().focus()

        self.app.push_screen(
            RenameDialog("Rename tab", active_tab.label_text),
            handle_rename,
        )

    def action_cycle_tool_forward(self) -> None:
        """Cycle to the next tool."""
        self._cycle_tool(1)

    def action_cycle_tool_backward(self) -> None:
        """Cycle to the previous tool."""
        self._cycle_tool(-1)

    def _cycle_tool(self, direction: int) -> None:
        """Cycle the active tool by direction (+1 forward, -1 backward)."""
        tools = [name for name, _ in get_tool_names_and_labels()]
        current_tool_name = self._state.current_tool_name

        try:
            current_idx = tools.index(current_tool_name)
        except ValueError:
            current_idx = 0

        next_idx = (current_idx + direction) % len(tools)
        self._set_tool_state(tool_name=tools[next_idx], enforce_fine_pen=True)

    def action_increase_brush_size(self) -> None:
        """Increase brush size by 1 (clamped at the active tool's max)."""
        self._adjust_brush_size(1)

    def action_decrease_brush_size(self) -> None:
        """Decrease brush size by 1 (clamped at MIN_BRUSH_SIZE)."""
        self._adjust_brush_size(-1)

    def _adjust_brush_size(self, delta: int) -> None:
        """Adjust brush size by delta, clamped to the active tool's range."""
        if self._state.current_tool_name == ToolName.FINE_PEN:
            return
        min_size, max_size = self._get_brush_size_limits(self._state.current_tool_name)
        current_size = self._state.brush_size
        new_size = max(min_size, min(max_size, current_size + delta))
        if new_size != current_size:
            self._set_tool_state(brush_size=new_size)

    def action_pick_color(self) -> None:
        """Pick color from canvas at cursor position (eyedropper tool)."""
        canvas = self._get_canvas()
        color = canvas.get_color_at_cursor()

        # Only update if there's a color at the cursor position
        if color is not None:
            # Update state
            self._state.pen_color = color
            self._sync_ui_from_state()
            self._get_color_picker().add_recent_color(color)
            self._apply_state_to_active_canvas()

            # Redraw cursor with new color for instant visual feedback
            canvas.hide_cursor()
            if canvas.cursor_pos is not None:
                cx, cy = canvas.cursor_pos
                if canvas.is_valid_position(cx, cy):
                    canvas.update_cursor(cx, cy)

    def action_save_canvas(self) -> None:
        """Open save dialog for the active canvas."""
        self._workspace_io.open_save_dialog()

    def action_export_canvas(self) -> None:
        """Open export dialog for the active canvas."""
        self._workspace_io.open_export_dialog()

    def action_load_canvas(self) -> None:
        """Open load dialog for importing a canvas."""
        self._workspace_io.open_load_dialog()

    def on_layer_picker_layer_selected(self, event: LayerPicker.LayerSelected) -> None:
        """Handle layer selection changes."""
        if not self._is_event_from_this_workspace(event.sender):
            return
        self._layer_controller.set_active(event.index)

    def on_layer_picker_layer_visibility_toggled(
        self, event: LayerPicker.LayerVisibilityToggled
    ) -> None:
        """Handle layer visibility changes."""
        if not self._is_event_from_this_workspace(event.sender):
            return
        self._layer_controller.set_visibility(event.index, event.visible)

    def action_new_layer(self) -> None:
        """Create a new layer on the active canvas."""
        if not self._layer_controller.add_layer():
            self.app.bell()

    def action_show_help(self) -> None:
        """Show help dialog with keyboard shortcuts."""
        self.app.push_screen(HelpDialog())

    def action_remove_layer(self) -> None:
        """Remove the active layer on the canvas."""
        if not self._layer_controller.remove_active_layer():
            self.app.bell()

    def action_toggle_layer_visibility(self) -> None:
        """Toggle visibility for the active layer."""
        self._layer_controller.toggle_visibility()

    def action_rename_layer(self) -> None:
        """Start rename for the active layer."""
        canvas = self._get_canvas()
        index = canvas.active_layer_index
        layers = self._layer_controller.get_layers()
        if not layers:
            return
        name, _ = layers[index]
        self.app.push_screen(
            RenameDialog("Rename layer", name),
            lambda value: self._handle_layer_rename_result(index, value),
        )

    def _handle_layer_rename_result(self, index: int, value: str | None) -> None:
        if value is None:
            return
        self._layer_controller.rename(index, value)

    def action_move_layer_up(self) -> None:
        """Move active layer up."""
        if not self._layer_controller.move_up():
            self.app.bell()

    def action_move_layer_down(self) -> None:
        """Move active layer down."""
        if not self._layer_controller.move_down():
            self.app.bell()

    def action_cycle_layer_up(self) -> None:
        """Select the previous layer."""
        self._layer_controller.cycle_up()

    def action_cycle_layer_down(self) -> None:
        """Select the next layer."""
        self._layer_controller.cycle_down()
