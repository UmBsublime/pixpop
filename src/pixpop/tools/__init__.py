"""Canvas drawing tools package."""

from pixpop.tools.base import CanvasProtocol, Tool, snap_to_normalized
from pixpop.tools.circle import CircleTool
from pixpop.tools.continuous_tool import ContinuousTool
from pixpop.tools.ellipse import EllipseTool
from pixpop.tools.eraser import EraserTool
from pixpop.tools.fine_pen import FinePenTool
from pixpop.tools.line import LineTool
from pixpop.tools.paint_bucket import PaintBucketTool
from pixpop.tools.pen import PenTool
from pixpop.tools.rectangle import RectangleTool
from pixpop.tools.registry import (
    get_default_tool_name,
    get_max_brush_size,
    get_normalized_capable_tool_names,
    get_tool_definitions,
    get_tool_names_and_labels,
    instantiate_tools,
)
from pixpop.tools.shape_tool import ShapeTool
from pixpop.tools.spray import SprayTool

__all__ = [
    "Tool",
    "CanvasProtocol",
    "ShapeTool",
    "ContinuousTool",
    "snap_to_normalized",
    "CircleTool",
    "EllipseTool",
    "EraserTool",
    "FinePenTool",
    "LineTool",
    "PaintBucketTool",
    "PenTool",
    "RectangleTool",
    "SprayTool",
    "get_default_tool_name",
    "get_max_brush_size",
    "get_normalized_capable_tool_names",
    "get_tool_definitions",
    "get_tool_names_and_labels",
    "instantiate_tools",
]
