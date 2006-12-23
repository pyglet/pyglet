#!/usr/bin/env python

'''Test framework for pyglet.  Reads details of components and capabilities
from a requirements document, runs the appropriate unit tests.

Overview
--------

First, some definitions:

Component:
    A component is a single feature that can be tested more or less
    in isolation.  In a requirements document, this appears as a row
    in the implementation table, and by convention is named with
    UPPERCASE_AND_UNDERSCORES.  A component corresponds to a single
    unit test, located in tests/section/subsection/COMPONENT.py

Capability:
    A capability is a special case of a component which has a separate
    implementation and/or environment.  For example, the window
    components have OS-specific capabilities: WIN, X11 and OSX.   An
    implementation of, for example, FULLSCREEN_TOGGLE, will depend
    very much on this capability, so it makes sense to track the
    progress of the implementation separately.  Capabilities are
    represented in the requirements document as the columns in the
    implementation table.  Arbitrary capabilities can be defined,
    for example, our graphics functions may need separate NVIDIA
    and ATI capabilities.

Section:
    A section groups together related components.  It has a description
    and an implementation table, which lists components and the
    current progress with respect to the capabilities.  Sections
    can also contain subsections, which are separated by periods, for
    example: image.codecs.gdk is a (hypothetical) section.

The requirements document (doc/requirements.txt) is written in
reStructured text and contains all the sections, components and
capabilities for the project.  The intent here is to integrate
our writings on "what needs to be done" with "what has been done"
and "what works at the moment".

A finished component is marked against the appropriate capabilities
with an "X"; partial or incomplete implementations with either a "/"
or empty table cell.  This test script will not attempt to run
unit tests for unfinished implementations.

Some tests generate regression images, so you will only need to run
through the interactive procedure once.  During subsequent runs the
image shown on screen will be compared with the regression images
and passed automatically if they match.  There are command line 
options for disabling this feature.

By default regression images are saved in tests/regression/images/

Running tests
-------------

The test procedure is interactive (this is necessary to facilitate the
many GUI-related tests, which cannot be completely automated).  With no
command-line arguments, all tests for all components in all sections
will be run::

    python tests/test.py

Before each test, a description of the test will be printed, including
some information of what you should look for, and what interactivity
is provided (including how to stop the test).  Press ENTER to begin
the test.

When the test is complete, assuming there were no detectable errors
(for example, failed assertions or an exception), you will be asked
to enter a [P]ass or [F]ail.  You should Fail the test if the behaviour
was not as described, and enter a short reason.

Details of each test session are logged for future use. [TODO: set up
default log files].

Command-line options:

--requirements=
    Specify the requirements file (defaults to doc/requirements.txt)
--test-root=
    Specify the top-level directory to look for unit tests in (defaults
    to test/)
--capabilities=
    Specify the capabilities to test, comma separated.  By default this
    only includes your operating system capability (X11, WIN or OSX).  If
    you specify an empty set of capabilties, the capabilities check
    will be ignored, and all tests are run.
--log-level=
    Specify the minimum log level to write (defaults to 10: info)
--log-file=
    Specify log file to write to (defaults to stderr [TODO])
--no-regression-capture
    Don't save regression images to disk.
--no-regression-check
    Don't look for a regression image on disk; assume none exists (good
    for rebuilding out of date regression images).
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
    Run tests with capability progress marked 'D' (developer-only).  Enable
    this only if you are the developer of the feature; otherwise expect
    it to fail.
--no-interactive=
    Don't write descriptions or prompt for confirmation; just run each
    test in succcession.

After the command line options, you can specify the all or part or a regular
expression of any components or sections you wish to test.  If none are
specified, all tests are run.

Examples
--------

    python tests/test.py --capabilities=GENERIC,NVIDIA,WIN window

Runs all tests in the window section with the given capabilities.

    python tests/test.py --no-interactive window.FULLSCREEN_TOGGLE

Test just the FULLSCREEN_TOGGLE component in the window section,
without prompting for input (useful for development).

Currently the image and text tests use regression images::

    python tests/test.py --no-regression-check image

Rebuild all of the regression images for the image section tests.

    python tests/test.py --no-regression-capture image

Run the image section tests, but don't overwrite the regression images (they
will still be checked, if possible though).

    python tests/image/PIL_RGBA_SAVE.py

Run a single test outside of the test harness.  Handy for development; it
is equivalent to specifying --no-interactive --no-regression-check
--no-regression-capture options.

Writing tests
-------------

Add the capability to the appropriate implementation table in the requirements
document (see requirements.txt for formatting).   Create one unit test
script per capability, located in the directory corresponding to the
section.  For example, the test for window.FULLSCREEN_TOGGLE is
located at::

    tests/window/FULLSCREEN_TOGGLE.py

The test file must contain:

- A module docstring describing what the test does and what the user should
  look for.
- One or more subclasses of unittest.TestCase.
- No other module-level code, except perhaps an if __name__ == '__main__'
  condition for running tests stand-alone.
- Optionally, the attribute "__noninteractive = True" to specify that
  the test is not interactive; doesn't require user intervention.

Mark off capabilities as implemented earlier rather than later, so that
the tests get run by default (even if they are failing).

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

Open questions
--------------

- Can/should this be integrated into an issue tracker?
- What should be done with test logs?
- Wouldn't an ncurses interface for this be cool?

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import array
import docutils.nodes
import docutils.parsers.rst
import getopt
import imp
import logging
import os
import re
import sys
import time
import unittest

import tests.regression
import pyglet.image

regressions_path = os.path.join(os.path.dirname(__file__), 
                                'regression', 'images')

class RequirementsComponent(object):
    FULL = 50
    DEVELOPER = 40
    PARTIAL = 25
    NONE = 0
    UNKNOWN = -1

    def __init__(self, section, name):
        self.section = section
        self.name = name
        self.progress = {}

    def set_progress(self, capability, progress):
        self.progress[capability] = progress

    def get_absname(self):
        return '%s.%s' % (self.section.get_absname(), self.name)

    def get_progress(self, capabilities):
        '''Return the progress of this component for a given set of
           capabilities.  If no capabilities match, we assume that
           they are unspecified, and return the best progress
           for any capability.'''
        for capability in capabilities:
            if capability in self.progress:
                return self.progress[capability]
        # None match, so return highest.
        return max(self.progress.values())

    def is_implemented(self, capabilities):
        if 'DEVELOPER' in capabilities:
            return self.get_progress(capabilities) >= self.DEVELOPER
        else:
            return self.get_progress(capabilities) >= self.FULL

    def get_module_filename(self, root=''):
        path = os.path.join(*self.get_absname().split('.'))
        return '%s.py' % os.path.join(root, path)

    def get_module(self, root=''):
        name = 'tests.%s' % self.get_absname()
        module = __import__(name)
        for c in name.split('.')[1:]:
            module = getattr(module, c)
        return module

    def get_regression_image_filename(self):
        return os.path.join(regressions_path, '%s.png' % self.get_absname())

    def __repr__(self):
        return 'RequirementsComponent(%s)' % self.get_absname()

    def __str__(self):
        return self.get_absname()

    def __cmp__(self, other):
        return cmp(str(self), str(other))

class RequirementsSection(object):
    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        self.description = ''
        self.sections = {}
        self.components = {}
        self.all_components = []
        self.all_sections = []

    def add_section(self, section):
        self.sections[section.name] = section

    def get_section(self, name):
        if '.' in name:
            root, path = name.split('.', 1)
            section = self.sections.get(root, None)
            if section:
                return section.get_section(path)
        else:
            return self.sections.get(name, None)

    def add_component(self, component):
        assert component.section is self
        self.components[component.name] = component

    def get_component(self, name):
        section, component = name.rsplit('.', 1)
        section = self.get_section(section)
        if section:
            return section.components.get(component, None)

    def get_all_components(self):
        if not self.all_components:
            self.all_components = self.components.values()
            for section in self.sections.values():
                self.all_components += section.get_all_components()
        return self.all_components

    def get_all_sections(self): 
        if not self.all_sections:
            self.all_sections = self.sections.values()
            for section in self.sections.values():
                self.all_sections += section.get_all_sections()
        return self.all_sections

    def search(self, query):
        pattern = re.compile(query, re.I)
        results = []
        for component in self.get_all_components():
            if pattern.search(component.get_absname()):
                results.append(component)

        for section in self.get_all_sections():
            if pattern.search(section.get_absname()):
                results += section.get_all_components()

        return results
    
    def get_absname(self):
        names = []
        me = self
        while me and me.name:
            names.insert(0, me.name)
            me = me.parent
        return '.'.join(names)
        
    def __repr__(self):
        return 'RequirementsSection(%s)' % self.get_absname()

class Requirements(RequirementsSection):
    def __init__(self):
        super(Requirements, self).__init__(None, '')

    @classmethod
    def from_rst(cls, rst):
        requirements = Requirements()
        parser = docutils.parsers.rst.Parser()
        document = docutils.utils.new_document('requirements')
        document.settings.tab_width = 4
        document.settings.report_level = 1
        document.settings.pep_references = 1
        document.settings.rfc_references = 1
        parser.parse(rst, document)
        document.walkabout(RequirementsParser(document, requirements))
        return requirements


class RequirementsParser(docutils.nodes.GenericNodeVisitor):
    def __init__(self, document, requirements):
        docutils.nodes.GenericNodeVisitor.__init__(self, document)

        self.requirements = requirements
        self.section_stack = [requirements]
        self.field_key = None

    def get_section(self):
        return self.section_stack[-1]

    def default_visit(self, node):
        pass

    def default_departure(self, node):
        pass

    def visit_term(self, node):
        section = RequirementsSection(self.get_section(), node.astext())
        self.get_section().add_section(section)
        self.section_stack.append(section)

    def depart_definition_list_item(self, node):
        self.section_stack.pop()

    def visit_field_name(self, node):
        self.field_key = node.astext()

    def visit_field_body(self, node):
        if self.field_key == 'description':
            self.get_section().description = node.astext()
        elif self.field_key == 'implementation':
            parser = ImplementationParser(self.document, self.get_section())
            node.walkabout(parser)

class ImplementationParser(docutils.nodes.GenericNodeVisitor):
    progress_lookup = {
        'X': RequirementsComponent.FULL,
        'D': RequirementsComponent.DEVELOPER,
        '/': RequirementsComponent.PARTIAL,
        '': RequirementsComponent.NONE,
    }

    def __init__(self, document, section):
        docutils.nodes.GenericNodeVisitor.__init__(
            self, document)
        self.section = section
        self.capabilities = []

    def default_visit(self, node):
        pass

    def default_departure(self, node):
        pass

    def visit_row(self, node):
        entries = [n.astext() for n in node.children]
        if node.parent.tagname == 'thead':
            # Head row; remember names of capabilities for this table.
            self.capabilities = entries[1:]
        else:
            component = RequirementsComponent(self.section, entries[0])
            self.section.add_component(component)
            for capability, progress in zip(self.capabilities, entries[1:]):
                progress = self.progress_lookup.get(progress.strip(),    
                               RequirementsComponent.UNKNOWN)
                component.set_progress(capability, progress)

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
        self.regression_image = pyglet.image.Image.load(self.filename)
        self.tolerance = tolerance

    def startTest(self, test):
        super(RegressionCheckTestResult, self).startTest(test)
        if isinstance(test, tests.regression.ImageRegressionTestCase):
            test._enable_regression_image = True
            test._enable_interactive = False
            logging.getLogger().info('Using regression %s' % self.filename)

    def addSuccess(self, test):
        # Check image
        ref_image = self.regression_image.get_raw_image()
        this_image = test._captured_image.get_raw_image()
        this_image.set_format(ref_image.format)
        if this_image.top_to_bottom != ref_image.top_to_bottom:
            this_image.swap_rows()

        if this_image.width != ref_image.width:
            self.addFailure(test, 
                'Buffer width does not match regression image')
        elif this_image.height != ref_image.height:
            self.addFailure(test, 
                'Buffer height does not match regression image')
        elif not buffer_equal(this_image.tostring(), ref_image.tostring(),
                              self.tolerance):
            self.addFailure(test,
                'Buffer does not match regression image')
        else:
            super(RegressionCheckTestResult, self).addSuccess(test)

    def addFailure(self, test, err):
        err = Regression(err)
        super(RegressionCheckTestResult, self).addFailure(test, (Regression,
            err, []))

def main(args):
    script_root = os.path.dirname(args[0]) or os.path.curdir
    requirements_filename = os.path.normpath(os.path.join(script_root,
        os.path.pardir, 'doc', 'requirements.txt'))
    test_root = script_root
    log_level = 10
    log_file = None
    enable_regression_capture = True
    enable_regression_check = True
    regression_tolerance = 2
    interactive = True
    developer = False

    capabilities = ['GENERIC']
    platform_capabilities = {
        'linux2': 'X11',
        'win32': 'WIN',
        'cygwin': 'WIN',
        'darwin': 'OSX'
    }
    if sys.platform in platform_capabilities:
        capabilities.append(platform_capabilities[sys.platform])

    arguments = ['requirements=',
         'test-root=',
         'capabilities=',
         'log-level=',
         'log-file=',
         'regression-path=',
         'regression-tolerance=',
         'no-regression-capture',
         'no-regression-check',
         'no-interactive',
         'developer',
         'help',
         'full-help'
    ]

    def usage():
        print '''Usage: %s [args] [tests]
Runs tests, optionally limited to just those specified as "tests" which may
be a regular expression (e.g. "image" to just run image tests).

OPTIONS (with default values):
  --requirements=%s
  --test-root=%s
  --capabilities=%s
  --log-level=%s
  --log-file=%s
  --regression-path=%s
  --regression-tolerance=%s
  --no-regression-capture
  --no-regression-check
  --no-interactive
  --developer
  --help
  --full-help'''%(sys.argv[0], requirements_filename, test_root,
            ','.join(capabilities), log_level, log_file or '<stdout>',
            regressions_path, regression_tolerance)

    try:
        opts, arguments = getopt.getopt(args[1:], '', arguments)
    except getopt.GetoptError, error:
        print '\nERROR:', error
        print
        usage()
        return

    for key, value in opts:
        if key == '--requirements':
            requirements_filename = value
        elif key == '--test-root':
            test_root = value
        elif key == '--capabilities':
            capabilities = value.split(',')
        elif key == '--log-level':
            log_level = int(value)
        elif key == '--log-file':
            log_file = value
        elif key == '--regression-path':
            global regressions_path
            regressions_path = value
        elif key == '--regression-tolerance':
            regression_tolerance = int(value)
        elif key == '--no-regression-capture':
            enable_regression_capture = False
        elif key == '--no-regression-check':
            enable_regression_check = False
        elif key == '--no-interactive':
            interactive = False
            enable_regression_capture = False
        elif key == '--developer':
            developer = True
        elif key == '--help':
            usage()
            return
        elif key == '--full-help':
            print __doc__
            return

    if developer:
        capabilities.append('DEVELOPER')

    if enable_regression_capture:
        try:
            os.makedirs(regressions_path)
        except OSError:
            pass

    logging.basicConfig(filename=log_file, level=log_level)

    log = logging.getLogger()

    log.info('Beginning test at %s', time.ctime())
    log.info('Capabilities are: %s', ', '.join(capabilities))
    log.info('sys.platform = %s', sys.platform)
    log.info('Reading requirements from %s', requirements_filename)
    requirements = Requirements.from_rst(open(requirements_filename).read())

    # Parse arguments: each one is the name of either a section or
    # a sepecific component.  Add all components under a section and
    # its subsection.  If nothing specified, test everything.
    if arguments:
        sections = []
        components = []
        for arg in arguments:
            matches = requirements.search(arg)
            if not matches:
                log.error('No components or sections match "%s"', arg)
            components += matches
    else:
        components = requirements.get_all_components()

    components = list(set(components))
    components.sort()

    # Now test each component
    for component in components:
        if not component.is_implemented(capabilities):
            log.info('%s is marked not implemented, skipping.', component)
            continue
        log.info('Testing %s.', component)
        module = None
        try:
            module = component.get_module(test_root)
        except IOError:
            log.warning('No test exists for %s', component)
        except Exception:
            log.exception('Cannot load test for %s', component)
        if not module:
            continue

        module_interactive = interactive and \
         not (hasattr(module, '__noninteractive') and module.__noninteractive)

        if enable_regression_check and \
           os.path.exists(component.get_regression_image_filename()):
            result = RegressionCheckTestResult(component, regression_tolerance)
            module_interactive = False
        elif enable_regression_capture:
            result = RegressionCaptureTestResult(component)
        else:
            result = StandardTestResult(component)

        if module_interactive:
            print '-' * 78
            if module.__doc__:
                print module.__doc__
            raw_input('Press return to begin test...')
        suite = unittest.TestLoader().loadTestsFromModule(module)

        log.info('Begin unit tests for %s', component)
        suite(result)
        for failure in result.failures:
            log.error('Failure in %s', component)
            log.error(failure[1])
        for error in result.errors:
            log.error('Error in %s', component)
            log.error(error[1])
        log.info('%d tests run', result.testsRun)

        if (module_interactive and 
            len(result.failures) == 0 and 
            len(result.errors) == 0):
            user_result = raw_input('[P]assed test, [F]ailed test: ')
            if user_result and user_result[0] in ('F', 'f'):
                print 'Enter failure description: '
                description = raw_input('> ')
                log.error('User marked fail for %s', component)
                log.error(description)
            else:
                log.info('User marked pass for %s', component)
                result.setUserPass()
        

if __name__ == '__main__':
    main(sys.argv)


