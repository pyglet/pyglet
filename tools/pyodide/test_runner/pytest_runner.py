"""Run the WebGL test modules from inside Pyodide."""
from __future__ import annotations

from pathlib import Path

import pytest


test_files = sorted(str(path) for path in Path("/tests").glob("*/test_*.py"))
if not test_files:
    raise RuntimeError("No WebGL tests were included in the Pyodide project.")

PYGLET_PYTEST_EXIT_CODE = int(pytest.main([*test_files, "-v", "--tb=short"]))
