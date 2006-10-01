#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import sys

from pyglet.window.event import WindowEventHandler
import pyglet.window.key

class WindowException(Exception):
    pass

class Mouse(object):
    def __init__(self):
        self.x, self.y = 0, 0
        self.buttons = [False] * 6      # mouse buttons index from 1 + 

class BaseWindowFactory(object):
    def __init__(self):
        self.config = self.create_config_prototype()

    def create(self, width=640, height=480):
        window = self.create_window(width, height)
        configs = self.get_config_matches(window)
        if len(configs) == 0:
            raise WindowException('No matching GL configuration available')
        config = configs[0]
        context = self.create_context(window, config)
        window.set_context(config, context)

        import sys
        window.set_title(sys.argv[0])
        window.switch_to()
        return window

    def create_config_prototype(self):
        pass
        
    def create_window(self, width, height):
        pass

    def get_config_matches(self, window):
        pass

    def create_context(self, window, config, share_context=None):
        pass

class BaseWindow(WindowEventHandler):
    def __init__(self):
        WindowEventHandler.__init__(self)
        self.mouse = Mouse()

    def set_title(self, title):
        self.title = title

    def get_title(self):
        return self.title

    def set_context(self, config, context):
        self.config = config
        self.context = context

    def get_context(self):
        return self.context

    def get_config(self):
        return self.config

class BaseGLConfig(object):
    def __init__(self):
        self._attributes = {}

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._attributes)

class BaseGLContext(object):
    pass

if sys.platform == 'darwin':
    from pyglet.window.carbon import CarbonWindowFactory
    WindowFactory = CarbonWindowFactory
elif sys.platform == 'win32':
    from pyglet.window.win32 import Win32WindowFactory
    WindowFactory = Win32WindowFactory
else:
    from pyglet.window.xlib import XlibWindowFactory
    WindowFactory = XlibWindowFactory

