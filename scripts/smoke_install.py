"""Install the built wheel as an isolated tool and run its public commands."""

import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    wheels = tuple((ROOT / "dist").glob("systempulse_monitor-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(
            f"Expected one SystemPulse wheel in dist/, found {len(wheels)}"
        )
    wheel = wheels[0]
    with zipfile.ZipFile(wheel) as archive:
        if "systempulse/tui/styles.tcss" not in archive.namelist():
            raise RuntimeError("The wheel does not contain the TUI stylesheet")

    uv = shutil.which("uv") or str(ROOT / "uv.exe")
    if not Path(uv).is_file():
        raise RuntimeError("uv executable was not found")
    expected_version = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))[
        "project"
    ]["version"]

    with tempfile.TemporaryDirectory(prefix="systempulse-install-") as directory:
        target = Path(directory)
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment["UV_TOOL_DIR"] = str(target / "tools")
        environment["UV_TOOL_BIN_DIR"] = str(target / "bin")
        subprocess.run(
            [uv, "tool", "install", "--python", "3.12", str(wheel)],
            cwd=target,
            env=environment,
            check=True,
            timeout=120,
        )
        command = (
            target / "bin" / ("systempulse.exe" if os.name == "nt" else "systempulse")
        )
        if not command.is_file():
            raise RuntimeError(f"Installed command not found: {command}")

        for arguments, expected in (
            (("version",), f"SystemPulse {expected_version}"),
            (("status",), "SystemPulse"),
            (("top", "--help"), "Continuously show"),
            (("processes", "--limit", "3"), "Processes"),
            (("doctor",), "SystemPulse doctor"),
        ):
            result = subprocess.run(
                [str(command), *arguments],
                cwd=target,
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode or expected not in result.stdout:
                raise RuntimeError(
                    f"{' '.join(arguments)} failed (exit {result.returncode}):\n"
                    f"{result.stdout}\n{result.stderr}"
                )
            print(f"PASS: systempulse {' '.join(arguments)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
