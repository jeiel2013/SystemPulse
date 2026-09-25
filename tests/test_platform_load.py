"""Platform-specific load average behavior."""

import os
import sys

import pytest

from systempulse.platform.load import get_load_average


def test_load_average_is_unavailable_on_windows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "platform", "win32")

    assert get_load_average() is None


def test_load_average_uses_native_counter_on_linux(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(os, "getloadavg", lambda: (1.0, 2.0, 3.0), raising=False)

    assert get_load_average() == (1.0, 2.0, 3.0)
