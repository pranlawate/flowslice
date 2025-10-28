"""flowslice - Dataflow slicing for Python.

Trace where your variables come from and where they go.
"""

__version__ = "1.0.0"

from flowslice.core.models import SliceDirection, SliceResult
from flowslice.core.slicer import Slicer
from flowslice.formatters.graph import GraphFormatter
from flowslice.formatters.json import JSONFormatter
from flowslice.formatters.tree import TreeFormatter

__all__ = [
    "Slicer",
    "SliceDirection",
    "SliceResult",
    "TreeFormatter",
    "JSONFormatter",
    "GraphFormatter",
    "__version__",
]
