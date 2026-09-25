"""Base Tool abstract class for canvas drawing tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from textual.color import Color


class CanvasProtocol(Protocol):
    """The tool-facing surface of PaintCanvas.

    Tools receive the canvas typed as this protocol so the contract is
    explicit and type-checkable, without tools depending on the concrete
    widget class (which would create an import cycle).
    """

    # Mutable drawing state (read by tools).
    pen_color: Color
    brush_size: int
    normalized: bool

    # Canvas dimensions.
    width: int
    height: int

    def draw_cell(
        self, x: int, y: int, color: Color | None, is_erase: bool = False
    ) -> None:
        """Draw/erase a brush-sized cell at (x, y)."""
        ...

    def set_layer_pixel(
        self,
        x: int,
        y: int,
        color: Color | None,
        index: int | None = None,
        refresh: bool = True,
    ) -> None:
        """Set a single pixel on a layer."""
        ...

    def get_layer_pixel(self, x: int, y: int, index: int | None = None) -> Color | None:
        """Get a pixel color from a layer."""
        ...

    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if coordinates are within canvas bounds."""
        ...

    def refresh_composite_pixels(self, pixels) -> None:
        """Refresh the composited rendering for the given pixels."""
        ...


def snap_to_normalized(
    canvas: CanvasProtocol,
    pixels: list[tuple[int, int]],
    center_y: int | None = None,
) -> list[tuple[int, int]]:
    """Snap pixels to even rows and dedupe, for normalized drawing mode.

    Args:
        canvas: The canvas (uses is_valid_position and normalized flag).
        pixels: Raw pixel coordinates.
        center_y: If provided, snap odd rows toward this row (circle mode);
            otherwise snap down to the nearest even row (line/ellipse mode).

    Returns:
        Deduped list of in-bounds (x, even_y) coordinates.
    """
    normalized: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for px, py in pixels:
        if center_y is not None:
            if py % 2 == 0:
                even_y = py
            elif py < center_y:
                even_y = py - 1
            else:
                even_y = py + 1
        else:
            even_y = py - (py % 2)
        if canvas.is_valid_position(px, even_y):
            coord = (px, even_y)
            if coord not in seen:
                seen.add(coord)
                normalized.append(coord)
    return normalized


class Tool(ABC):
    """Abstract base class for drawing tools.

    Each tool manages its own state and handles mouse events.
    Tools are responsible for drawing operations on the canvas.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the tool name."""

    @abstractmethod
    def on_mouse_down(
        self, canvas: CanvasProtocol, x: int, y: int, button: int = 1
    ) -> None:
        """Handle mouse button press.

        Args:
            canvas: The PaintCanvas instance.
            x: X coordinate on canvas.
            y: Y coordinate on canvas.
            button: The mouse button pressed (1=left, 2=middle, 3=right).
        """

    def on_mouse_move(  # noqa: B027
        self, canvas: CanvasProtocol, x: int, y: int, button: int = 1
    ) -> None:
        """Handle mouse movement while button is held (intentional no-op default).

        Args:
            canvas: The PaintCanvas instance.
            x: X coordinate on canvas.
            y: Y coordinate on canvas.
            button: The mouse button held (1=left, 2=middle, 3=right).
        """

    def on_mouse_up(  # noqa: B027
        self, canvas: CanvasProtocol, x: int, y: int, button: int = 1
    ) -> None:
        """Handle mouse button release (intentional no-op default).

        Args:
            canvas: The PaintCanvas instance.
            x: X coordinate on canvas.
            y: Y coordinate on canvas.
            button: The mouse button released (1=left, 2=middle, 3=right).
        """

    def can_drag(self) -> bool:
        """Return True if tool supports continuous drawing while dragging."""
        return False

    def supports_preview(self) -> bool:
        """Return True if tool supports live preview while dragging.

        Shape tools (rectangle, line, circle, ellipse) should return True.
        Continuous drawing tools (pen, eraser) should return False.
        """
        return False

    def get_preview_pixels(
        self,
        canvas: CanvasProtocol,
        start_x: int,
        start_y: int,
        current_x: int,
        current_y: int,
    ) -> list[tuple[int, int]]:
        """Get list of pixel coordinates that would be drawn for preview.

        Args:
            canvas: The PaintCanvas instance.
            start_x: Starting X coordinate (from mouse_down).
            start_y: Starting Y coordinate (from mouse_down).
            current_x: Current X coordinate.
            current_y: Current Y coordinate.

        Returns:
            List of (x, y) tuples representing pixels to preview.
        """
        return []

    def is_eraser(self) -> bool:
        """Return True if this tool acts as an eraser.

        Eraser tools should return True to allow proper state tracking
        during drawing operations.
        """
        return False
