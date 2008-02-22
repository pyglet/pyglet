#!/usr/bin/env python

'''Test that all public modules are accessible after importing just 'pyglet'.

This _must_ be the first test run.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: TICK.py 310 2006-12-23 15:56:35Z Alex.Holkner $'

import unittest

import pyglet

__noninteractive = True

modules = [
    'app',
    'clock',
    'event',
    'font',
    'font.base',
    'gl',
    'gl.gl_info',
    'gl.glu_info',
    'graphics',
    'graphics.allocation',
    'graphics.vertexattribute',
    'graphics.vertexbuffer',
    'graphics.vertexdomain',
    'image',
    'image.atlas',
    'media',
    'resource',
    'sprite',
    'text',
    'text.caret',
    'text.document',
    'text.layout',
    'text.runlist',
    'window',
    'window.event',
    'window.key',
    'window.mouse',
]

def add_module_tests(name, bases, dict):
    for module in modules:
        components = module.split('.')
        def create_test(components):
            def test_module(self):
                top = pyglet
                for component in components:
                    self.assertTrue(hasattr(top, component),
                      'Cannot access "%s" in "%s"' % (component, top.__name__))
                    top = getattr(top, component)
            return test_module
        test_module = create_test(components)
        test_name = 'test_%s' % module.replace('.', '_')
        test_module.__name__ = test_name
        dict[test_name] = test_module
    return type.__new__(type, name, bases, dict)

class TEST_CASE(unittest.TestCase):
    __metaclass__ = add_module_tests


if __name__ == '__main__':
    unittest.main()
