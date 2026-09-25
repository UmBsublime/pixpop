"""Canvas widget with drawing capabilities."""

import time
from dataclasses import dataclass, field
from typing import Iterable

from textual.color import Color
from textual.events import Leave, MouseDown, MouseMove, MouseUp, Resize
from textual.message import Message
from textual_canvas import Canvas

from pixpop.config import AppConfig
from pixpop.constants import (
    BUTTON_LEFT,
    BUTTON_MIDDLE,
    BUTTON_RIGHT,
    OVERLAY_FPS_LIMIT,
    ToolName,
)
from pixpop.state import UndoRedoManager
from pixpop.tools import Tool, get_default_tool_name, instantiate_tools

# Brush sizes whose square footprint is anchored at the cursor's top-left
# pixel, so the block aligns flush with the cursor at the canvas's top-left
# corner instead of extending above/left and clipping.
_TOP_LEFT_ANCHORED_SIZES = (3, 5)


@dataclass
class Layer:
    """Represents a single canvas layer."""

    name: str
    visible: bool = True
    pixels: dict[tuple[int, int], Color] = field(default_factory=dict)


class PaintCanvas(Canvas):
    """A canvas widget that supports drawing and erasing with mouse interactions."""

    class CursorMoved(Message):
        """Posted when the cursor moves over a valid canvas cell."""

        def __init__(self, canvas: "PaintCanvas", x: int, y: int) -> None:
            super().__init__()
            self.canvas = canvas
            self.x = x
            self.y = y

    class Resized(Message):
        """Posted when the canvas grid size changes."""

        def __init__(self, canvas: "PaintCanvas", width: int, height: int) -> None:
            super().__init__()
            self.canvas = canvas
            self.width = width
            self.height = height

    def __init__(
        self,
        canvas_color: Color | None = None,
        config: AppConfig | None = None,
        **kwargs,
    ):
        cfg = config if config is not None else AppConfig()
        self._config = cfg
        # These attributes must exist before super().__init__() because the
        # parent constructor calls our overridden clear()/refresh_composite()
        # and get_background_pixel(), which read them.
        self._layers: list[Layer] = [Layer(name="Layer 1")]
        self._active_layer_index = 0
        self._canvas_color = canvas_color
        self._checker_enabled = cfg.background_mode == "checker"
        self._checker_colors = (
            Color.parse(cfg.checker_color_a),
            Color.parse(cfg.checker_color_b),
        )
        self._checker_size_x = cfg.checker_size_width
        self._checker_size_y = cfg.checker_size_height

        super().__init__(
            cfg.min_canvas_width,
            cfg.min_canvas_height,
            canvas_color=canvas_color,
            **kwargs,
        )

        self.drawing = False
        self.erasing = False
        self.pen_color = Color.parse("red")
        self.brush_size = 1
        self.normalized = False
        # The button driving the current stroke (set on mouse down).
        self._stroke_button = BUTTON_LEFT

        # Tool instances - each tool manages its own state
        self._tools = instantiate_tools()
        self._current_tool = self._tools[get_default_tool_name()]

        self.undo_manager = UndoRedoManager(max_history=cfg.undo_max_entries)

        # Live preview state for shape tools
        self._preview_backup: dict[tuple[int, int], Color | None] = {}
        self._preview_start_pos: tuple[int, int] | None = None
        self._is_preview_active = False
        self._last_preview_time: float = 0.0

        # Brush cursor state
        self._cursor_pos: tuple[int, int] | None = None
        self._cursor_backup: dict[tuple[int, int], Color | None] = {}
        self._last_cursor_time: float = 0.0

    @property
    def current_tool(self) -> Tool:
        """Get current tool instance."""
        return self._current_tool

    @current_tool.setter
    def current_tool(self, tool_name: str):
        """Set current tool by name."""
        if tool_name in self._tools:
            self._current_tool = self._tools[tool_name]
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    @property
    def active_layer_index(self) -> int:
        """Get the active layer index."""
        return self._active_layer_index

    @property
    def active_layer_visible(self) -> bool:
        """Return whether the active layer is visible."""
        if self._active_layer_index < 0 or self._active_layer_index >= len(
            self._layers
        ):
            return False
        return self._layers[self._active_layer_index].visible

    @property
    def cursor_pos(self) -> tuple[int, int] | None:
        """Get the current cursor position, if available."""
        return self._cursor_pos

    @property
    def tools(self) -> dict[str, Tool]:
        """Get the tool registry."""
        return self._tools

    @property
    def layers(self) -> list[Layer]:
        """Get the layer list (read-only access for serialization)."""
        return self._layers

    @property
    def canvas_color(self) -> Color | None:
        """Get the flat background color, if one was provided."""
        return self._canvas_color

    def get_layers(self) -> list[tuple[str, bool]]:
        """Get a list of layers as (name, visible) tuples."""
        return [(layer.name, layer.visible) for layer in self._layers]

    def set_active_layer(self, index: int) -> None:
        """Set the active layer by index."""
        if index < 0 or index >= len(self._layers):
            return
        self._active_layer_index = index

    def add_layer(self, name: str | None = None) -> bool:
        """Add a new layer and make it active."""
        if len(self._layers) >= self._config.max_layers:
            return False
        layer_number = len(self._layers) + 1
        layer_name = name or f"Layer {layer_number}"
        self._layers.append(Layer(name=layer_name))
        self._active_layer_index = len(self._layers) - 1
        self.refresh_composite()
        return True

    def remove_layer(self, index: int) -> bool:
        """Remove the specified layer."""
        if len(self._layers) <= 1:
            return False
        if index < 0 or index >= len(self._layers):
            return False
        del self._layers[index]
        if self._active_layer_index >= len(self._layers):
            self._active_layer_index = len(self._layers) - 1
        self.refresh_composite()
        return True

    def rename_layer(self, index: int, name: str) -> None:
        """Rename the specified layer."""
        if index < 0 or index >= len(self._layers):
            return
        self._layers[index].name = name

    def set_layer_visibility(self, index: int, visible: bool) -> None:
        """Set visibility of a layer."""
        if index < 0 or index >= len(self._layers):
            return
        self._layers[index].visible = visible
        self.refresh_composite()

    def toggle_layer_visibility(self, index: int) -> None:
        """Toggle visibility of a layer."""
        if index < 0 or index >= len(self._layers):
            return
        self._layers[index].visible = not self._layers[index].visible
        self.refresh_composite()

    def move_layer_up(self, index: int) -> bool:
        """Move a layer up (toward front)."""
        if index <= 0 or index >= len(self._layers):
            return False
        self._layers[index - 1], self._layers[index] = (
            self._layers[index],
            self._layers[index - 1],
        )
        self._active_layer_index = index - 1
        self.refresh_composite()
        return True

    def move_layer_down(self, index: int) -> bool:
        """Move a layer down (toward back)."""
        if index < 0 or index >= len(self._layers) - 1:
            return False
        self._layers[index + 1], self._layers[index] = (
            self._layers[index],
            self._layers[index + 1],
        )
        self._active_layer_index = index + 1
        self.refresh_composite()
        return True

    def get_layer_pixel(self, x: int, y: int, index: int | None = None) -> Color | None:
        """Get a pixel color from a layer."""
        if not self.is_valid_position(x, y):
            return None
        layer_index = self._active_layer_index if index is None else index
        if layer_index < 0 or layer_index >= len(self._layers):
            return None
        return self._layers[layer_index].pixels.get((x, y))

    def set_layer_pixel(
        self,
        x: int,
        y: int,
        color: Color | None,
        index: int | None = None,
        refresh: bool = True,
    ) -> None:
        """Set a pixel on a layer and refresh composite."""
        if not self.is_valid_position(x, y):
            return
        layer_index = self._active_layer_index if index is None else index
        if layer_index < 0 or layer_index >= len(self._layers):
            return
        layer = self._layers[layer_index]
        if not layer.visible:
            return
        if color is None:
            layer.pixels.pop((x, y), None)
        else:
            layer.pixels[(x, y)] = color
        if refresh:
            self.refresh_composite_pixels([(x, y)])

    def get_composited_pixel(self, x: int, y: int) -> Color | None:
        """Get the composited pixel at a position."""
        if not self.is_valid_position(x, y):
            return None
        for layer in reversed(self._layers):
            if not layer.visible:
                continue
            color = layer.pixels.get((x, y))
            if color is not None:
                return color
        return None

    def refresh_composite_pixels(self, pixels: Iterable[tuple[int, int]]) -> None:
        """Refresh composite for a set of pixels."""
        for x, y in pixels:
            if not self.is_valid_position(x, y):
                continue
            color = self.get_composited_pixel(x, y)
            target = self.get_background_pixel(x, y) if color is None else color
            super().set_pixel(x, y, target)

    def refresh_composite(self) -> None:
        """Rebuild the composited canvas from all visible layers."""
        super().clear()
        for y in range(self.height):
            for x in range(self.width):
                color = self.get_composited_pixel(x, y)
                target = self.get_background_pixel(x, y) if color is None else color
                super().set_pixel(x, y, target)

    def capture_snapshot(self) -> dict:
        """Capture a full snapshot of layers for undo/redo.

        The shape matches ``pixpop.session.model`` serialization (pixel lists,
        lowercase hex colors) so snapshots can round-trip through session
        save/load without type drift.
        """
        layers_data = []
        for layer in self._layers:
            pixels = [
                [x, y, color.hex.lower()]
                for (x, y), color in sorted(layer.pixels.items())
            ]
            layers_data.append(
                {"name": layer.name, "visible": layer.visible, "pixels": pixels}
            )
        return {
            "layers": layers_data,
            "active_layer_index": self._active_layer_index,
        }

    def restore_snapshot(self, snapshot: dict) -> None:
        """Restore layers from a snapshot."""
        layers_data = snapshot.get("layers", [])
        restored_layers: list[Layer] = []
        for data in layers_data:
            layer = Layer(
                name=data.get("name", "Layer"),
                visible=data.get("visible", True),
            )
            pixels = {}
            for x, y, color_hex in data.get("pixels", []):
                pixels[(x, y)] = Color.parse(color_hex)
            layer.pixels = pixels
            restored_layers.append(layer)
        if restored_layers:
            self._layers = restored_layers
        else:
            self._layers = [Layer(name="Layer 1")]
        self._active_layer_index = max(
            0, min(snapshot.get("active_layer_index", 0), len(self._layers) - 1)
        )
        self.refresh_composite()

    def screen_to_canvas_coords(self, screen_x: int, screen_y: int) -> tuple[int, int]:
        """Convert screen coordinates to canvas-relative coordinates."""
        canvas_region = self.region
        canvas_x = screen_x - canvas_region.x - 1
        canvas_y = (screen_y - canvas_region.y) * 2
        return canvas_x, canvas_y

    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if coordinates are within canvas bounds."""
        return 0 <= x < self.width and 0 <= y < self.height

    def get_background_pixel(self, x: int, y: int) -> Color:
        """Return the background color at a canvas coordinate."""
        if not self._checker_enabled:
            background = self._canvas_color or self.styles.background
            if isinstance(background, Color):
                return background
            return Color.parse(str(background))
        cell_x = x // self._checker_size_x
        cell_y = y // self._checker_size_y
        if (cell_x + cell_y) % 2 == 0:
            return self._checker_colors[0]
        return self._checker_colors[1]

    def _brush_offsets(self) -> list[tuple[int, int]]:
        """Return (dx, dy) offsets covered by the current brush.

        Footprint per brush size (in pixels):

        - size 1: one full cell (1x2 pixels, both halves of the anchor cell)
        - size 2: 2x2 pixels
        - size 3: 4x4 pixels, top-left anchored at the cursor
        - size 4: 6x6 pixels
        - size 5: 8x8 pixels, top-left anchored at the cursor

        Sizes 3 and 5 are anchored at the cursor's top-left corner so the
        block aligns flush with the cursor at the canvas's top-left corner.
        Sizes 2 and 4 keep centered anchoring (symmetric on x, trailing
        downward on y); size 2 already evaluates to the cursor-anchored
        {(0,0),(1,0),(0,1),(1,1)}.
        """
        if self.brush_size <= 1:
            return [(0, 0), (0, 1)]
        half = self.brush_size - 1  # N = 2*half pixels per side
        if self.brush_size in _TOP_LEFT_ANCHORED_SIZES:
            side = half * 2
            return [(dx, dy) for dx in range(side) for dy in range(side)]
        lo = -(half - 1)
        hi = half
        return [(dx, dy) for dx in range(lo, hi + 1) for dy in range(lo, hi + 1)]

    def draw_cell(
        self, x: int, y: int, color: Color | None, is_erase: bool = False
    ) -> None:
        """Draw or erase pixels in a brush-sized area centered at (x, y)."""
        target_color = None if is_erase else color
        updated: set[tuple[int, int]] = set()
        for dx, dy in self._brush_offsets():
            px, py = x + dx, y + dy
            if not self.is_valid_position(px, py):
                continue
            self.set_layer_pixel(px, py, target_color, refresh=False)
            updated.add((px, py))
        self.refresh_composite_pixels(updated)

    def _draw_overlay_cell(self, x: int, y: int, color: Color | None) -> None:
        """Draw a brush-sized cell directly to the widget (overlay only)."""
        for dx, dy in self._brush_offsets():
            px, py = x + dx, y + dy
            if not self.is_valid_position(px, py):
                continue
            if color is None:
                super().clear_pixel(px, py)
            else:
                super().set_pixel(px, py, color)

    def on_mouse_down(self, event: MouseDown) -> None:
        """Handle mouse button press."""
        canvas_x, canvas_y = self.screen_to_canvas_coords(
            int(event.screen_x), int(event.screen_y)
        )

        # Hide cursor when starting to draw
        self.hide_cursor()
        button = event.button
        self._stroke_button = button

        # Only record an undo snapshot for clicks that can actually draw;
        # an out-of-bounds press is a no-op and must not clobber redo history.
        can_draw = self.is_valid_position(canvas_x, canvas_y)

        if button == BUTTON_LEFT:
            if can_draw:
                self.save_state_for_undo()
            self._current_tool.on_mouse_down(self, canvas_x, canvas_y, button)
            if self._current_tool.can_drag():
                self.drawing = True
                self.erasing = self._current_tool.is_eraser()
            elif self._current_tool.supports_preview():
                self._start_preview(canvas_x, canvas_y)
        elif (
            button in (BUTTON_MIDDLE, BUTTON_RIGHT)
            and self._current_tool.name == ToolName.FINE_PEN
        ):
            if can_draw:
                self.save_state_for_undo()
            self._current_tool.on_mouse_down(self, canvas_x, canvas_y, button)
            if self._current_tool.can_drag():
                self.drawing = True
        elif button == BUTTON_RIGHT:
            # Right click - use eraser tool
            if can_draw:
                self.save_state_for_undo()
            self.drawing = True
            self.erasing = True
            eraser = self._tools.get(ToolName.ERASER)
            if eraser:
                eraser.on_mouse_down(self, canvas_x, canvas_y, button)

    def on_mouse_move(self, event: MouseMove) -> None:
        """Handle mouse movement."""
        canvas_x, canvas_y = self.screen_to_canvas_coords(
            int(event.screen_x), int(event.screen_y)
        )

        # Report cursor position so the workspace info panel stays in sync.
        if self.is_valid_position(canvas_x, canvas_y):
            self.post_message(self.CursorMoved(self, canvas_x, canvas_y))

        if self._is_preview_active:
            if self.is_valid_position(canvas_x, canvas_y):
                self._draw_preview(canvas_x, canvas_y)
            return

        if not (self.drawing or self.erasing):
            # Show brush cursor when not drawing
            if self.is_valid_position(canvas_x, canvas_y):
                self.update_cursor(canvas_x, canvas_y)
            else:
                self.hide_cursor()
            return

        if self.is_valid_position(canvas_x, canvas_y):
            if self.erasing:
                eraser = self._tools.get(ToolName.ERASER)
                if eraser:
                    eraser.on_mouse_move(self, canvas_x, canvas_y, self._stroke_button)
            elif self.drawing and self._current_tool.can_drag():
                self._current_tool.on_mouse_move(
                    self, canvas_x, canvas_y, self._stroke_button
                )

    def on_mouse_up(self, event: MouseUp) -> None:
        """Handle mouse button release."""
        canvas_x, canvas_y = self.screen_to_canvas_coords(
            int(event.screen_x), int(event.screen_y)
        )

        if self._is_preview_active:
            self._end_preview(canvas_x, canvas_y)

        self._current_tool.on_mouse_up(self, canvas_x, canvas_y, event.button)

        self.drawing = False
        self.erasing = False
        self._stroke_button = BUTTON_LEFT

    def on_leave(self, event: Leave) -> None:
        """Handle mouse leaving the canvas widget."""
        self.hide_cursor()

    def clear(self, width: int | None = None, height: int | None = None) -> None:
        """Clear canvas and all layers."""
        super().clear(width=width, height=height)
        for layer in self._layers:
            layer.pixels.clear()
        self.refresh_composite()

    def resize_preserve_content(self, new_width: int, new_height: int) -> None:
        """Resize the canvas, keeping layer pixels that remain in bounds."""
        old_width, old_height = self._width, self._height
        if old_width == 0 or old_height == 0:
            return

        # Clear cursor/preview overlays to avoid out-of-bounds writes
        self._cursor_backup = {}
        self._cursor_pos = None
        self._preview_backup = {}
        self._preview_start_pos = None
        self._is_preview_active = False

        # Resize widget without touching layer data
        super().clear(width=new_width, height=new_height)

        # Drop any pixels outside the new bounds
        for layer in self._layers:
            out_of_bounds = [
                (x, y)
                for (x, y) in layer.pixels.keys()
                if x >= new_width or y >= new_height
            ]
            for coord in out_of_bounds:
                layer.pixels.pop(coord, None)

        self.refresh_composite()

    def _notify_canvas_size(self) -> None:
        """Notify listeners (e.g. the workspace) about the current canvas size."""
        self.post_message(self.Resized(self, self.width, self.height))

    def _resize_to_widget(self) -> None:
        """Resize canvas to match widget dimensions."""
        content = self.content_size
        if content.width == 0 or content.height == 0:
            return
        new_width = max(self._config.min_canvas_width, int(content.width))
        new_height = max(self._config.min_canvas_height, int(content.height * 2))

        if new_width != self._width or new_height != self._height:
            self.resize_preserve_content(new_width, new_height)
            self._notify_canvas_size()

    def on_resize(self, event: Resize) -> None:
        """Handle resize events."""
        self._resize_to_widget()

    def on_mount(self) -> None:
        """Handle widget mounting."""
        self.set_timer(0.1, self._resize_to_widget)
        self.undo_manager.attach_canvas(self)

    def action_undo(self) -> None:
        """Undo the last drawing operation."""
        self.hide_cursor()
        if self.undo_manager.undo():
            self.refresh()

    def action_redo(self) -> None:
        """Redo the last undone drawing operation."""
        self.hide_cursor()
        if self.undo_manager.redo():
            self.refresh()

    def clear_with_undo(self) -> None:
        """Clear the canvas and record the action for undo."""
        self.save_state_for_undo()
        self.clear()

    def save_state_for_undo(self) -> None:
        """Save current canvas state before a drawing operation."""
        self.undo_manager.save_state()

    def _clear_overlays(self) -> None:
        """Clear cursor and preview overlays before mutating pixels."""
        self.hide_cursor()
        self._preview_backup = {}
        self._preview_start_pos = None
        self._is_preview_active = False

    def _start_preview(self, start_x: int, start_y: int) -> None:
        """Start live preview mode for shape tools.

        Args:
            start_x: Starting X coordinate.
            start_y: Starting Y coordinate.
        """
        self._is_preview_active = True
        self._preview_start_pos = (start_x, start_y)
        self._preview_backup = {}

    def _restore_preview_pixels(self) -> None:
        """Restore pixels to their original state before drawing new preview."""
        for (x, y), original_color in self._preview_backup.items():
            if original_color is None:
                self.clear_pixel(x, y)
            else:
                self.set_pixel(x, y, original_color)

    def _save_pixels_for_backup(self, pixels: list[tuple[int, int]]) -> None:
        """Save current colors of pixels before overwriting them.

        Args:
            pixels: List of (x, y) coordinates to backup.
        """
        for x, y in pixels:
            if (x, y) not in self._preview_backup and self.is_valid_position(x, y):
                self._preview_backup[(x, y)] = self.get_pixel(x, y)

    def _get_brush_pixels(self, x: int, y: int) -> list[tuple[int, int]]:
        """Get all in-bounds pixel coordinates the brush covers at (x, y)."""
        return [
            (x + dx, y + dy)
            for dx, dy in self._brush_offsets()
            if self.is_valid_position(x + dx, y + dy)
        ]

    def _draw_preview(self, current_x: int, current_y: int) -> None:
        """Draw preview of shape at current position.

        Args:
            current_x: Current X coordinate.
            current_y: Current Y coordinate.
        """
        if not self._is_preview_active or self._preview_start_pos is None:
            return

        now = time.monotonic()
        throttle_interval = 1.0 / OVERLAY_FPS_LIMIT
        if now - self._last_preview_time < throttle_interval:
            return
        self._last_preview_time = now

        start_x, start_y = self._preview_start_pos

        # Restore previous preview
        self._restore_preview_pixels()

        # Get new preview pixels from tool
        preview_pixels = self._current_tool.get_preview_pixels(
            self, start_x, start_y, current_x, current_y
        )

        # Calculate all unique pixels that would be affected by the brush
        all_brush_pixels = list(
            dict.fromkeys(
                pixel
                for x, y in preview_pixels
                for pixel in self._get_brush_pixels(x, y)
            )
        )

        # Backup pixels before drawing
        self._save_pixels_for_backup(all_brush_pixels)

        # Draw preview pixels using brush size (overlay only)
        for x, y in preview_pixels:
            self._draw_overlay_cell(x, y, self.pen_color)

    def _end_preview(self, final_x: int, final_y: int) -> None:
        """End preview mode and commit final shape.

        Args:
            final_x: Final X coordinate.
            final_y: Final Y coordinate.
        """
        if not self._is_preview_active:
            return

        # Restore original pixels (preview will be re-drawn by tool's on_mouse_up)
        self._restore_preview_pixels()

        # Clear preview state
        self._is_preview_active = False
        self._preview_start_pos = None
        self._preview_backup = {}

    def _get_outline_pixels(self, x: int, y: int) -> list[tuple[int, int]]:
        """Get the perimeter pixels of the brush footprint at (x, y).

        Used to render the brush cursor outline. Only pixels on the outer edge
        of the footprint are included. Derived from _brush_offsets() so the
        cursor outline always matches the painted footprint.
        """
        offsets = self._brush_offsets()
        min_dx = min(dx for dx, _ in offsets)
        max_dx = max(dx for dx, _ in offsets)
        min_dy = min(dy for _, dy in offsets)
        max_dy = max(dy for _, dy in offsets)

        outline_pixels: set[tuple[int, int]] = set()
        for dx, dy in offsets:
            if dx in (min_dx, max_dx) or dy in (min_dy, max_dy):
                px, py = x + dx, y + dy
                if self.is_valid_position(px, py):
                    outline_pixels.add((px, py))

        return list(outline_pixels)

    def update_cursor(self, x: int, y: int) -> None:
        """Show brush cursor outline at position (throttled to OVERLAY_FPS_LIMIT).

        Args:
            x: X coordinate on canvas.
            y: Y coordinate on canvas.
        """
        now = time.monotonic()
        throttle_interval = 1.0 / OVERLAY_FPS_LIMIT
        if now - self._last_cursor_time < throttle_interval:
            return
        self._last_cursor_time = now

        # If position hasn't changed, don't redraw
        if self._cursor_pos == (x, y):
            return

        # Hide previous cursor
        self.hide_cursor()

        # Get outline pixels
        outline_pixels = self._get_outline_pixels(x, y)

        if not outline_pixels:
            return

        # Backup current colors
        for px, py in outline_pixels:
            if (px, py) not in self._cursor_backup:
                self._cursor_backup[(px, py)] = self.get_pixel(px, py)

        # Draw outline with selected pen color
        for px, py in outline_pixels:
            self.set_pixel(px, py, self.pen_color)

        self._cursor_pos = (x, y)

    def hide_cursor(self) -> None:
        """Restore original pixels and hide cursor."""
        for (x, y), original_color in self._cursor_backup.items():
            if original_color is None:
                self.clear_pixel(x, y)
            else:
                self.set_pixel(x, y, original_color)

        self._cursor_backup = {}
        self._cursor_pos = None

    def get_color_at_cursor(self) -> Color | None:
        """Get the color at the current cursor position.

        Returns:
            The Color at cursor position, or None if no color (transparent)
            or cursor is not on canvas.
        """
        if self._cursor_pos is None:
            return None

        x, y = self._cursor_pos
        if not self.is_valid_position(x, y):
            return None

        color = self.get_composited_pixel(x, y)
        if color is None:
            return None

        return color

    @staticmethod
    def _flip_layer_pixels(layer: Layer, flip_fn) -> None:
        """Remap one layer's pixels through flip_fn(x, y) -> (nx, ny)."""
        layer.pixels = {flip_fn(x, y): color for (x, y), color in layer.pixels.items()}

    def _flip_pixels(self, flip_fn) -> None:
        """Remap every layer's pixels through flip_fn."""
        for layer in self._layers:
            self._flip_layer_pixels(layer, flip_fn)

    def flip_horizontal(self) -> None:
        """Flip all layers about the vertical axis (left/right mirror)."""
        self._clear_overlays()
        width = self.width
        self._flip_pixels(lambda x, y: (width - 1 - x, y))
        self.refresh_composite()

    def flip_vertical(self) -> None:
        """Flip all layers about the horizontal axis (top/bottom mirror)."""
        self._clear_overlays()
        height = self.height
        self._flip_pixels(lambda x, y: (x, height - 1 - y))
        self.refresh_composite()

    def _flip_active_layer(self, flip_fn) -> bool:
        """Flip only the active layer, if it is visible."""
        if not self.active_layer_visible:
            return False
        self._clear_overlays()
        self._flip_layer_pixels(self._layers[self._active_layer_index], flip_fn)
        self.refresh_composite()
        return True

    def flip_active_layer_horizontal(self) -> bool:
        """Flip the active layer about the vertical axis (left/right mirror)."""
        width = self.width
        return self._flip_active_layer(lambda x, y: (width - 1 - x, y))

    def flip_active_layer_vertical(self) -> bool:
        """Flip the active layer about the horizontal axis (top/bottom mirror)."""
        height = self.height
        return self._flip_active_layer(lambda x, y: (x, height - 1 - y))
