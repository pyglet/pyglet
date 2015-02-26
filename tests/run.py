"""
Test runner that wraps around unittest.
"""

import argparse
import os
import unittest


def _parse_args():
    parser = argparse.ArgumentParser(description='Pyglet test runner')

    suite_choices = ['unit', 'integration', 'interactive']
    parser.add_argument('suites',
                        metavar='SUITE',
                        nargs='*',
                        choices=suite_choices,
                        help='Test suite to run'
                        )
    parser.add_argument('--non-interactive', '-n',
                        action='store_true',
                        help='Do not use interactive prompts. Skip tests that cannot validate or run without.'
                        )
    parser.add_argument('--sanity', '-s',
                        action='store_true',
                        help='Run a sanity check without interactive prompts. Only skips tests that cannot finish without user intervention.'
                        )

    return parser.parse_args()

def _load_suites(suites):
    loader = unittest.loader.defaultTestLoader
    tests_dir = os.path.dirname(__file__)
    top_dir = os.path.abspath(os.path.join(tests_dir, '..'))

    combined_suite = unittest.TestSuite()
    for suite in suites:
        start_dir = os.path.join(tests_dir, suite)
        loaded_suite = loader.discover(start_dir, top_level_dir=top_dir)
        if loaded_suite:
            combined_suite.addTests(loaded_suite)

    return combined_suite

def _run_suites(test_suite, options):
    if options.non_interactive or options.sanity:
        import tests.interactive.interactive_test_base
        if options.non_interactive:
            tests.interactive.interactive_test_base.set_noninteractive_only_automatic()
        else:
            tests.interactive.interactive_test_base.set_noninteractive_sanity()

    runner = unittest.TextTestRunner()
    runner.run(test_suite)

if __name__ == '__main__':
    options =_parse_args()
    test_suite = _load_suites(options.suites)
    _run_suites(test_suite, options)
