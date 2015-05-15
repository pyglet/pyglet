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

# Try to get python-future
try:
    import future
except ImportError:
    import os.path as op
    import sys
    sys.path.insert(0, op.abspath(op.join(op.dirname(__file__), 'extlibs', 'future')))
    del sys
    del op
    try:
        import future
    except ImportError:
        print('Failed to get python-future')
        raise

