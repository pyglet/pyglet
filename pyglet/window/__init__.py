#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import pyglet.window.key

class WindowException(Exception):
    pass

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

class BaseWindow(object):
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

class Event(object):
    def __init__(self, window, sequence):
        self.window = window
        self.sequence = sequence

    def __repr__(self):
        return '%s()' % self.__class__.__name__

class KeyEvent(Event):
    def __init__(self, window, sequence, symbol, modifiers, characters):
        super(KeyEvent, self).__init__(window, sequence)
        self.symbol = symbol
        self.modifiers = modifiers
        self.characters = characters

    def __repr__(self):
        mod_names = []
        if self.modifiers & pyglet.window.key.MOD_SHIFT:
            mod_names.append('MOD_SHIFT')
        if self.modifiers & pyglet.window.key.MOD_CTRL:
            mod_names.append('MOD_CTRL')
        if self.modifiers & pyglet.window.key.MOD_ALT:
            mod_names.append('MOD_ALT')
        if self.modifiers & pyglet.window.key.MOD_CAPSLOCK:
            mod_names.append('MOD_CAPSLOCK')
        if self.modifiers & pyglet.window.key.MOD_NUMLOCK:
            mod_names.append('MOD_NUMLOCK')
        return '%s(symbol=%s, modifiers=%s, characters=%r)' % \
           (self.__class__.__name__, 
            pyglet.window.key._key_names.get(self.symbol, str(self.symbol)),
            '+'.join(mod_names),
            self.characters)

class KeyPressEvent(KeyEvent):
    pass

class KeyReleaseEvent(KeyEvent):
    pass

try:
    from pyglet.window.xlib import XlibWindowFactory
    WindowFactory = XlibWindowFactory
except:
    pass

try:
    from pyglet.window.carbon import CarbonWindowFactory
    WindowFactory = CarbonWindowFactory
except:
    pass

try:
    from pyglet.window.win32 import Win32WindowFactory
    WindowFactory = Win32WindowFactory
except:
    pass
