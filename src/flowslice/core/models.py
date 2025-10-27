"""Data models for flowslice."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SliceDirection(Enum):
    """Direction of slicing."""

    BACKWARD = "backward"
    FORWARD = "forward"
    BOTH = "both"


@dataclass
class SliceNode:
    """Represents a single node in the slice."""

    file: str
    line: int
    function: str
    code: str
    variable: str
    operation: str
    dependencies: list[str] = field(default_factory=list)
    context: Optional[str] = None


@dataclass
class SliceResult:
    """Result of slicing operation."""

    target_file: str
    target_line: int
    target_variable: str
    backward_slice: list[SliceNode] = field(default_factory=list)
    forward_slice: list[SliceNode] = field(default_factory=list)
