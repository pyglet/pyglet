from __future__ import annotations

import sys
from pathlib import Path

import pytest

if sys.platform != "emscripten":
    pytest.skip("requires the Emscripten/Pyodide runtime", allow_module_level=True)

from pyodide.ffi import run_sync
from pyglet.libs.emscripten.filesystem import mount_idbfs, sync_idbfs, unmount_idbfs


def test_idbfs_mount_exposes_persistent_python_directory(tmp_path):
    mount_path = f"/pyglet-test-{tmp_path.name}"
    run_sync(mount_idbfs(mount_path))
    try:
        path = Path(mount_path, "settings.txt")
        path.write_text("pyglet")
        run_sync(sync_idbfs())
        assert path.read_text() == "pyglet"
    finally:
        unmount_idbfs(mount_path)
