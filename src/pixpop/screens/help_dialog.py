"""Help dialog screen listing keyboard shortcuts."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Label, Static

# Action-name prefix/substring -> help section, in display order. Actions not
# matching any rule land in "Other". This derives the help content from the
# workspace's live BINDINGS so the dialog can never drift from the keymap.
_SECTION_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Drawing", ("clear_canvas", "undo", "redo", "tool", "brush", "color")),
    ("Tabs", ("tab",)),
    ("Layers", ("layer",)),
    ("File", ("save", "export", "load")),
    ("Other", ()),
]

# Friendly grouping of multi-key actions shown on one line.
_COMBINED: dict[frozenset[str], str] = {
    frozenset({"cycle_tool_forward", "cycle_tool_backward"}): "d/a",
    frozenset({"increase_brush_size", "decrease_brush_size"}): "w/s",
    frozenset({"move_layer_up", "move_layer_down"}): "left/right",
    frozenset({"cycle_layer_up", "cycle_layer_down"}): "up/down",
}

# Overrides for descriptions that read better in help than in the footer.
_DESCRIPTION_OVERRIDES: dict[str, str] = {
    "next_tab": "Next canvas tab",
    "save_canvas": "Save (png/ansi/pix)",
    "export_canvas": "Export (ansi)",
    "load_canvas": "Load (ansi/png/pix)",
    "toggle_layer_visibility": "Toggle layer visibility",
}


def _binding_parts(binding) -> tuple[str, str, str]:
    """Return (key, action, description) for a tuple or Binding entry."""
    if isinstance(binding, Binding):
        return binding.key, binding.action, binding.description
    key, action, description = binding
    return key, action, description


def _section_for(action: str) -> str:
    for section, needles in _SECTION_RULES:
        if any(needle in action for needle in needles):
            return section
    return "Other"


def _build_sections() -> list[tuple[str, list[str]]]:
    """Group live workspace bindings into (section, ["key: description"])."""
    from pixpop.workspace import PaintWorkspace

    # First pass: collect per-action (key, description).
    rows: dict[str, tuple[str, str]] = {}
    for binding in PaintWorkspace.BINDINGS:
        key, action, description = _binding_parts(binding)
        description = _DESCRIPTION_OVERRIDES.get(action, description or action)
        rows[action] = (key, description)

    # Merge combined multi-key actions into a single row.
    for actions, combined_key in _COMBINED.items():
        present = [a for a in actions if a in rows]
        if len(present) == len(actions):
            # Use a shared, neutral description for the combined row.
            description = {
                "d/a": "Next/previous tool",
                "w/s": "Increase/decrease brush size",
                "left/right": "Move layer",
                "up/down": "Select layer",
            }[combined_key]
            for a in present:
                del rows[a]
            rows[present[0]] = (combined_key, description)

    # Bucket into ordered sections.
    sections: dict[str, list[str]] = {name: [] for name, _ in _SECTION_RULES}
    for action, (key, description) in rows.items():
        sections[_section_for(action)].append(f"{key}: {description}")
    return [(name, lines) for name, lines in sections.items() if lines]


class HelpDialog(ModalScreen[None]):
    """Modal screen showing keyboard shortcuts."""

    CSS_PATH = "../styles/screens/help_dialog.tcss"

    BINDINGS = [
        ("escape", "close", "Close"),
        ("enter", "close", "Close"),
        ("q", "close", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Static(id="help-dialog", classes="help-dialog"):
            yield Label("Help", id="help-title")
            for section, lines in _build_sections():
                yield Label(section, classes="help-section-title")
                yield Label("\n".join(lines), classes="help-section-body")
            yield Label("Press Esc, Enter, or q to close", id="help-hint")

    def action_close(self) -> None:
        self.dismiss(None)
