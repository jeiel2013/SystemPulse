"""Read a quit key without blocking the monitor on supported terminals."""

import os
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager


@contextmanager
def quit_key_reader() -> Iterator[Callable[[], bool]]:
    """Temporarily enable single-key input and restore the terminal on exit."""
    if os.name == "nt":
        import msvcrt

        def pressed() -> bool:
            # Unix type stubs omit Windows-only msvcrt attributes.
            if not bool(getattr(msvcrt, "kbhit")()):  # noqa: B009
                return False
            return bool(getattr(msvcrt, "getwch")().lower() == "q")  # noqa: B009

        yield pressed
        return

    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    # Windows type stubs omit Unix-only termios and tty attributes.
    original = getattr(termios, "tcgetattr")(fd)  # noqa: B009
    try:
        getattr(tty, "setcbreak")(fd)  # noqa: B009

        def pressed() -> bool:
            readable, _, _ = select.select([fd], [], [], 0)
            return bool(readable) and os.read(fd, 1).lower() == b"q"

        yield pressed
    finally:
        getattr(termios, "tcsetattr")(  # noqa: B009
            fd,
            getattr(termios, "TCSADRAIN"),  # noqa: B009
            original,
        )
