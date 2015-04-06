"""
Test Suite for Pyglet
=====================

NOTE: This description is desired implementation. Still in progress.

The test suite is divided in the following segments:
    - unit tests
    - integration tests
    - interactive test

The unit and integration tests should run without user interaction. Unit tests are limited to
functionality contained in a single module/entity, while integration tests test integration
between different modules and towards the system.
Interactive tests require human interaction to validate the outcomes. They are mostly about
verifying display of rendering.

If any test requires external data files, please put them in the appropriate data directory. This
way the tests can share a limited set of resources.

Running unit and integration tests
----------------------------------
The tests run using Python's unittest module. They support running directly using that module, but
to support extra options a wrapper is created.

To run using the wrapper:
    python -m tests.run [unit] [integration] [interactive]
Here you can combine any of the suites to run.

To run using unittest directly:
    python -m unittest discover tests.unit
    python -m unittest discover tests.integration
    python -m unittest discover tests.interactive
    python -m unittest discover tests

The unit and integration tests should run fully automatic in a limited amount of time. The
integration tests might spawn windows for rendering. No need to interact with these windows.
The interactive tests require you to watch what happens and then respond whether they are passed
or failed.

You can also run all the interactive tests without giving feedback. This has two functions:
    - If the tests supports screenshots, it will compare to a reference screenshot to determine
      pass or fail.
    - If not, the test can still verify that no exceptions or crashes occurs.
Some test cases do not support running non interactively, they will be skipped.

To run without interaction:
    python -m tests.run interactive --non-interactive
    python -m tests.run interactive -n

You can also combine all tests in this way:
    python -m tests.run unit integration interactive -n

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

