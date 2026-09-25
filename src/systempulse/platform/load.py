"""Load average capability across the supported operating systems."""

import os
import sys
from collections.abc import Callable
from typing import cast


def get_load_average() -> tuple[float, float, float] | None:
    """Return native load averages where they are available."""
    if sys.platform not in {"linux", "darwin"}:
        return None
    native_load = cast(
        "Callable[[], tuple[float, float, float]] | None",
        getattr(os, "getloadavg", None),
    )
    if native_load is None:
        return None
    try:
        return native_load()
    except (AttributeError, OSError):
        return None
