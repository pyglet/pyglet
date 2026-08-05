"""Helpers for importing browser-provided files into Pyodide's file system."""
from __future__ import annotations

from pathlib import Path, PurePath
from typing import Any
from uuid import uuid4

import js  # noqa: F821


_IMPORT_ROOT = Path("/tmp/pyglet-imports")  # noqa: S108


def _safe_filename(name: str, index: int) -> str:
    """Return a file name that cannot escape its temporary import directory."""
    name = PurePath(str(name).replace("\\", "/")).name
    return name if name not in {"", ".", ".."} else f"file-{index}"


async def import_files(files: Any) -> list[str]:
    """Copy browser ``File`` objects into a unique temporary VFS directory."""
    if not files:
        return []

    directory = _IMPORT_ROOT / uuid4().hex
    directory.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for index, file in enumerate(files):
        filename = _safe_filename(file.name, index)
        path = directory / filename
        # Keep duplicate names distinct while retaining a useful name in the VFS.
        stem, extension = path.stem, path.suffix
        duplicate = 1
        while path.exists():
            path = directory / f"{stem}-{duplicate}{extension}"
            duplicate += 1

        data = js.Uint8Array.new(await file.arrayBuffer())
        try:
            with path.open("wb") as output:
                data.to_file(output)
        finally:
            data.destroy()
        paths.append(str(path))
    return paths
