"""
For documentation please see doc/internal/testing.txt
"""
from __future__ import print_function
import argparse
import imp
import os
import pyglet
import sys
from tests.annotations import Platform
import unittest

try:
    from coverage import coverage
    _cov = None
except:
    coverage = None

def _parse_args():
    parser = argparse.ArgumentParser(description='Pyglet test runner',
                                     formatter_class=argparse.RawTextHelpFormatter)

    suite_choices = ['unit', 'integration', 'interactive', 'sanity', 'automatic']
    suite_help = """Test suite(s) to run. Has the following options:
- unit:        Run the unit tests.
- integration: Run the integration tests.
- interactive: Run the interactive tests.
- sanity:      Run all tests. For the interactive tests do not use interactive prompts and try to
               run as many tests as possible. (Same as: unit integration interactve --sanity).
- automatic:   Run all tests. For the interactive tests skip the tests that cannot validate without
               user interaction. (Same as: unit integration interactive --non-interactive)."""
    coverage_help = 'Determine test coverage and create an HTML report for it.'
    if coverage is None:
        coverage_help += '\nTo use, install coverage (pip install coverage)'
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
    parser.add_argument('--coverage', '-c',
                        action='store_true',
                        help=coverage_help
                        )
    parser.add_argument('--verbose', '-v',
                        action='store_const',
                        const=2,
                        default=1,
                        help='Enable unittest verbose output.'
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

    runner = unittest.TextTestRunner(verbosity=options.verbose)
    runner.run(test_suite)

def _start_coverage(options):
    if coverage is not None and options.coverage:
        global _cov
        _cov = coverage(branch=True,
                        source=['pyglet'],
                        omit=_get_platform_omit())
        _cov.exclude('if _debug:')
        _cov.exclude('@abstractmethod')
        _cov.exclude('pass')
        _cov.start()

        # Need to reload pyglet to get full coverage, because it was imported before coverage was
        # started
        imp.reload(pyglet)

def _stop_coverage(options):
    if coverage is not None and options.coverage:
        global _cov
        _cov.stop()
        _cov.html_report(directory='coverage_report')
        html_report = os.path.abspath(os.path.join('coverage_report', 'index.html'))
        print('Coverage report: file://' + html_report)

def _get_platform_omit():
    omit = ['pyglet/extlibs/*']

    windows_specific = ['*win32*', '*wgl*', '*gdiplus*', '*wintab*', '*directsound*']
    linux_specific = ['*xlib*', '*freetype*', '*glx*', '*gdkpixbuf2*', '*x11*', '*pulse*']
    osx_specific = ['*agl*', '*darwin*']
    osx_cocoa_specific = ['*cocoa*', '*quartz*']

    if pyglet.compat_platform not in Platform.LINUX:
        omit.extend(linux_specific)
    if pyglet.compat_platform not in Platform.WINDOWS:
        omit.extend(windows_specific)
    if pyglet.compat_platform not in Platform.OSX:
        omit.extend(osx_specific)
        omit.extend(osx_cocoa_specific)

    return omit

if __name__ == '__main__':
    import pytest
    sys.exit(pytest.main())
