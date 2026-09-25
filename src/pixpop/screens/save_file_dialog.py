"""Modal screen for saving files with a file picker."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from textual import on
from textual.containers import Horizontal
from textual.widgets import Button, Checkbox, Input, Label, Select
from textual_fspicker import FileSave
from textual_fspicker.parts import DirectoryNavigation, DriveNavigation
from textual_fspicker.path_maker import MakePath


@dataclass(frozen=True)
class SaveFileDialogResult:
    """Result of the save dialog."""

    format: str
    path: str
    scale: int
    trim: bool


class SaveFileDialog(FileSave):
    """File save dialog with format selection and optional PNG scaling."""

    DEFAULT_CSS = """
    SaveFileDialog Dialog {
        border: round $primary;
    }

    SaveFileDialog #save-scale-row.-hidden {
        display: none;
    }

    SaveFileDialog #save-scale-row {
        height: auto;
    }

    SaveFileDialog #save-trim-row.-hidden {
        display: none;
    }

    SaveFileDialog #save-trim-row {
        height: auto;
    }
    """

    def __init__(
        self,
        default_path: str = ".",
        default_format: str = "session",
        non_session_path: str | None = None,
    ) -> None:
        super().__init__(
            title="Save Canvas",
            default_file=default_path,
        )
        self._default_format = default_format
        self._last_format = default_format
        self._session_path = default_path
        self._non_session_path = non_session_path or default_path

    def _input_bar(self):
        yield Label("Format")
        yield Select(
            [
                ("PNG", "png"),
                ("ANSI", "ansi"),
                ("Session (.pix)", "session"),
            ],
            value=self._default_format,
            id="save-format",
        )
        yield Label("Path")
        yield Input(
            value=self._apply_default_extension(
                self._session_path, self._default_format
            ),
            id="save-path",
        )
        with Horizontal(id="save-scale-row", classes="-hidden"):
            yield Label("Scale")
            yield Select(
                [("1x", "1"), ("2x", "2"), ("4x", "4"), ("8x", "8")],
                value="1",
                id="save-scale",
            )
        with Horizontal(id="save-trim-row", classes="-hidden"):
            yield Checkbox("Trim", value=False, id="save-trim")

    def on_mount(self) -> None:
        self.query_one("#save-path", Input).focus()
        self._update_scale_visibility(self._default_format)
        self._update_trim_visibility(self._default_format)

    def _extension_for_format(self, format_value: str) -> str:
        if format_value == "png":
            return ".png"
        if format_value == "session":
            return ".pix"
        return ".ans"

    def _apply_default_extension(self, raw_path: str, format_value: str) -> str:
        if raw_path in ("", ".") or raw_path.endswith(("/", "\\")):
            return raw_path or "."
        path = Path(raw_path)
        if path.suffix:
            return raw_path
        return f"{raw_path}{self._extension_for_format(format_value)}"

    def _scale_from_select(self) -> int:
        scale_select = self.query_one("#save-scale", Select)
        value = scale_select.value or "1"
        try:
            return int(value)
        except ValueError:
            return 1

    def _update_scale_visibility(self, format_value: str) -> None:
        scale_row = self.query_one("#save-scale-row", Horizontal)
        if format_value == "png":
            scale_row.remove_class("-hidden")
        else:
            scale_row.add_class("-hidden")

    def _update_trim_visibility(self, format_value: str) -> None:
        trim_row = self.query_one("#save-trim-row", Horizontal)
        if format_value == "ansi":
            trim_row.remove_class("-hidden")
        else:
            trim_row.add_class("-hidden")

    def _should_swap_default_path(self, raw_path: str, format_value: str) -> bool:
        if self._last_format == "session" and format_value != "session":
            if raw_path.endswith(".pix") or raw_path == self._session_path:
                return True
        return False

    def _should_swap_session_path(self, raw_path: str, format_value: str) -> bool:
        if self._last_format != "session" and format_value == "session":
            if (
                raw_path.endswith((".png", ".ans"))
                or raw_path == self._non_session_path
            ):
                return True
        return False

    @on(Select.Changed)
    def _on_format_changed(self, event: Select.Changed) -> None:
        if event.select.id != "save-format":
            return
        format_value = event.value or "png"
        self._update_scale_visibility(format_value)
        self._update_trim_visibility(format_value)
        path_input = self.query_one("#save-path", Input)
        raw_path = path_input.value.strip()
        if self._should_swap_default_path(raw_path, format_value):
            path_input.value = self._apply_default_extension(
                self._non_session_path, format_value
            )
            self._last_format = format_value
            return
        if self._should_swap_session_path(raw_path, format_value):
            path_input.value = self._apply_default_extension(
                self._session_path, format_value
            )
            self._last_format = format_value
            return
        if raw_path in ("", ".") or raw_path.endswith(("/", "\\")):
            self._last_format = format_value
            return
        path = Path(raw_path)
        if path.suffix in {".png", ".ans", ".pix", ""}:
            base = raw_path[: -len(path.suffix)] if path.suffix else raw_path
            path_input.value = f"{base}{self._extension_for_format(format_value)}"
        self._last_format = format_value

    @on(Input.Submitted)
    @on(Button.Pressed, "#select")
    def _confirm_file(self, event) -> None:
        event.stop()
        # Prevent the base class handler from also processing this event,
        # which would dismiss the screen a second time and crash with a
        # ScreenStackError.
        event.prevent_default()
        file_name = self.query_one("#save-path", Input)
        if not file_name.value:
            self._set_error(self.ERROR_A_FILE_MUST_BE_CHOSEN)
            return
        if file_name.value.startswith("~"):
            try:
                chosen = MakePath.of(file_name.value).expanduser()
            except RuntimeError as error:
                self._set_error(str(error))
                return
        else:
            chosen = (
                self.query_one(DirectoryNavigation).location / file_name.value
            ).resolve()
        try:
            if chosen.is_dir():
                drive = MakePath.of(file_name.value).drive
                if drive:
                    try:
                        self.query_one(DriveNavigation).drive = drive
                    except Exception as exc:
                        # Drive switching is best-effort; log and continue.
                        self.log.debug(f"Could not switch drive to {drive}: {exc}")
                self.query_one(DirectoryNavigation).location = chosen
                self.query_one(DirectoryNavigation).focus()
                file_name.value = ""
                return
        except PermissionError:
            self._set_error(self.ERROR_PERMISSION_ERROR)
            return
        if not self._should_return(chosen):
            return
        format_select = self.query_one("#save-format", Select)
        format_value = format_select.value or "png"
        scale = self._scale_from_select()
        trim_checkbox = self.query_one("#save-trim", Checkbox)
        self.dismiss(
            SaveFileDialogResult(format_value, str(chosen), scale, trim_checkbox.value)
        )
