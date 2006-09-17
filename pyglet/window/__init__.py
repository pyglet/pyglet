#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import inspect

import pyglet.window.event
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
    def __init__(self):
        self._event_stack = [{}]

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

    def push_handlers(self, instance=None, **kwargs):
        self._event_stack.insert(0, {})
        self.set_handlers(instance, **kwargs)

    def set_handlers(self, instance=None, **kwargs):
        if instance:
            for name, handler in inspect.getmembers(instance):
                event_type = pyglet.window.event._event_types.get(name, None)
                if event_type:
                    self._event_stack[0][event_type] = handler
        else:
            for event_name, handler in kwargs.items():
                event_type = pyglet.window.event._event_types.get(event_name, None)
                if not event_type:
                    raise WindowException('Unknown event "%s"' % event_name)
                self._event_stack[0][event_type] = handler
    
    def pop_handlers(self):
        del self._event_stack[0]

    def dispatch_event(self, event_type, *args):
        for frame in self._event_stack[:]:
            handler = frame.get(event_type, None)
            if handler:
                if handler(*args) != pyglet.window.event.EVENT_UNHANDLED:
                    break
        return None

    def dispatch_events(self):
        raise NotImplementedError('Abstract; this method needs overriding')

class BaseGLConfig(object):
    def __init__(self):
        self._attributes = {}

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._attributes)

class BaseGLContext(object):
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
