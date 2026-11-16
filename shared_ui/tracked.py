from __future__ import annotations

import os
import subprocess
from pathlib import Path


def tracked(root: Path) -> tuple[list[Path], str]:
    quiet = {name: value for name, value in os.environ.items() if not name.startswith("GIT_")}
    listed = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                            capture_output=True, text=True, encoding="utf-8", env=quiet, check=False)
    return [root / name for name in listed.stdout.split("\0") if name], listed.stderr
