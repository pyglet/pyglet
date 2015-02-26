"""
Test runner that wraps around unittest.
"""

import argparse
import os
import sys
import unittest


def _parse_args():
    parser = argparse.ArgumentParser(description='Pyglet test runner',
                                     formatter_class=argparse.RawTextHelpFormatter)

    suite_choices = ['unit', 'integration', 'interactive', 'sanity', 'automatic']
    suite_help = """Test suite(s) to run. Has the following options:
- unit:        Run the unit tests
- integration: Run the integration tests
- interactive: Run the interactive tests
- sanity:      Run all tests. For the interactive tests do not use interactive prompts and try to
               run as many tests as possible
- automatic:   Run all tests. For the interactive tests skip the tests that cannot validate without
               user interaction."""
    parser.add_argument('suites',
                        metavar='SUITE',
                        nargs='*',
                        choices=suite_choices,
                        help=suite_help
                        )
    parser.add_argument('--non-interactive', '-n',
                        action='store_true',
                        help='[Interactive tests only] Do not use interactive prompts. Skip tests that cannot validate or run without.'
                        )
    parser.add_argument('--sanity', '-s',
                        action='store_true',
                        help='[Interactive tests only] Do not use interactive prompts. Only skips tests that cannot finish without user intervention.'
                        )

    options = parser.parse_args()

    if 'sanity' in options.suites:
        if len(options.suites) > 1:
            print('sanity suite cannot be combined with other suites')
            sys.exit(-1)
        options.suites = ['unit', 'integration', 'interactive']
        options.non_interactive = False
        options.sanity = True
    elif 'automatic' in options.suites:
        if len(options.suites) > 1:
            print('automatic suite cannot be combined with other suites')
            sys.exit(-1)
        options.suites = ['unit', 'integration', 'interactive']
        options.non_interactive = True
        options.sanity = False

    return options

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
