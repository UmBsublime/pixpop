"""I/O helpers for workspace save/load/export flows."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from textual.widgets import TabPane

from pixpop.canvas import PaintCanvas
from pixpop.export import save_canvas_ansi, save_canvas_png
from pixpop.importers import apply_ascii_alpha, apply_png
from pixpop.screens.load_file_dialog import LoadFileDialog
from pixpop.screens.save_file_dialog import (
    SaveFileDialog,
    SaveFileDialogResult,
)
from pixpop.session import (
    apply_session_file,
    build_session_file,
    load_session_file,
    write_session_file,
)
from pixpop.workspace_tabs import TabManager

if TYPE_CHECKING:
    from pixpop.workspace import PaintWorkspace

# File extension per save format.
FORMAT_EXTENSIONS: dict[str, str] = {
    "session": ".pix",
    "ansi": ".ans",
    "png": ".png",
}

# Sentinel raw path meaning "no name yet" — doubles as the current directory
# in _resolve_save_path, which then generates a timestamped filename.
_DEFAULT_SAVE_DIR = "."

# Upper bound on refresh-cycle retries while waiting for a canvas to lay out.
_PNG_LAYOUT_MAX_ATTEMPTS = 60


class WorkspaceIO:
    """Workspace dialog and file handling operations."""

    def __init__(
        self,
        workspace: PaintWorkspace,
        tabs_manager: TabManager,
        get_canvas: Callable[[], PaintCanvas],
        create_tab_with_name: Callable[[str], TabPane],
        refresh_active_canvas: Callable[[], PaintCanvas],
    ) -> None:
        self._workspace = workspace
        self._tabs_manager = tabs_manager
        self._get_canvas = get_canvas
        self._create_tab_with_name = create_tab_with_name
        self._refresh_active_canvas = refresh_active_canvas
        self._last_session_filename: str | None = None

    def open_save_dialog(self) -> None:
        """Open save dialog for the active canvas."""
        default_name = self._get_default_tab_name()
        if self._last_session_filename:
            default_name = self._last_session_filename
        self._workspace.app.push_screen(
            SaveFileDialog(
                default_path=default_name,
                default_format="session",
                non_session_path=self._get_default_tab_name(),
            ),
            self._handle_save_dialog,
        )

    def open_export_dialog(self) -> None:
        """Open export dialog for the active canvas."""
        default_name = self._get_default_tab_name()
        self._workspace.app.push_screen(
            SaveFileDialog(
                default_path=default_name,
                default_format="ansi",
                non_session_path=default_name,
            ),
            self._handle_save_dialog,
        )

    def open_load_dialog(self) -> None:
        """Open load dialog for importing a canvas."""
        self._workspace.app.push_screen(
            LoadFileDialog(),
            self._handle_load_dialog,
        )

    def _get_default_tab_name(self) -> str:
        name = self._tabs_manager.active_name()
        return name if name else _DEFAULT_SAVE_DIR

    def _handle_save_dialog(self, result: SaveFileDialogResult | None) -> None:
        """Handle save dialog completion."""
        if result is None:
            return
        format_value = result.format
        raw_path = result.path or _DEFAULT_SAVE_DIR
        target_path = self._resolve_save_path(raw_path, format_value)

        try:
            canvas = self._get_canvas()
            if format_value == "session":
                session = build_session_file(self._workspace)
                write_session_file(session, target_path)
                self._set_project_title(target_path.name)
                self._last_session_filename = target_path.name
            elif format_value == "ansi":
                save_canvas_ansi(canvas, target_path, trim=result.trim)
            else:
                save_canvas_png(canvas, target_path, result.scale)
            if format_value != "session":
                active_pane = self._tabs_manager.active_pane()
                if active_pane is not None:
                    self._tabs_manager.set_tab_label(active_pane, target_path.name)
        except (OSError, ValueError) as exc:
            self._workspace.app.notify(
                f"Save failed: {exc}", title="Save", severity="error"
            )
            return
        self._workspace.app.notify(f"Saved to {target_path}", title="Save")

    def _resolve_save_path(self, raw_path: str, format_value: str) -> Path:
        """Resolve output path based on format and user input."""
        extension = FORMAT_EXTENSIONS.get(format_value, ".ans")
        path = Path(raw_path).expanduser()

        if path.is_dir() or raw_path.endswith("/"):
            filename = datetime.now().strftime(f"canvas-%Y%m%d-%H%M%S{extension}")
            path = path / filename
        else:
            path = path.with_suffix(extension)

        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _handle_load_dialog(self, path: Path | None) -> None:
        """Handle load dialog completion."""
        if path is None:
            return
        path = Path(path).expanduser()
        if not path.exists() or not path.is_file():
            self._workspace.app.notify(
                f"File not found: {path}", title="Load", severity="error"
            )
            return

        try:
            if path.suffix.lower() == ".pix":
                session = load_session_file(path)
                apply_session_file(self._workspace, session)
                self._set_project_title(path.name)
                self._last_session_filename = path.name
                self._workspace.app.notify(f"Loaded session {path.name}", title="Load")
                return
            new_tab = self._create_tab_with_name(path.name)
            self._tabs_manager.add_pane(new_tab, activate=True)
            canvas = self._get_canvas()
            if path.suffix.lower() == ".png":
                self._apply_png_when_ready(canvas, path)
            else:
                apply_ascii_alpha(canvas, path)
        except (OSError, ValueError) as exc:
            self._workspace.app.notify(
                f"Load failed: {exc}", title="Load", severity="error"
            )
            return
        self._refresh_active_canvas()

    def _set_project_title(self, project_name: str | None) -> None:
        """Update app title with the active project name."""
        base_title = getattr(self._workspace.app, "base_title", "Pixpop")
        if project_name:
            self._workspace.app.title = f"{base_title} - {project_name}"
        else:
            self._workspace.app.title = base_title

    def _apply_png_when_ready(
        self, canvas: PaintCanvas, path: Path, attempts: int = 0
    ) -> None:
        """Apply a PNG once the canvas layout is ready."""
        content = canvas.content_size
        if content.width == 0 or content.height == 0:
            if attempts >= _PNG_LAYOUT_MAX_ATTEMPTS:
                self._workspace.app.notify(
                    f"Could not load {path.name}: canvas never became ready.",
                    title="Load",
                    severity="error",
                )
                return
            self._workspace.call_after_refresh(
                lambda: self._apply_png_when_ready(canvas, path, attempts + 1)
            )
            return
        apply_png(canvas, path)
