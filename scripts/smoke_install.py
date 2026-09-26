"""Install the built wheel as an isolated tool and run its public commands."""

import os
import shutil
import subprocess
import sys
import tarfile
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
    sources = tuple((ROOT / "dist").glob("systempulse_monitor-*.tar.gz"))
    if len(sources) != 1:
        raise RuntimeError(
            f"Expected one SystemPulse source archive in dist/, found {len(sources)}"
        )
    with tarfile.open(sources[0]) as archive:
        names = archive.getnames()
        if any(".uv-cache" in name or "__pycache__" in name for name in names):
            raise RuntimeError("The source archive contains generated cache files")
        if not any(name.endswith("/LICENSE") for name in names):
            raise RuntimeError("The source archive does not contain the license")

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
        environment["APPDATA"] = str(target / "appdata")
        environment["LOCALAPPDATA"] = str(target / "localappdata")
        environment["XDG_CONFIG_HOME"] = str(target / "config")
        environment["XDG_DATA_HOME"] = str(target / "data")
        environment["XDG_CACHE_HOME"] = str(target / "cache")
        environment["SYSTEMPULSE_DATA_DIR"] = str(target / "systempulse-data")
        environment["SYSTEMPULSE_CONFIG_DIR"] = str(target / "systempulse-config")
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
            (("history", "--range", "10m"), "SystemPulse history"),
            (("alerts",), "No alerts recorded"),
            (("tree", "--limit", "3"), "Process tree"),
            (("report", "--format", "json"), "Export completed:"),
            (("plugins",), "No collector plugins installed"),
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
        if not tuple((target / "systempulse-data" / "reports").glob("*.json")):
            raise RuntimeError("The report was not written to isolated user data")
    return 0


if __name__ == "__main__":
    sys.exit(main())
