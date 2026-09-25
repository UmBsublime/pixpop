"""Undo/Redo manager for canvas operations."""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pixpop.canvas import PaintCanvas


class UndoRedoManager:
    """Manages undo/redo stack for canvas snapshots.

    This implementation uses a snapshot-based approach where the entire
    canvas pixel state is captured before each drawing operation.
    This provides robust undo/redo with simple implementation.

    Attributes:
        max_history: Maximum number of states to keep in undo stack.
        undo_stack: Deque storing canvas snapshots for undo.
        redo_stack: Deque storing canvas snapshots for redo.
    """

    def __init__(self, max_history: int = 50) -> None:
        """Initialize the undo/redo manager.

        Args:
            max_history: Maximum number of undo states to retain.
        """
        self.max_history = max_history
        self.undo_stack: deque[dict] = deque(maxlen=max_history)
        self.redo_stack: deque[dict] = deque(maxlen=max_history)
        self._canvas: PaintCanvas | None = None

    def attach_canvas(self, canvas: PaintCanvas) -> None:
        """Attach a canvas to this manager for operations.

        Args:
            canvas: The canvas to manage.
        """
        self._canvas = canvas

    def save_state(self) -> None:
        """Save current canvas state to undo stack.

        Call this before any drawing operation that should be undoable.
        This also clears the redo stack since a new action invalidates
        the redo history.
        """
        if self._canvas is None:
            return

        snapshot = self._canvas.capture_snapshot()
        self.undo_stack.append(snapshot)
        # Clear redo stack on new action
        self.redo_stack.clear()

    def can_undo(self) -> bool:
        """Check if undo operation is available.

        Returns:
            True if there are states to undo.
        """
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo operation is available.

        Returns:
            True if there are states to redo.
        """
        return len(self.redo_stack) > 0

    def undo(self) -> bool:
        """Perform undo operation.

        Moves current state to redo stack and restores previous state.

        Returns:
            True if undo was performed, False if no undo available.
        """
        if not self.can_undo() or self._canvas is None:
            return False

        # Save current state to redo stack
        self.redo_stack.append(self._canvas.capture_snapshot())

        # Restore previous state from undo stack
        previous_state = self.undo_stack.pop()
        self._canvas.restore_snapshot(previous_state)

        return True

    def redo(self) -> bool:
        """Perform redo operation.

        Moves state from redo stack back to canvas.

        Returns:
            True if redo was performed, False if no redo available.
        """
        if not self.can_redo() or self._canvas is None:
            return False

        # Save current state to undo stack
        self.undo_stack.append(self._canvas.capture_snapshot())

        # Restore state from redo stack
        next_state = self.redo_stack.pop()
        self._canvas.restore_snapshot(next_state)

        return True

    def clear(self) -> None:
        """Clear all undo/redo history."""
        self.undo_stack.clear()
        self.redo_stack.clear()
