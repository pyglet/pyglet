"""Select and run tests supported by the Pyodide browser environment."""
from __future__ import annotations

from pathlib import Path

import pytest


tests_root = Path("/tests")
test_files = sorted(
    str(path)
    for path in (
        *tests_root.joinpath("unit").rglob("test_*.py"),
        *tests_root.joinpath("integration", "graphics").glob("test_*.py"),
        *tests_root.joinpath("integration", "graphics", "webgl").glob("test_*.py"),
        *tests_root.joinpath("integration", "platform", "pyodide").glob("test_*.py"),
    )
)
if not test_files:
    raise RuntimeError("No supported tests were included in the Pyodide project.")

PYGLET_PYTEST_EXIT_CODE = int(pytest.main([
    *test_files,
    "-v",
    "--tb=short",
    "-p",
    "no:cacheprovider",
]))
