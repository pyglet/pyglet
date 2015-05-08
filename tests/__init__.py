"""
Please see doc/internal/testing.txt for test documentation.
"""

# Try to get a version of mock
try:
    # Python 3.3+ has mock in the stdlib
    import unittest.mock as mock
except ImportError:
    try:
        # User could have mock installed
        import mock
    except ImportError:
        # Last resort: use included mock library
        import tests.extlibs.mock as mock

