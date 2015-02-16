"""
Test the base class for interactive test cases.
"""

import glob
import mock
import os
import shutil
from tests.interactive.interactive_test_base import InteractiveTestCase, only_interactive
import tempfile
import unittest

from pyglet import window
from pyglet.gl import *

@only_interactive
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
        self._session_screenshot_path = self._patch_directory('tests.interactive.interactive_test_base.session_screenshot_path')
        self._committed_screenshot_path = self._patch_directory('tests.interactive.interactive_test_base.committed_screenshot_path')

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

    @mock.patch('tests.interactive.noninteractive.run_interactive', lambda: False)
    @mock.patch('tests.interactive.interactive_test_base.run_interactive', lambda: False)
    def test_skip_only_interactive(self):
        @only_interactive
        class _Test(InteractiveTestCase):
            test1_ran = False

            def test_1(self):
                _Test.test1_ran = True

        tests = unittest.defaultTestLoader.loadTestsFromTestCase(_Test)
        self.assertIsNotNone(tests)
        self.assertEqual(tests.countTestCases(), 1)

        result = unittest.TestResult()
        tests.run(result)

        self.assertFalse(_Test.test1_ran, 'Test should have been skipped')

    @mock.patch('tests.interactive.noninteractive.run_interactive', lambda: False)
    @mock.patch('tests.interactive.interactive_test_base.run_interactive', lambda: False)
    def test_do_not_skip_normal_interactive(self):
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

    @mock.patch('tests.interactive.noninteractive.run_interactive', lambda: False)
    @mock.patch('tests.interactive.interactive_test_base.run_interactive', lambda: False)
    def test_verify_takes_screenshot(self):
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
        self.assertEqual(len(files), 1)
        self.assertIn('tests.interactive.test_interactive_test_base._Test.test_1.001.png', files[0])

        files = glob.glob(os.path.join(self._committed_screenshot_path, '*.png'))
        self.assertEqual(len(files), 1)
        self.assertIn('tests.interactive.test_interactive_test_base._Test.test_1.001.png', files[0])

