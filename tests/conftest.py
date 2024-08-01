

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

