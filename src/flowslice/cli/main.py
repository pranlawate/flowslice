"""Command-line interface for flowslice."""

import sys
from pathlib import Path
from typing import Union

from flowslice.core.models import SliceDirection
from flowslice.core.slicer import Slicer
from flowslice.formatters.dot import DotFormatter
from flowslice.formatters.graph import GraphFormatter
from flowslice.formatters.json import JSONFormatter
from flowslice.formatters.tree import TreeFormatter


def main() -> None:
    """CLI entry point for flowslice."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    # Parse input
    criterion = sys.argv[1]
    direction_str = sys.argv[2] if len(sys.argv) > 2 else "both"
    format_str = sys.argv[3] if len(sys.argv) > 3 else "tree"

    # Parse direction
    try:
        direction = SliceDirection(direction_str.lower())
    except ValueError:
        print(f"Error: Invalid direction '{direction_str}'")
        print("Valid directions: backward, forward, both")
        sys.exit(1)

    # Parse format
    format_str = format_str.lower()
    if format_str not in ("tree", "graph", "json", "dot"):
        print(f"Error: Invalid format '{format_str}'")
        print("Valid formats: tree, graph, json, dot")
        sys.exit(1)

    # Parse criterion (file:line:variable)
    try:
        file_path, line_str, variable = criterion.split(":")
        line = int(line_str)
    except ValueError:
        print("Error: Invalid format. Use <file>:<line>:<variable>")
        print("Example: main.py:42:result")
        sys.exit(1)

    # Check file exists
    if not Path(file_path).exists():
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)

    # Perform slicing
    slicer = Slicer()
    result = slicer.slice(file_path, line, variable, direction)

    # Select formatter
    formatter: Union[GraphFormatter, JSONFormatter, DotFormatter, TreeFormatter]
    if format_str == "graph":
        formatter = GraphFormatter()
    elif format_str == "json":
        formatter = JSONFormatter()
    elif format_str == "dot":
        formatter = DotFormatter()
    else:  # tree (default)
        formatter = TreeFormatter()

    # Format and print result
    output = formatter.format(result, direction)
    print(output)


def print_usage() -> None:
    """Print usage information."""
    print("flowslice - Dataflow Slicing for Python")
    print("\nUsage:")
    print("  flowslice <file>:<line>:<variable> [direction] [format]")
    print("\nArguments:")
    print("  file        Path to Python file to analyze")
    print("  line        Line number where variable appears")
    print("  variable    Name of variable to trace")
    print("  direction   Slicing direction: backward, forward, or both (default: both)")
    print("  format      Output format: tree, graph, or json (default: tree)")
    print("\nFormats:")
    print("  tree        Classic tree view (default)")
    print("  graph       Grouped DAG view showing convergence/divergence")
    print("  json        Machine-readable JSON output")
    print("\nExamples:")
    print("  flowslice main.py:1251:skipped both")
    print("  flowslice main.py:1251:skipped backward graph")
    print("  flowslice example.py:26:result forward json")


if __name__ == "__main__":
    main()
