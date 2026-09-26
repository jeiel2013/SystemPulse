"""Require the manually selected release tag to match package metadata."""

import sys
import tomllib
from pathlib import Path


def check_tag(tag: str) -> None:
    version = tomllib.loads(Path("pyproject.toml").read_text("utf-8"))["project"][
        "version"
    ]
    expected = f"v{version}"
    if tag != expected:
        raise ValueError(f"Release tag {tag!r} must match {expected!r}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: check_release_tag.py vX.Y.Z")
    check_tag(sys.argv[1])
