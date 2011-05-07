#!/usr/bin/env python

'''Test framework for pyglet.  Reads details of components and capabilities
from a requirements document, runs the appropriate unit tests.

Overview
--------

First, some definitions:

Test case:
    A single test, implemented by a Python module in the tests/ directory.
    Tests can be interactive (requiring the user to pass or fail them) or
    non-interactive (the test passes or fails itself).

Section:
    A list of test cases to be run in a specified order.  Sections can
    also contain other sections to an arbitrary level.

Capability:
    A capability is a tag that can be applied to a test-case, which specifies
    a particular instance of the test.  The tester can select which
    capabilities are present on their system; and only test cases matching
    those capabilities will be run.  
    
    There are platform capabilities "WIN", "OSX" and "X11", which are
    automatically selected by default.  
    
    The "DEVELOPER" capability is used to mark test cases which test a feature
    under active development.  
    
    The "GENERIC" capability signifies that the test case is equivalent under
    all platforms, and is selected by default.

    Other capabilities can be specified and selected as needed.  For example,
    we may wish to use an "NVIDIA" or "ATI" capability to specialise a
    test-case for a particular video card make.

Some tests generate regression images if enabled, so you will only
need to run through the interactive procedure once.  During
subsequent runs the image shown on screen will be compared with the
regression images and passed automatically if they match.  There are
command line options for enabling this feature.

By default regression images are saved in tests/regression/images/

Running tests
-------------

The test procedure is interactive (this is necessary to facilitate the
many GUI-related tests, which cannot be completely automated).  With no
command-line arguments, all test cases in all sections will be run::

    python tests/test.py

Before each test, a description of the test will be printed, including
some information of what you should look for, and what interactivity
is provided (including how to stop the test).  Press ENTER to begin
the test.

When the test is complete, assuming there were no detectable errors
(for example, failed assertions or an exception), you will be asked
to enter a [P]ass or [F]ail.  You should Fail the test if the behaviour
was not as described, and enter a short reason.

Details of each test session are logged for future use.

Command-line options:

--plan=
    Specify the test plan file (defaults to tests/plan.txt)
--test-root=
    Specify the top-level directory to look for unit tests in (defaults
    to test/)
--capabilities=
    Specify the capabilities to select, comma separated.  By default this
    only includes your operating system capability (X11, WIN or OSX) and
    GENERIC.
--log-level=
    Specify the minimum log level to write (defaults to 10: info)
--log-file=
    Specify log file to write to (defaults to "pyglet.%d.log")
--regression-capture
    Save regression images to disk.  Use this only if the tests have
    already been shown to pass.
--regression-check
    Look for a regression image on disk instead of prompting the user for
    passage.  If a regression image is found, it is compared with the test
    case using the tolerance specified below.  Recommended only for
    developers.
--regression-tolerance=
    Specify the tolerance when comparing a regression image.  A value of
    2, for example, means each sample component must be +/- 2 units
    of the regression image.  Tolerance of 0 means images must be identical,
    tolerance of 256 means images will always match (if correct dimensions).
    Defaults to 2.
--regression-path=
    Specify the directory to store and look for regression images.
    Defaults to tests/regression/images/
--developer
    Selects the DEVELOPER capability.
--no-interactive=
    Don't write descriptions or prompt for confirmation; just run each
    test in succcession.

After the command line options, you can specify a list of sections or test
cases to run.

Examples
--------

    python tests/test.py --capabilities=GENERIC,NVIDIA,WIN window

Runs all tests in the window section with the given capabilities.

    python tests/test.py --no-interactive FULLSCREEN_TOGGLE

Test just the FULLSCREEN_TOGGLE test case without prompting for input (useful
for development).

    python tests/image/PIL_RGBA_SAVE.py

Run a single test outside of the test harness.  Handy for development; it
is equivalent to specifying --no-interactive.

Writing tests
-------------

Add the test case to the appropriate section in the test plan (plan.txt).
Create one unit test script per test case.  For example, the test for
window.FULLSCREEN_TOGGLE is located at::

    tests/window/FULLSCREEN_TOGGLE.py

The test file must contain:

- A module docstring describing what the test does and what the user should
  look for.
- One or more subclasses of unittest.TestCase.
- No other module-level code, except perhaps an if __name__ == '__main__'
  condition for running tests stand-alone.
- Optionally, the attribute "__noninteractive = True" to specify that
  the test is not interactive; doesn't require user intervention.

During development, test cases should be marked with DEVELOPER.  Once finished
add the WIN, OSX and X11 capabilities, or GENERIC if it's platform
independent.

Writing regression tests
------------------------

Your test case should subclass tests.regression.ImageRegressionTestCase
instead of unitttest.TestCase.  At the point where the buffer (window
image) should be checked/saved, call self.capture_regression_image().
If this method returns True, you can exit straight away (regression
test passed), otherwise continue running interactively (regression image
was captured, wait for user confirmation).  You can call
capture_regression_image() several times; only the final image will be
used.

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import array
import logging
import os
import optparse
import re
import sys
import time
import unittest

# So we can find tests.regression and ensure local pyglet copy is tested.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import tests.regression
import pyglet.image

regressions_path = os.path.join(os.path.dirname(__file__), 
                                'regression', 'images')

class TestCase(object):
    def __init__(self, name):
        self.name = name
        self.short_name = name.split('.')[-1]
        self.capabilities = set()

    def get_module_filename(self, root=''):
        path = os.path.join(*self.name.split('.'))
        return '%s.py' % os.path.join(root, path)

    def get_module(self, root=''):
        name = 'tests.%s' % self.name
        module = __import__(name)
        for c in name.split('.')[1:]:
            module = getattr(module, c)
        return module

    def get_regression_image_filename(self):
        return os.path.join(regressions_path, '%s.png' % self.name)

    def test(self, options):
        if not options.capabilities.intersection(self.capabilities):
            return

        options.log.info('Testing %s.', self)
        if options.pretend:
            return

        module = None
        try:
            module = self.get_module(options.test_root)
        except IOError:
            options.log.warning('No test exists for %s', self)
        except Exception:
            options.log.exception('Cannot load test for %s', self)
        if not module:
            return

        module_interactive = options.interactive
        if hasattr(module, '__noninteractive') and \
           getattr(module, '__noninteractive'):
            module_interactive = False

        if options.regression_check and \
           os.path.exists(self.get_regression_image_filename()):
            result = RegressionCheckTestResult(
                self, options.regression_tolerance)
            module_interactive = False
        elif options.regression_capture:
            result = RegressionCaptureTestResult(self)
        else:
            result = StandardTestResult(self)

        print ("Running Test: %s" % self)
        if module.__doc__:
            print module.__doc__
        print '-' * 78
        if module_interactive:
            raw_input('Press return to begin test...')


        suite = unittest.TestLoader().loadTestsFromModule(module)

        options.log.info('Begin unit tests for %s', self)
        suite(result)
        for failure in result.failures:
            options.log.error('Failure in %s', self)
            options.log.error(failure[1])
        for error in result.errors:
            options.log.error('Error in %s', self)
            options.log.error(error[1])
        options.log.info('%d tests run', result.testsRun)

        if (module_interactive and 
            len(result.failures) == 0 and 
            len(result.errors) == 0):
            print module.__doc__
            user_result = raw_input('[P]assed test, [F]ailed test: ')
            if user_result and user_result[0] in ('F', 'f'):
                print 'Enter failure description: '
                description = raw_input('> ')
                options.log.error('User marked fail for %s', self)
                options.log.error(description)
            else:
                options.log.info('User marked pass for %s', self)
                result.setUserPass()

    def __repr__(self):
        return 'TestCase(%s)' % self.name

    def __str__(self):
        return self.name

    def __cmp__(self, other):
        return cmp(str(self), str(other))

class TestSection(object):
    def __init__(self, name):
        self.name = name
        self.children = []

    def add(self, child):
        # child can be TestSection or TestCase
        self.children.append(child)

    def test(self, options):
        for child in self.children:
            child.test(options)
        
    def __repr__(self):
        return 'TestSection(%s)' % self.name

class TestPlan(TestSection):
    def __init__(self):
        self.root = None
        self.names = {}

    @classmethod
    def from_file(cls, file):
        plan = TestPlan()
        plan.root = TestSection('{root}')
        plan.root.indent = None

        # Section stack
        sections = [plan.root]

        if not hasattr(file, 'read'):
            file = open(file, 'r')
        line_number = 0
        for line in file:
            line_number += 1
            # Skip empty lines
            if not line.strip():
                continue

            # Skip comments
            if line[0] == '#':
                continue

            indent = len(line) - len(line.lstrip())
            while (sections and sections[-1].indent and
                   sections[-1].indent > indent):
                sections.pop()

            if sections[-1].indent is None:
                sections[-1].indent = indent

            if sections[-1].indent != indent:
                raise Exception('Indentation mismatch line %d' % line_number)
            
            if '.' in line:
                tokens = line.strip().split()
                test_case = TestCase(tokens[0])
                test_case.capabilities = set(tokens[1:])
                sections[-1].add(test_case)
                plan.names[test_case.name] = test_case
                plan.names[test_case.short_name] = test_case
            else:
                section = TestSection(line.strip())
                section.indent = None
                sections[-1].add(section)
                sections.append(section)
                plan.names[section.name] = section

        return plan
        
class StandardTestResult(unittest.TestResult):
    def __init__(self, component):
        super(StandardTestResult, self).__init__()

    def setUserPass(self):
        pass

class RegressionCaptureTestResult(unittest.TestResult):
    def __init__(self, component):
        super(RegressionCaptureTestResult, self).__init__()
        self.component = component
        self.captured_image = None

    def startTest(self, test):
        super(RegressionCaptureTestResult, self).startTest(test)
        if isinstance(test, tests.regression.ImageRegressionTestCase):
            test._enable_regression_image = True

    def addSuccess(self, test):
        super(RegressionCaptureTestResult, self).addSuccess(test)
        assert self.captured_image is None
        if isinstance(test, tests.regression.ImageRegressionTestCase):
            self.captured_image = test._captured_image

    def setUserPass(self):
        if self.captured_image:
            filename = self.component.get_regression_image_filename()
            self.captured_image.save(filename)
            logging.getLogger().info('Wrote regression image %s' % filename)

class Regression(Exception):
    pass

def buffer_equal(a, b, tolerance=0):
    if tolerance == 0:
        return a == b

    if len(a) != len(b):
        return False

    a = array.array('B', a)
    b = array.array('B', b)
    for i in range(len(a)):
        if abs(a[i] - b[i]) > tolerance:
            return False
    return True

class RegressionCheckTestResult(unittest.TestResult):
    def __init__(self, component, tolerance):
        super(RegressionCheckTestResult, self).__init__()
        self.filename = component.get_regression_image_filename()
        self.regression_image = pyglet.image.load(self.filename)
        self.tolerance = tolerance

    def startTest(self, test):
        super(RegressionCheckTestResult, self).startTest(test)
        if isinstance(test, tests.regression.ImageRegressionTestCase):
            test._enable_regression_image = True
            test._enable_interactive = False
            logging.getLogger().info('Using regression %s' % self.filename)

    def addSuccess(self, test):
        # Check image
        ref_image = self.regression_image.image_data
        this_image = test._captured_image.image_data
        this_image.format = ref_image.format
        this_image.pitch = ref_image.pitch

        if this_image.width != ref_image.width:
            self.addFailure(test, 
                'Buffer width does not match regression image')
        elif this_image.height != ref_image.height:
            self.addFailure(test, 
                'Buffer height does not match regression image')
        elif not buffer_equal(this_image.data, ref_image.data,
                              self.tolerance):
            self.addFailure(test,
                'Buffer does not match regression image')
        else:
            super(RegressionCheckTestResult, self).addSuccess(test)

    def addFailure(self, test, err):
        err = Regression(err)
        super(RegressionCheckTestResult, self).addFailure(test, (Regression,
            err, []))


def main():
    capabilities = ['GENERIC']
    platform_capabilities = {
        'linux2': 'X11',
        'win32': 'WIN',
        'cygwin': 'WIN',
        'darwin': 'OSX'
    }
    if sys.platform in platform_capabilities:
        capabilities.append(platform_capabilities[sys.platform])

    script_root = os.path.dirname(__file__)
    plan_filename = os.path.normpath(os.path.join(script_root, 'plan.txt'))
    test_root = script_root
 
    op = optparse.OptionParser()
    op.usage = 'test.py [options] [components]'
    op.add_option('--plan', help='test plan file', default=plan_filename)
    op.add_option('--test-root', default=script_root,
        help='directory containing test cases')
    op.add_option('--capabilities', help='selected test capabilities',
        default=','.join(capabilities))
    op.add_option('--log-level', help='verbosity of logging',
        default=10, type='int')
    op.add_option('--log-file', help='log to FILE', metavar='FILE', 
        default='pyglet.%d.log')
    op.add_option('--regression-path', metavar='DIR', default=regressions_path,
        help='locate regression images in DIR')
    op.add_option('--regression-tolerance', type='int', default=2,
        help='tolerance for comparing regression images')
    op.add_option('--regression-check', action='store_true',
        help='enable image regression checks')
    op.add_option('--regression-capture', action='store_true',
        help='enable image regression capture')
    op.add_option('--no-interactive', action='store_false', default=True,
        dest='interactive', help='disable interactive prompting')
    op.add_option('--developer', action='store_true',
        help='add DEVELOPER capability')
    op.add_option('--pretend', action='store_true',
        help='print selected test cases only')

    options, args = op.parse_args()

    options.capabilities = set(options.capabilities.split(','))
    if options.developer:
        options.capabilities.add('DEVELOPER')

    if options.regression_capture:
        try:
            os.makedirs(regressions_path)
        except OSError:
            pass

    if '%d' in options.log_file: 
        i = 1
        while os.path.exists(options.log_file % i):
            i += 1
        options.log_file = options.log_file % i

    logging.basicConfig(filename=options.log_file, level=options.log_level)
    options.log = logging.getLogger()

    options.log.info('Beginning test at %s', time.ctime())
    options.log.info('Capabilities are: %s', ', '.join(options.capabilities))
    options.log.info('sys.platform = %s', sys.platform)
    options.log.info('Reading test plan from %s', options.plan)
    plan = TestPlan.from_file(options.plan)

    errors = False
    if args:
        components = []
        for arg in args:
            try:
                component = plan.names[arg]
                components.append(component)
            except KeyError:
                options.log.error('Unknown test case or section "%s"', arg)
                errors = True
    else:
        components = [plan.root]

    if not errors:
        print '-' * 78
        for component in components:
            component.test(options)
        print '-' * 78

if __name__ == '__main__':
    main()


