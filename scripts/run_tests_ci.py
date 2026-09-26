"""Run pytest and expose failures as GitHub check annotations."""

import subprocess
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree


def _escape(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="systempulse-pytest-") as directory:
        report = Path(directory) / "results.xml"
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", f"--junitxml={report}"],
            capture_output=True,
            text=True,
            check=False,
        )
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        if result.returncode and report.is_file():
            for case in ElementTree.parse(report).iter("testcase"):
                failure = case.find("failure")
                if failure is None:
                    failure = case.find("error")
                if failure is None:
                    continue
                title = _escape(f"{case.get('classname')}.{case.get('name')}")
                detail = _escape((failure.text or failure.get("message") or "")[-3000:])
                print(f"::error title={title}::{detail}")
        return result.returncode


if __name__ == "__main__":
    sys.exit(main())
