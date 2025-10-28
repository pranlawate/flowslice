"""ANSI color support for terminal output."""

import os
import sys


class Colors:
    """ANSI color codes for terminal output."""

    # Check if colors are supported
    _colors_enabled = (
        hasattr(sys.stdout, "isatty")
        and sys.stdout.isatty()
        and os.getenv("NO_COLOR") is None
    )

    # Color codes
    RESET = "\033[0m" if _colors_enabled else ""
    BOLD = "\033[1m" if _colors_enabled else ""
    DIM = "\033[2m" if _colors_enabled else ""

    # Foreground colors
    BLACK = "\033[30m" if _colors_enabled else ""
    RED = "\033[31m" if _colors_enabled else ""
    GREEN = "\033[32m" if _colors_enabled else ""
    YELLOW = "\033[33m" if _colors_enabled else ""
    BLUE = "\033[34m" if _colors_enabled else ""
    MAGENTA = "\033[35m" if _colors_enabled else ""
    CYAN = "\033[36m" if _colors_enabled else ""
    WHITE = "\033[37m" if _colors_enabled else ""

    # Bright foreground colors
    BRIGHT_BLACK = "\033[90m" if _colors_enabled else ""
    BRIGHT_RED = "\033[91m" if _colors_enabled else ""
    BRIGHT_GREEN = "\033[92m" if _colors_enabled else ""
    BRIGHT_YELLOW = "\033[93m" if _colors_enabled else ""
    BRIGHT_BLUE = "\033[94m" if _colors_enabled else ""
    BRIGHT_MAGENTA = "\033[95m" if _colors_enabled else ""
    BRIGHT_CYAN = "\033[96m" if _colors_enabled else ""
    BRIGHT_WHITE = "\033[97m" if _colors_enabled else ""

    @classmethod
    def disable(cls) -> None:
        """Disable color output."""
        cls._colors_enabled = False
        cls.RESET = ""
        cls.BOLD = ""
        cls.DIM = ""
        cls.BLACK = ""
        cls.RED = ""
        cls.GREEN = ""
        cls.YELLOW = ""
        cls.BLUE = ""
        cls.MAGENTA = ""
        cls.CYAN = ""
        cls.WHITE = ""
        cls.BRIGHT_BLACK = ""
        cls.BRIGHT_RED = ""
        cls.BRIGHT_GREEN = ""
        cls.BRIGHT_YELLOW = ""
        cls.BRIGHT_BLUE = ""
        cls.BRIGHT_MAGENTA = ""
        cls.BRIGHT_CYAN = ""
        cls.BRIGHT_WHITE = ""

    @classmethod
    def enable(cls) -> None:
        """Enable color output."""
        cls._colors_enabled = True
        cls.RESET = "\033[0m"
        cls.BOLD = "\033[1m"
        cls.DIM = "\033[2m"
        cls.BLACK = "\033[30m"
        cls.RED = "\033[31m"
        cls.GREEN = "\033[32m"
        cls.YELLOW = "\033[33m"
        cls.BLUE = "\033[34m"
        cls.MAGENTA = "\033[35m"
        cls.CYAN = "\033[36m"
        cls.WHITE = "\033[37m"
        cls.BRIGHT_BLACK = "\033[90m"
        cls.BRIGHT_RED = "\033[91m"
        cls.BRIGHT_GREEN = "\033[92m"
        cls.BRIGHT_YELLOW = "\033[93m"
        cls.BRIGHT_BLUE = "\033[94m"
        cls.BRIGHT_MAGENTA = "\033[95m"
        cls.BRIGHT_CYAN = "\033[96m"
        cls.BRIGHT_WHITE = "\033[97m"


def colorize(text: str, color: str, bold: bool = False) -> str:
    """Colorize text with ANSI codes.

    Args:
        text: The text to colorize
        color: The color code (e.g., Colors.GREEN)
        bold: Whether to make the text bold

    Returns:
        Colorized text
    """
    if not Colors._colors_enabled:
        return text

    prefix = f"{Colors.BOLD}{color}" if bold else color
    return f"{prefix}{text}{Colors.RESET}"
