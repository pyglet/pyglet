Testing pyglet
==============
Test Suites
-----------
Tests for pyglet are divided into 3 suites.

Unit tests
''''''''''

Unit tests only cover a single unit of code or a combination of a limited number of units. No
resource intensive computations should be included. These tests should run in limited time without
any user interaction.

Integration tests
'''''''''''''''''

Integration tests cover the integration of components of pyglet into the whole of pyglet and
the integration into the supported systems. Like unit tests these tests do not require user
interaction, but they can take longer to run due to access to system resources.

Interactive tests
'''''''''''''''''

Interactive tests require the user to verify whether the test is successful and in some cases
require the user to perform actions in order for the test to continue. These tests can take a
long time to run.

There are currently 3 types of interactive test cases:

    - tests that can only run in fully interactive mode as they require the user to perform an
      action in order for the test to continue. These tests are decorated with
      :func:`~tests.interactive.interactive_test_base.requires_user_action`.
    - tests that can run without user interaction, but that cannot validate whether they should
      pass or fail. These tests are docorated with
      :func:`~tests.interactive.interactive_test_base.requires_user_validation`.
    - tests that can run without user interaction and that can compare results to screenshots from
      a previous run to determine whether they pass or fail. This is the default type.

Running tests
-------------

The pyglet test suite is based on the `py.test framework <http://pytest.org>`_.

It is preferred to use a virtual environment to run the tests. For instructions to set
up virtual environments see :doc:`virtualenv`.
Make sure the virtual environment for the Python version you want to test is active. It is
preferred to run the tests on 2.7, 3.4 and 3.5 to make sure changes are compatible with all
supported Python versions.

To run all tests, execute py.test in the root of the pyglet repository::

    py.test

You can also run just a single suite::

    py.test tests/unit
    py.test tests/integration
    py.test tests/interactive

For the interactive test suites, there are some extra command line switches for py.test:

    - ``--non-interactive``: Only run the interactive tests that can only verify themselves using
      screenshots. The screenshots are created when you run the tests in interactive mode, so you
      will need to run the tests interactively once, before you can use this option;
    - ``--sanity``: Do a sanity check by running as many interactive tests without user intervention.
      Not all tests can run without intervention, so these tests will still be skipped. Mostly
      useful to quickly check changes in code. Not all tests perform complete validation.

Writing tests
-------------

Annotations
'''''''''''

Some control over test execution can be exerted by using annotations in the form of
decorators. One function of annotations is to skip tests under certain conditions.

General annotations
^^^^^^^^^^^^^^^^^^^

General test annotations are available in the module :mod:`tests.annotations`.

.. py:currentmodule:: tests.annotations
.. py:decorator:: require_platform(platform)

   Only run the test on the given platform(s), skip on other platforms.

   :param list(str) platform: A list of platform identifiers as returned by
       :data:`pyglet.options`. See also :class:`~tests.annotations.Platform`.

.. py:decorator:: skip_platform(platform)

   Skip test on the given platform(s).

   :param list(str) platform: A list of platform identifiers as returned by
       :data:`pyglet.options`. See also :class:`~tests.annotations.Platform`.

.. autoclass:: tests.annotations.Platform
   :members:

.. py:decorator:: require_gl_extension(extension)

   Skip the test if the given GL extension is not available.

   :param str extension: Name of the extension required.

Suite annotations
^^^^^^^^^^^^^^^^^

This is currently not used.

.. py:decorator:: pytest.mark.unit

   Test belongs to the unit test suite.

.. py:decorator:: pytest.mark.integration

   Test belongs to the integration test suite.

.. py:decorator:: pytest.mark.interactive

  Test belongs to the interactive test suite.

Interactive test annotations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Interactive test cases can be marked with specific py.test marks. Currently
the following marks are used:

.. py:decorator:: pytest.mark.requires_user_action

   Test requires user interaction to run. It needs to be skipped when running in
   non-interactive or sanity mode.

.. py:decorator:: pytest.mark.requires_user_validation

   User validation is required to mark the test passed or failed. However the test
   can run in sanity mode.

.. py:decorator:: pytest.mark.only_interactive

   For another reason the test can only run in interactive mode.

