"""JSON formatter for flowslice results."""

import json
from typing import Any

from flowslice.core.models import SliceDirection, SliceNode, SliceResult


class JSONFormatter:
    """Format slice results as JSON."""

    @staticmethod
    def format(
        result: SliceResult, direction: SliceDirection = SliceDirection.BOTH, indent: int = 2
    ) -> str:
        """Format a SliceResult as JSON.

        Args:
            result: The SliceResult to format.
            direction: Which direction(s) to display.
            indent: Number of spaces for indentation (default: 2).

        Returns:
            Formatted JSON string.
        """
        data: dict[str, Any] = {
            "target": {
                "file": result.target_file,
                "line": result.target_line,
                "variable": result.target_variable,
            }
        }

        if direction in (SliceDirection.BACKWARD, SliceDirection.BOTH) and result.backward_slice:
            data["backward_slice"] = [
                JSONFormatter._node_to_dict(node) for node in result.backward_slice
            ]

        if direction in (SliceDirection.FORWARD, SliceDirection.BOTH) and result.forward_slice:
            data["forward_slice"] = [
                JSONFormatter._node_to_dict(node) for node in result.forward_slice
            ]

        # Add statistics
        all_files = set(n.file for n in result.backward_slice + result.forward_slice)
        all_functions = set(
            n.function for n in result.backward_slice + result.forward_slice
        )

        data["statistics"] = {
            "total_lines": len(result.backward_slice) + len(result.forward_slice),
            "files_involved": sorted(list(all_files)),
            "functions_involved": sorted(list(all_functions)),
        }

        return json.dumps(data, indent=indent)

    @staticmethod
    def _node_to_dict(node: SliceNode) -> dict[str, Any]:
        """Convert a SliceNode to a dictionary.

        Args:
            node: The SliceNode to convert.

        Returns:
            Dictionary representation of the node.
        """
        node_dict: dict[str, Any] = {
            "file": node.file,
            "line": node.line,
            "function": node.function,
            "code": node.code.strip(),
            "variable": node.variable,
            "operation": node.operation,
        }

        if node.dependencies:
            node_dict["dependencies"] = node.dependencies

        if node.context:
            node_dict["context"] = node.context

        return node_dict
