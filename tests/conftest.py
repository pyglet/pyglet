

def pytest_addoption(parser):
    """Add the special options for interactive tests."""
    parser.addoption('--non-interactive',
                     action='store_true',
                     help='[Interactive tests only] Do not use interactive prompts. '
                          'Skip tests that cannot validate or run without.',
                     )
    parser.addoption('--sanity',
                     action='store_true',
                     help='[Interactive tests only] Do not use interactive prompts. '
                          'Only skips tests that cannot finish without user intervention.',
                     )


# Import shared fixtures
from .base.data import test_data
from .base.performance import performance


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print rendering backend details in the test summary footer."""
    terminalreporter.write_sep("=", "Graphics Backend")
    terminalreporter.write_line(f"pyglet.options.backend: {pyglet.options.backend}")
    env_backend = os.environ.get("PYGLET_BACKEND")
    terminalreporter.write_line(f"PYGLET_BACKEND env: {env_backend if env_backend is not None else '<unset>'}")

import os

import pyglet
