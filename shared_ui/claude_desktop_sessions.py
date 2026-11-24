from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path


def session_records() -> Iterator[Path]:
    local = os.environ.get("LOCALAPPDATA")
    places = [Path(base) for base in (os.environ.get("APPDATA"), local) if base]
    if local:
        places += [cache / kind for cache in Path(local).glob("Packages/Claude_*/LocalCache")
                   for kind in ("Roaming", "Local")]
    for place in places:
        for data_folder in (*place.glob("Claude*"), *place.glob("Claude*/*")):
            yield from data_folder.glob("claude-code-sessions/*/*/local_*.json")
