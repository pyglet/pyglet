"""
Test the base class for interactive test cases.
"""

import glob
from tests import mock
import os
import pytest
import shutil
from ..base.interactive import InteractiveTestCase
import tempfile
import unittest

import pyglet
from pyglet import window
from pyglet.gl import *


@pytest.mark.requires_user_action
class InteractiveTestCaseTest(InteractiveTestCase):
    """
    Test the interactive test case base. Is an interactive test case itself, to be able to test it
    properly.
    """

    def setUp(self):
        self._patchers = []
        self._temporary_directories = []

    def tearDown(self):
        for patcher in self._patchers:
            patcher.stop()
        for directory in self._temporary_directories:
            shutil.rmtree(directory)

    def _patch_directory(self, target):
        directory = tempfile.mkdtemp()
        self._temporary_directories.append(directory)
        patcher = mock.patch(target, directory)
        self._patchers.append(patcher)
        patcher.start()
        return directory

    def _patch_screenshot_paths(self):
        self._session_screenshot_path = self._patch_directory('tests.base.interactive.session_screenshot_path')
        self._committed_screenshot_path = self._patch_directory('tests.base.interactive.committed_screenshot_path')

    def test_single_method(self):
        class _Test(InteractiveTestCase):
            test1_ran = False

            def test_1(self):
                _Test.test1_ran = True

        tests = unittest.defaultTestLoader.loadTestsFromTestCase(_Test)
        self.assertIsNotNone(tests)
        self.assertEqual(tests.countTestCases(), 1)

        result = unittest.TestResult()
        tests.run(result)

        self.assertTrue(_Test.test1_ran, 'Test should have run')

    def test_multiple_methods(self):
        class _Test(InteractiveTestCase):
            test1_ran = False
            test2_ran = False

            def test_1(self):
                _Test.test1_ran = True

            def test_2(self):
                _Test.test2_ran = True

        tests = unittest.defaultTestLoader.loadTestsFromTestCase(_Test)
        self.assertIsNotNone(tests)
        self.assertEqual(tests.countTestCases(), 2)

        result = unittest.TestResult()
        tests.run(result)

        self.assertTrue(_Test.test1_ran, 'Test 1 should have run')
        self.assertTrue(_Test.test2_ran, 'Test 2 should have run')

    def test_user_verify_passed(self):
        class _Test(InteractiveTestCase):
            test1_ran = False

            def test_1(self):
                _Test.test1_ran = True

                self.user_verify('Just press Enter', take_screenshot=False)

        tests = unittest.defaultTestLoader.loadTestsFromTestCase(_Test)
        self.assertIsNotNone(tests)
        self.assertEqual(tests.countTestCases(), 1)

        result = unittest.TestResult()
        tests.run(result)

        self.assertTrue(_Test.test1_ran, 'Test should have run')
        self.assertEqual(len(result.failures), 0, 'Not expecting failures')
        self.assertEqual(len(result.errors), 0, 'Not expecting errors')
        self.assertEqual(result.testsRun, 1, 'Expected 1 test run')

        self.user_verify('Did I ask you to press Enter?', take_screenshot=False)

    def test_user_verify_failed(self):
        class _Test(InteractiveTestCase):
            test1_ran = False

            def test_1(self):
                _Test.test1_ran = True

                self.user_verify('Enter "n" and then enter reason "abcd"', take_screenshot=False)

        tests = unittest.defaultTestLoader.loadTestsFromTestCase(_Test)
        self.assertIsNotNone(tests)
        self.assertEqual(tests.countTestCases(), 1)

        result = unittest.TestResult()
        tests.run(result)

        self.assertTrue(_Test.test1_ran, 'Test should have run')
        self.assertEqual(len(result.failures), 1, 'Expected 1 test failure')
        self.assertEqual(len(result.errors), 0, 'Not expecting errors')
        self.assertEqual(result.testsRun, 1, 'Expected 1 test run')

        self.assertIn('AssertionError: abcd', result.failures[0][1], 'Did not get failure message entered by user.')

    def test_verify_commits_screenshot_on_user_passed(self):
        class _Test(InteractiveTestCase):
            def test_1(self):
                w = window.Window(200, 200)
                w.switch_to()
                glClearColor(1, 0, 1, 1)
                glClear(GL_COLOR_BUFFER_BIT)
                w.flip()

                self.user_verify('Please choose yes (or press Enter)')
                w.close()

        self._patch_screenshot_paths()

        tests = unittest.defaultTestLoader.loadTestsFromTestCase(_Test)
        self.assertIsNotNone(tests)
        self.assertEqual(tests.countTestCases(), 1)

        result = unittest.TestResult()
        tests.run(result)

        self.assertEqual(len(result.failures), 0, 'Not expecting failures')
        self.assertEqual(len(result.errors), 0, 'Not expecting errors')
        self.assertEqual(result.testsRun, 1, 'Expected 1 test run')

        files = glob.glob(os.path.join(self._session_screenshot_path, '*.png'))
        self.assertEqual(len(files), 1, 'Screenshot not stored in session directory')
        self.assertIn('tests.interactive.test_interactive_test_base._Test.test_1.001.png', files[0])

        files = glob.glob(os.path.join(self._committed_screenshot_path, '*.png'))
        self.assertEqual(len(files), 1, 'Screenshot not committed')
        self.assertIn('tests.interactive.test_interactive_test_base._Test.test_1.001.png', files[0])

    @mock.patch('tests.interactive.interactive_test_base.interactive', False)
    def test_screenshot_taken_but_not_committed_on_noninteractive_failure(self):
        class _Test(InteractiveTestCase):
            def test_1(self):
                w = window.Window(200, 200)
                w.switch_to()
                glClearColor(1, 0, 1, 1)
                glClear(GL_COLOR_BUFFER_BIT)
                w.flip()

                self.user_verify('Empty window')
                w.close()

                self.fail('Test failed')

        self._patch_screenshot_paths()

        tests = unittest.defaultTestLoader.loadTestsFromTestCase(_Test)
        self.assertIsNotNone(tests)
        self.assertEqual(tests.countTestCases(), 1)

        result = unittest.TestResult()
        tests.run(result)

        self.assertEqual(len(result.failures), 1, 'Expecting 1 failure')
        self.assertEqual(len(result.errors), 0, 'Not expecting errors')
        self.assertEqual(result.testsRun, 1, 'Expected 1 test run')

        files = glob.glob(os.path.join(self._session_screenshot_path, '*.png'))
        self.assertEqual(len(files), 1, 'Screenshot not stored in session directory')
        self.assertIn('tests.interactive.test_interactive_test_base._Test.test_1.001.png', files[0])

        files = glob.glob(os.path.join(self._committed_screenshot_path, '*.png'))
        self.assertEqual(len(files), 0, 'Screenshot should not have been comitted')

    @mock.patch('tests.interactive.interactive_test_base.interactive', False)
    @mock.patch('tests.interactive.interactive_test_base.allow_missing_screenshots', True)
    def test_screenshot_taken_but_not_committed_on_noninteractive_pass(self):
        class _Test(InteractiveTestCase):
            def test_1(self):
                w = window.Window(200, 200)
                w.switch_to()
                glClearColor(1, 0, 1, 1)
                glClear(GL_COLOR_BUFFER_BIT)
                w.flip()

                self.user_verify('Empty window')
                w.close()

        self._patch_screenshot_paths()

        tests = unittest.defaultTestLoader.loadTestsFromTestCase(_Test)
        self.assertIsNotNone(tests)
        self.assertEqual(tests.countTestCases(), 1)

        result = unittest.TestResult()
        tests.run(result)

        self.assertEqual(len(result.failures), 0, 'Not expecting failures')
        self.assertEqual(len(result.errors), 0, 'Not expecting errors')
        self.assertEqual(result.testsRun, 1, 'Expected 1 test run')

        files = glob.glob(os.path.join(self._session_screenshot_path, '*.png'))
        self.assertEqual(len(files), 1, 'Screenshot not stored in session directory')
        self.assertIn('tests.interactive.test_interactive_test_base._Test.test_1.001.png', files[0])

        files = glob.glob(os.path.join(self._committed_screenshot_path, '*.png'))
        self.assertEqual(len(files), 0, 'Screenshot should not have been comitted')

    @mock.patch('tests.interactive.interactive_test_base.interactive', False)
    def test_fails_on_missing_screenshot_on_noninteractive_pass(self):
        class _Test(InteractiveTestCase):
            def test_1(self):
                w = window.Window(200, 200)
                w.switch_to()
                glClearColor(1, 0, 1, 1)
                glClear(GL_COLOR_BUFFER_BIT)
                w.flip()

                self.user_verify('Empty window')
                w.close()

        self._patch_screenshot_paths()

        tests = unittest.defaultTestLoader.loadTestsFromTestCase(_Test)
        self.assertIsNotNone(tests)
        self.assertEqual(tests.countTestCases(), 1)

        result = unittest.TestResult()
        tests.run(result)

        self.assertEqual(len(result.failures), 1, 'Expecting 1 failure')
        self.assertEqual(len(result.errors), 0, 'Not expecting errors')
        self.assertEqual(result.testsRun, 1, 'Expected 1 test run')

        files = glob.glob(os.path.join(self._session_screenshot_path, '*.png'))
        self.assertEqual(len(files), 1, 'Screenshot not stored in session directory')
        self.assertIn('tests.interactive.test_interactive_test_base._Test.test_1.001.png', files[0])

        files = glob.glob(os.path.join(self._committed_screenshot_path, '*.png'))
        self.assertEqual(len(files), 0, 'Screenshot should not have been comitted')


    def test_screenshot_taken_but_not_committed_on_user_failure(self):
        class _Test(InteractiveTestCase):
            def test_1(self):
                w = window.Window(200, 200)
                w.switch_to()
                glClearColor(1, 0, 1, 1)
                glClear(GL_COLOR_BUFFER_BIT)
                w.flip()

                try:
                    self.user_verify('Please select "n" and enter any reason')
                finally:
                    w.close()


        self._patch_screenshot_paths()

        tests = unittest.defaultTestLoader.loadTestsFromTestCase(_Test)
        self.assertIsNotNone(tests)
        self.assertEqual(tests.countTestCases(), 1)

        result = unittest.TestResult()
        tests.run(result)

        self.assertEqual(len(result.failures), 1, 'Expecting 1 failure')
        self.assertEqual(len(result.errors), 0, 'Not expecting errors')
        self.assertEqual(result.testsRun, 1, 'Expected 1 test run')

        files = glob.glob(os.path.join(self._session_screenshot_path, '*.png'))
        self.assertEqual(len(files), 1, 'Screenshot not stored in session directory')
        self.assertIn('tests.interactive.test_interactive_test_base._Test.test_1.001.png', files[0])

        files = glob.glob(os.path.join(self._committed_screenshot_path, '*.png'))
        self.assertEqual(len(files), 0, 'Screenshot should not have been committed')

    @mock.patch('tests.interactive.interactive_test_base.interactive', False)
    def test_screenshot_does_not_match(self):
        class _Test(InteractiveTestCase):
            def test_1(self):
                w = window.Window(200, 200)
                w.switch_to()
                glClearColor(0, 0, 1, 1)
                glClear(GL_COLOR_BUFFER_BIT)
                w.flip()

                self.user_verify('Empty window')
                w.close()

        self._patch_screenshot_paths()

        # Copy non matching screenshot
        screenshot_name = 'tests.interactive.test_interactive_test_base._Test.test_1.001.png'
        original_screenshot = os.path.join(os.path.dirname(__file__), '..', 'data', 'images', screenshot_name)
        committed_screenshot = os.path.join(self._committed_screenshot_path, screenshot_name)
        shutil.copy(original_screenshot, committed_screenshot)

        # Start the test
        tests = unittest.defaultTestLoader.loadTestsFromTestCase(_Test)
        self.assertIsNotNone(tests)
        self.assertEqual(tests.countTestCases(), 1)

        result = unittest.TestResult()
        tests.run(result)

        self.assertEqual(len(result.failures), 1, 'Expecting 1 failure')
        self.assertEqual(len(result.errors), 0, 'Not expecting errors')
        self.assertEqual(result.testsRun, 1, 'Expected 1 test run')

        files = glob.glob(os.path.join(self._session_screenshot_path, '*.png'))
        self.assertEqual(len(files), 1, 'Screenshot not stored in session directory')
        self.assertIn('tests.interactive.test_interactive_test_base._Test.test_1.001.png', files[0])

        # Verify committed image not changed
        original_image = pyglet.image.load(original_screenshot)
        committed_image = pyglet.image.load(committed_screenshot)
        self.assert_image_equal(original_image, committed_image, msg='Committed image should not be overwritten')

    @mock.patch('tests.interactive.interactive_test_base.interactive', False)
    def test_screenshot_matches(self):
        class _Test(InteractiveTestCase):
            def test_1(self):
                w = window.Window(200, 200)
                w.switch_to()
                glClearColor(1, 0, 1, 1)
                glClear(GL_COLOR_BUFFER_BIT)
                w.flip()

                self.user_verify('Empty window')
                w.close()

        self._patch_screenshot_paths()

        # Copy matching screenshot
        screenshot_name = 'tests.interactive.test_interactive_test_base._Test.test_1.001.png'
        original_screenshot = os.path.join(os.path.dirname(__file__), '..', 'data', 'images', screenshot_name)
        committed_screenshot = os.path.join(self._committed_screenshot_path, screenshot_name)
        shutil.copy(original_screenshot, committed_screenshot)

        # Start the test
        tests = unittest.defaultTestLoader.loadTestsFromTestCase(_Test)
        self.assertIsNotNone(tests)
        self.assertEqual(tests.countTestCases(), 1)

        result = unittest.TestResult()
        tests.run(result)

        self.assertEqual(len(result.failures), 0, 'Not expecting failures')
        self.assertEqual(len(result.errors), 0, 'Not expecting errors')
        self.assertEqual(result.testsRun, 1, 'Expected 1 test run')

        files = glob.glob(os.path.join(self._session_screenshot_path, '*.png'))
        self.assertEqual(len(files), 1, 'Screenshot not stored in session directory')
        self.assertIn('tests.interactive.test_interactive_test_base._Test.test_1.001.png', files[0])


