#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

class WindowException(Exception):
    pass

class BaseWindowFactory(object):
    def __init__(self):
        pass

    def set_config(**kwargs):
        for key, value in kwargs:
            self.config._attributes[key] = value

class BaseWindow(object):
    pass

class BaseGLConfig(object):
    def __init__(self, **kwargs):
        self._attributes = kwargs

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
    def __init__(self, window, sequence, symbol):
        super(KeyEvent, self).__init__(window, sequence)
        self.symbol = symbol

    def __repr__(self):
        return '%s(symbol=%r)' % (self.__class__.__name__, self.symbol)

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
