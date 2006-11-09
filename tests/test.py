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
    implementation and/or environment.  For example, the pyglet.window
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
    example: pyglet.window is a section.

The requirements document (doc/requirements.txt) is written in
reStructured text and contains all the sections, components and
capabilities for the project.  The intent here is to integrate
our writings on "what needs to be done" with "what has been done"
and "what works at the moment".

A finished component is marked against the appropriate capabilities
with an "X"; partial or incomplete implementations with either a "/"
or empty table cell.  This test script will not attempt to run
unit tests for unfinished implementations.

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
--no-interactive=
    Don't write descriptions or prompt for confirmation; just run each
    test in succcession.

After the command line options, you can specify the names of any
sections or capabilities you wish to test.  If none are specified, all
tests are run.  For example::

    python test/test.py --capabilities=NVIDIA,WIN pyglet.window

Runs all tests in the pyglet.window section with the given capabilities.

    python test/test.py --no-interactive pyglet.window.FULLSCREEN_TOGGLE

Test just the FULLSCREEN_TOGGLE component in the pyglet.window section,
without prompting for input (useful for development).

Writing tests
-------------

Add the capability to the appropriate implementation table in the requirements
document (see requirements.txt for formatting).   Create one unit test
script per capability, located in the directory corresponding to the
section.  For example, the test for pyglet.window.FULLSCREEN_TOGGLE is
located at::

    test/pyglet/window/FULLSCREEN_TOGGLE.py

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

Open questions
--------------

- Can/should this be integrated into an issue tracker?
- What should be done with test logs?
- Wouldn't an ncurses interface for this be cool?

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import docutils.nodes
import docutils.parsers.rst
import getopt
import imp
import logging
import os
import sys
import time
import unittest

class RequirementsComponent(object):
    FULL = 50
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
        return self.get_progress(capabilities) >= self.FULL

    def get_module_filename(self, root=''):
        path = os.path.join(*self.get_absname().split('.'))
        return '%s.py' % os.path.join(root, path)

    def get_module(self, root=''):
        module_name = self.get_absname().replace('.', '_')
        suffixes = ('.py', 'r', imp.PY_SOURCE)
        filename = self.get_module_filename(root)
        file = open(filename, 'r')
        return imp.load_module(module_name, file, filename, suffixes)

    def __repr__(self):
        return 'RequirementsComponent(%s)' % self.get_absname()

    def __str__(self):
        return self.get_absname()

class RequirementsSection(object):
    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        self.description = ''
        self.sections = {}
        self.components = {}

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
        components = self.components.values()
        for section in self.sections.values():
            components += section.get_all_components()
        return components
    
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

def main(args):
    script_root = os.path.dirname(args[0]) or os.path.curdir
    requirements_filename = os.path.sep.join(
        [script_root, os.path.pardir, 'doc', 'requirements.txt'])
    test_root = script_root
    log_level = 10
    log_file = None
    interactive = True

    capabilities = []
    platform_capabilities = {
        'linux2': 'X11',
        'win32': 'WIN',
        'darwin': 'OSX'
    }
    if sys.platform in platform_capabilities:
        capabilities.append(platform_capabilities[sys.platform])

    opts, arguments = getopt.getopt(args[1:], '',
        ['requirements=',
         'test-root=',
         'capabilities=',
         'log-level=',
         'log-file=',
         'no-interactive'])

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
        elif key == '--no-interactive':
            interactive = False

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
            section = requirements.get_section(arg)
            if section:
                sections.append(requirements.get_section(arg))
            else:
                component = requirements.get_component(arg)
                if component:
                    components.append(requirements.get_component(arg))
                else:
                    log.error('No section or component named %s' % arg)
    else:
        sections = [requirements]
        components = []

    for section in sections:
        components += section.get_all_components()

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

        if module_interactive:
            print '-' * 78
            if module.__doc__:
                print module.__doc__
            raw_input('Press a key to begin test...')
        suite = unittest.TestLoader().loadTestsFromModule(module)
        result = unittest.TestResult()
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
            result = raw_input('[P]assed test, [F]ailed test: ')
            if result and result[0] in ('F', 'f'):
                print 'Enter failure description: '
                description = raw_input('> ')
                log.error('User marked fail for %s', component)
                log.error(description)
            else:
                log.info('User marked pass for %s', component)

if __name__ == '__main__':
    main(sys.argv)


