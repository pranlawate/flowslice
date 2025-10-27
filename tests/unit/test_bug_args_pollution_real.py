"""Test for real-world args pollution bug."""

import tempfile
from pathlib import Path

import pytest

from flowslice.core.models import SliceDirection
from flowslice.core.slicer import Slicer


def test_args_pollution_real_world():
    """Reproduce the real bug with many unrelated args usages."""
    code = """
def main(args):
    # Target line: file_path depends on args.file
    file_path = args.file

    detected_format = detect_file_format(file_path)

    # Many unrelated args usages below
    # These should NOT appear in backward slice of file_path

    if args.raw:
        file_path = args.file if args.file else args.raw_file

    if args.avc:
        file_path = args.file if args.file else args.avc_file

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Lots of unrelated args usages
    sorted_data = sort_denials(data, args.sort)
    filtered_data = filter_denials(
        data,
        args.type,
        args.scontext,
        args.tcontext,
        args.tclass,
        args.permission
    )

    if args.process:
        filter_msg = f"process='{args.process}'"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()
        temp_path = f.name

    try:
        slicer = Slicer()
        # Slice file_path at line 4 (the initial assignment)
        result = slicer.slice(temp_path, 4, "file_path", SliceDirection.BACKWARD)

        print("\n=== BACKWARD SLICE RESULTS ===")
        for node in result.backward_slice:
            print(f"Line {node.line}: {node.code.strip()}")
            if node.dependencies:
                print(f"  Dependencies: {node.dependencies}")

        # Count how many nodes reference args
        args_references = [node for node in result.backward_slice if "args" in node.code]

        print(f"\n=== ANALYSIS ===")
        print(f"Total slice nodes: {len(result.backward_slice)}")
        print(f"Nodes referencing 'args': {len(args_references)}")

        # The backward slice should be very small - just the line itself
        # It should NOT include all the subsequent args usages
        assert len(result.backward_slice) <= 3, \
            f"Backward slice too large! Found {len(result.backward_slice)} nodes, " \
            f"expected <= 3. This suggests args pollution bug."

    finally:
        Path(temp_path).unlink()


if __name__ == "__main__":
    test_args_pollution_real_world()
