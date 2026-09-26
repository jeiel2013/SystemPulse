"""A release dispatch must use a tag matching the built package version."""

import subprocess
import sys
import tomllib
from pathlib import Path


def test_release_tag_matches_package_version() -> None:
    root = Path(__file__).resolve().parents[1]
    version = tomllib.loads((root / "pyproject.toml").read_text("utf-8"))["project"][
        "version"
    ]
    command = [sys.executable, str(root / "scripts" / "check_release_tag.py")]
    valid = subprocess.run([*command, f"v{version}"], cwd=root, check=False)
    invalid = subprocess.run(
        [*command, "main"], cwd=root, check=False, capture_output=True, text=True
    )
    assert valid.returncode == 0
    assert invalid.returncode != 0
    assert "must match" in invalid.stderr
