from __future__ import print_function

import array
import inspect
import os
import pyglet
from pyglet.image import get_buffer_manager
import shutil
import unittest
import warnings

try:
    # If the easygui package is available, use it to display popup questions, instead of using the
    # console (which might lose focus to the Pyglet windows).
    # Not using Pyglet to show a window with the question to prevent interfering with the test.
    import easygui
    _has_gui = True
except:
    _has_gui = False

local_dir = os.path.dirname(__file__)

base_screenshot_path = os.path.join(local_dir, 'screenshots')
committed_screenshot_path = os.path.join(base_screenshot_path, 'committed')
session_screenshot_path = os.path.join(base_screenshot_path, 'session')

test_data_path = os.path.abspath(os.path.join(local_dir, '..', 'data'))

del local_dir

# Filters for tests, corresponds to the decorators for tests
run_only_interactive = True
run_requires_user_action = True
run_requires_user_validation = True

# Show interactive prompts or not
interactive = True

# Allow tests missing reference screenshots to pass
allow_missing_screenshots = False

def set_noninteractive_sanity():
    """
    Filter tests to run in sanity check mode. Test cases that require the user to validate the
    outcome will run, but the validation steps are skipped. Test cases that cannot run without
    user intervention will be skipped. Fully automatic tests (using asserts and screenshot
    comparison) also run without user intervention.
    """
    global run_only_interactive, run_requires_user_action, run_requires_user_validation
    global interactive, allow_missing_screenshots

    run_only_interactive = False
    run_requires_user_action = False
    run_requires_user_validation = True
    interactive = False
    allow_missing_screenshots = True


def set_noninteractive_only_automatic():
    """
    Filter tests for only the fully automated tests to run. Tests that require user intervention
    or validation by the user are skipped.
    """
    global run_only_interactive, run_requires_user_action, run_requires_user_validation
    global interactive, allow_missing_screenshots

    run_only_interactive = False
    run_requires_user_action = False
    run_requires_user_validation = False
    interactive = False
    allow_missing_screenshots = False


class InteractiveTestCase(unittest.TestCase):
    """
    Base class for interactive tests.

    Interactive tests exist on several levels of interactivity. The least interactive tests store
    screenshots of user validated output that can be used to automatically compare to in a non
    interactive run. More interactive tests cannot validate the results automatically, but can
    run fully automatic for sanity checks. Finally there are tests that really require the user
    to perform an action for the test to continue.

    Use the decorators @only_interactive, @requires_user_validation and @requires_user_action to
    mark a test case as such. This only works on the test suite (class) level.
    """

    def __init__(self, methodName):
        super(InteractiveTestCase, self).__init__(methodName='_run_test')
        self.__test_method_name = methodName

        self._screenshots = []

    def _run_test(self):
        """
        Internal main body of the test. Kicks off the test to run either interactive or not.
        """
        self._filter_test()

        test_method = getattr(self, self.__test_method_name, None)
        if not test_method:
            self.fail('Unknown test method: {}'.format(self.__test_method_name))
        if interactive:
            self._show_test_header(test_method)
        test_method()

        # If we arrive here, there have not been any failures yet
        if interactive:
            self._commit_screenshots()
        else:
            if self._has_reference_screenshots():
                self._validate_screenshots()
                # Always commit the screenshots here. They can be used for the next test run.
                # If reference screenshots were already present and there was a mismatch, it should
                # have failed above.
                self._commit_screenshots()

            elif allow_missing_screenshots:
                warnings.warn('No committed reference screenshots available. Ignoring.')
            else:
                self.fail('No committed reference screenshots available. Run interactive first.')

    def _filter_test(self):
        """
        Check the filters to see whether this test needs to run.
        """
        only_interactive = getattr(self, 'test_only_interactive', False)
        requires_user_action = getattr(self, 'test_requires_user_action', False)
        requires_user_validation = getattr(self, 'test_requires_user_validation', False)

        if only_interactive and not run_only_interactive:
            self.skipTest('Test requires to be run interactively.')
        if requires_user_action and not run_requires_user_action:
            self.skipTest('Tests requiring user action are excluded.')
        if requires_user_validation and not run_requires_user_validation:
            self.skipTest('Tests requiring user validation are excluded.')

    def user_verify(self, description, take_screenshot=True):
        """
        Request the user to verify the current display is correct.
        """
        failed = False
        failure_description = None

        if interactive:
            failure_description = _ask_user_to_verify(description)
        if take_screenshot:
            self._take_screenshot()

        if failure_description is not None:
            self.fail(failure_description)

    def assert_image_equal(self, a, b, tolerance=0, msg=None):
        if a is None:
            self.assertIsNone(b, msg)
        else:
            self.assertIsNotNone(b, msg)

        a_data = a.image_data
        b_data = b.image_data

        self.assertEqual(a_data.width, b_data.width, msg)
        self.assertEqual(a_data.height, b_data.height, msg)
        self.assertEqual(a_data.format, b_data.format, msg)
        self.assertEqual(a_data.pitch, b_data.pitch, msg)
        self.assert_buffer_equal(a_data.data, b_data.data, tolerance, msg)

    def assert_buffer_equal(self, a, b, tolerance=0, msg=None):
        if tolerance == 0:
            self.assertEqual(a, b, msg)

        self.assertEqual(len(a), len(b), msg)

        a = array.array('B', a)
        b = array.array('B', b)
        for (aa, bb) in zip(a, b):
            self.assertTrue(abs(aa - bb) <= tolerance, msg)

    def get_test_data_file(self, *file_parts):
        """
        Get a file from the test data directory in an OS independent way. Supply relative file
        name as you would in os.path.join().
        """
        return os.path.join(test_data_path, *file_parts)

    def _take_screenshot(self):
        """
        Take a screenshot to allow visual verification.
        """
        screenshot_name = self._get_next_screenshot_name()
        screenshot_file_name = self._get_screenshot_session_file_name(screenshot_name)

        get_buffer_manager().get_color_buffer().image_data.save(screenshot_file_name)

        self._screenshots.append(screenshot_name)

    def _commit_screenshots(self):
        """
        Store the screenshots for reference if the test case is successful.
        """
        for screenshot_name in self._screenshots:
            shutil.copyfile(self._get_screenshot_session_file_name(screenshot_name),
                            self._get_screenshot_committed_file_name(screenshot_name))

    def _validate_screenshots(self):
        """
        Check the screenshot against regression reference images if available.
        """
        for screenshot_name in self._screenshots:
            committed_image = pyglet.image.load(self._get_screenshot_committed_file_name(screenshot_name))
            session_image = pyglet.image.load(self._get_screenshot_session_file_name(screenshot_name))
            self.assert_image_equal(committed_image, session_image)

    def _has_reference_screenshots(self):
        """
        Check whether there are screenshots from a previous successful run available to validate
        against. Use after taking all required screenshots. Also validates the number of required
        screenshots.
        """
        for screenshot_name in self._screenshots:
            if not os.path.isfile(self._get_screenshot_committed_file_name(screenshot_name)):
                return False
        else:
            return True

    def _get_next_screenshot_name(self):
        """
        Get the unique name for the next screenshot.
        """
        return '{}.{}.{}.{:03d}.png'.format(self.__class__.__module__,
                                        self.__class__.__name__,
                                        self.__test_method_name,
                                        len(self._screenshots)+1)

    def _get_screenshot_session_file_name(self, screenshot_name):
        return os.path.join(session_screenshot_path, screenshot_name)

    def _get_screenshot_committed_file_name(self, screenshot_name):
        return os.path.join(committed_screenshot_path, screenshot_name)

    def _show_test_header(self, test_method):
        print('='*80)
        print('{}.{}'.format(self.__class__.__name__, test_method.__name__))
        if test_method.__doc__:
            print(inspect.getdoc(test_method))
        elif self.__doc__:
            print(inspect.getdoc(self))
        print('-'*80)

if _has_gui:
    def _ask_user_to_verify(description):
        failure_description = None
        success = easygui.ynbox(description)
        if not success:
            failure_description = easygui.enterbox('Enter failure description:')
        return failure_description
else:
    def _ask_user_to_verify(description):
        failure_description = None
        print()
        print(description)
        while True:
            response = raw_input('Passed [Yn]: ')
            if not response:
                break
            elif response in 'Nn':
                failure_description = raw_input('Enter failure description: ')
                break
            elif response in 'Yy':
                break
            else:
                print('Invalid response')
        return failure_description


def only_interactive(cls):
    """
    Mark a test case (class) as only interactive. This means it will be skipped if the user requests
    to run noninteractively.
    """
    cls.test_only_interactive = True
    return cls

def requires_user_action(cls):
    """
    Mark a test case (class) as requiring user action to run. The test cannot be run non interactive
    at all.
    """
    cls.test_requires_user_action = True
    return cls

def requires_user_validation(cls):
    """
    Mark a test case (class) as requiring the user to validate the outcome. It cannot use screenshot
    comparison or other asserts to validate. It is however possible to run non interactively to
    perform a simple sanity check (no exceptions/crashes).
    """
    cls.test_requires_user_validation = True
    return cls
