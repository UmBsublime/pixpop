"""Tool picker widget."""

from __future__ import annotations

from pixpop.state import ToolChanged
from pixpop.tools import get_tool_definitions
from pixpop.widgets.single_select_picker import SingleSelectPicker


class ToolPicker(SingleSelectPicker[str]):
    """Tool selection widget for choosing drawing tools."""

    def __init__(self, workspace_id: str) -> None:
        tools = get_tool_definitions()
        self._tools = tools
        labels = {tool.name: tool.label for tool in tools}
        tooltips = {tool.name: tool.tooltip for tool in tools}
        super().__init__(
            workspace_id=workspace_id,
            picker_id="tool-picker",
            title="Tools",
            label="Tools:",
            values=[tool.name for tool in tools],
            label_fn=lambda name: f" {labels[name]}",
            build_changed_message=lambda name: ToolChanged(name, sender=self),
            default=tools[0].name,
            grid_class="tool-grid",
            button_tooltip=lambda name: tooltips[name],
        )

    # Backwards-compatible API used by workspace and tests.
    def select_tool(self, tool_name: str, emit: bool = True) -> None:
        """Select a tool programmatically (e.g., from keyboard shortcuts)."""
        self.select_value(tool_name, emit=emit)

    @property
    def current_tool(self) -> str:
        return self.current_value
