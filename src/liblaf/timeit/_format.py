"""Stable plain-text formatting for timing events."""

import math


def format_duration(seconds: float) -> str:
    """Format seconds using a compact unit without optional dependencies.

    Examples:
        >>> format_duration(0.0015)
        '1.5 ms'
        >>> format_duration(65)
        '1.083 min'
    """
    if not math.isfinite(seconds):
        return str(seconds)
    magnitude = abs(seconds)
    if magnitude < 1e-6:
        value, unit = seconds * 1e9, "ns"
    elif magnitude < 1e-3:
        value, unit = seconds * 1e6, "µs"
    elif magnitude < 1:
        value, unit = seconds * 1e3, "ms"
    elif magnitude < 60:
        value, unit = seconds, "s"
    elif magnitude < 3600:
        value, unit = seconds / 60, "min"
    else:
        value, unit = seconds / 3600, "h"
    return f"{value:.4g} {unit}"
