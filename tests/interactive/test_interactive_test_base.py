"""
Test the base class for interactive test cases.
"""

import mock
from tests.interactive.interactive_test_base import InteractiveTestCase, only_interactive
import unittest

@only_interactive
class InteractiveTestCaseTest(InteractiveTestCase):
    """
    Test the interactive test case base. Is an interactive test case itself, to be able to test it
    properly.
    """

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



