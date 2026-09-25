"""Central tool registry - single source of truth for all tools."""

from dataclasses import dataclass

from pixpop.constants import MAX_BRUSH_SIZE
from pixpop.tools.base import Tool
from pixpop.tools.circle import CircleTool
from pixpop.tools.ellipse import EllipseTool
from pixpop.tools.eraser import EraserTool
from pixpop.tools.fine_pen import FinePenTool
from pixpop.tools.line import LineTool
from pixpop.tools.paint_bucket import PaintBucketTool
from pixpop.tools.pen import PenTool
from pixpop.tools.rectangle import RectangleTool
from pixpop.tools.spray import SprayTool

# The default tool selected on startup.
DEFAULT_TOOL_NAME = "pen"


@dataclass
class ToolDefinition:
    """Definition of a tool for registration."""

    name: str  # Internal identifier
    label: str  # UI display label
    tooltip: str  # UI tooltip
    tool_class: type[Tool]  # Tool class to instantiate
    supports_normalized: bool = False  # Whether normalized mode applies
    max_brush_size: int = MAX_BRUSH_SIZE  # Upper brush size limit for this tool


# Central registry - ADD NEW TOOLS HERE ONLY.
# Immutable; use the accessor functions below rather than touching directly.
_REGISTERED_TOOLS: tuple[ToolDefinition, ...] = (
    ToolDefinition(
        DEFAULT_TOOL_NAME,
        "Pen",
        "Freehand drawing.",
        PenTool,
    ),
    ToolDefinition(
        "fine-pen",
        "Fine",
        "Precise single-pixel pen: \n\n"
        "• left-click top pixel\n"
        "• middle-click both pixels\n"
        "• right-click top pixel",
        FinePenTool,
    ),
    ToolDefinition(
        "spray",
        "Spray",
        "Spray paint effect.",
        SprayTool,
        supports_normalized=True,
    ),
    ToolDefinition(
        "paint_bucket",
        "Fill",
        "Flood fill from the cursor.",
        PaintBucketTool,
    ),
    ToolDefinition(
        "eraser",
        "Erase",
        "Erase pixels.",
        EraserTool,
    ),
    ToolDefinition(
        "rectangle",
        "Rect",
        "Draw a rectangle.",
        RectangleTool,
        max_brush_size=3,
    ),
    ToolDefinition(
        "line",
        "Line",
        "Draw a straight line.",
        LineTool,
        supports_normalized=True,
    ),
    ToolDefinition(
        "circle",
        "Circle",
        "Draw a circle.",
        CircleTool,
        supports_normalized=True,
        max_brush_size=3,
    ),
    ToolDefinition(
        "ellipse",
        "Ellipse",
        "Draw an ellipse.",
        EllipseTool,
        supports_normalized=True,
        max_brush_size=3,
    ),
)


def get_tool_names_and_labels() -> list[tuple[str, str]]:
    """Get tool names and labels for UI."""
    return [(t.name, t.label) for t in _REGISTERED_TOOLS]


def get_tool_definitions() -> list[ToolDefinition]:
    """Get tool definitions for UI."""
    return list(_REGISTERED_TOOLS)


def instantiate_tools() -> dict[str, Tool]:
    """Create tool instances for canvas, verifying name/class agreement."""
    tools: dict[str, Tool] = {}
    for definition in _REGISTERED_TOOLS:
        instance = definition.tool_class()
        if instance.name != definition.name:
            raise ValueError(
                f"Tool {definition.tool_class.__name__} has name "
                f"{instance.name!r} but is registered as {definition.name!r}."
            )
        tools[definition.name] = instance
    return tools


def get_default_tool_name() -> str:
    """Get the name of the default tool."""
    return DEFAULT_TOOL_NAME


def get_normalized_capable_tool_names() -> frozenset[str]:
    """Return the names of tools that support normalized drawing mode."""
    return frozenset(t.name for t in _REGISTERED_TOOLS if t.supports_normalized)


def get_max_brush_size(tool_name: str) -> int:
    """Get the maximum brush size for a tool.

    Falls back to the global MAX_BRUSH_SIZE for unknown tool names.
    """
    for definition in _REGISTERED_TOOLS:
        if definition.name == tool_name:
            return definition.max_brush_size
    return MAX_BRUSH_SIZE
