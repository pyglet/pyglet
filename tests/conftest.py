

def pytest_addoption(parser):
    """Add the special options for interactive tests."""
    parser.addoption('--non-interactive',
                     action='store_true',
                     help='Exclude interactive tests from the run.',
                     )
    parser.addoption('--sanity',
                     action='store_true',
                     help='[Interactive tests only] Do not use interactive prompts. '
                          'Only skips tests that cannot finish without user intervention.',
                     )


def pytest_ignore_collect(collection_path, config):
    """Avoid importing the interactive suite during automated runs."""
    if config.getoption('--non-interactive', False):
        interactive_dir = Path(__file__).parent / 'interactive'
        if collection_path == interactive_dir or interactive_dir in collection_path.parents:
            return True
    return None


def pytest_collection_modifyitems(items, config):
    """Also exclude explicitly selected interactive tests and marked tests."""
    if not config.getoption('--non-interactive', False):
        return

    interactive_dir = Path(__file__).parent / 'interactive'
    markers = ('interactive', 'only_interactive', 'requires_user_action', 'requires_user_validation')
    remaining = []
    deselected = []
    for item in items:
        if (interactive_dir in item.path.parents
                or any(item.get_closest_marker(marker) is not None for marker in markers)):
            deselected.append(item)
        else:
            remaining.append(item)
    if deselected:
        items[:] = remaining
        config.hook.pytest_deselected(items=deselected)


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
from pathlib import Path

import pyglet
