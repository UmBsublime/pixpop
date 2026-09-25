"""Modal screen for opening files with a file picker."""

from __future__ import annotations

from pathlib import Path

from textual.events import Click
from textual_fspicker import FileOpen
from textual_fspicker.parts import DirectoryNavigation
from textual_fspicker.parts.directory_navigation import DirectoryEntry
from textual_fspicker.path_filters import Filters
from textual_fspicker.safe_tests import is_file


class LoadFileDialog(FileOpen):
    """File open dialog for supported pixpop formats."""

    DEFAULT_CSS = """
    LoadFileDialog Dialog {
        border: round $primary;
    }
    """

    def __init__(self) -> None:
        super().__init__(
            title="Load Canvas",
            filters=_build_load_filters(),
        )

    def on_click(self, event: Click) -> None:
        if event.chain != 2:
            return
        if not isinstance(event.control, DirectoryNavigation):
            return
        option = event.control.highlighted_option
        if not isinstance(option, DirectoryEntry):
            return
        path = option.location
        if not is_file(path):
            return
        if not self._should_return(path):
            return
        self.dismiss(result=path)


def _suffix_filter(*suffixes: str):
    """Build a filter accepting directories or files with the given suffixes."""

    def is_match(path: Path) -> bool:
        return path.is_dir() or path.suffix.lower() in suffixes

    return is_match


def _build_load_filters() -> Filters:
    """Return file picker filters for supported formats."""
    return Filters(
        ("All supported", _suffix_filter(".pix", ".png", ".ans")),
        ("Pixpop Session (.pix)", _suffix_filter(".pix")),
        ("Images (.png)", _suffix_filter(".png")),
        ("ASCII Alpha (.ans)", _suffix_filter(".ans")),
    )
