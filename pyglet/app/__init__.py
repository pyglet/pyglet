#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import sys
import weakref

class WeakSet(object):
    '''Set of objects, referenced weakly.

    Adding an object to this set does not prevent it from being garbage
    collected.  Upon being garbage collected, the object is automatically
    removed from the set.
    '''
    def __init__(self):
        self._dict = weakref.WeakKeyDictionary()

    def add(self, value):
        self._dict[value] = True

    def remove(self, value):
        del self._dict[value]

    def __iter__(self):
        for key in self._dict.keys():
            yield key

    def __contains__(self, other):
        return other in self._dict

    def __len__(self):
        return len(self._dict)

#: Set of all open displays.  Instances of `Display` are automatically added
#: to this set upon construction.  The set uses weak references, so displays
#: are removed from the set when they are no longer referenced.
displays = WeakSet()

#: Set of all open windows (including invisible windows).  Instances of
#: `Window` are automatically added to this set upon construction.  The set
#: uses weak references, so windows are removed from the set when they are no
#: longer referenced or are closed explicitly.
windows = WeakSet()

class BaseEventLoop(object):
    has_exit = False

    def setup(self):
        # Disable event queuing for dispatch_events
        from pyglet.window import Window
        Window._enable_event_queue = False
        for window in windows:
            window.switch_to()
            window.dispatch_pending_events()

    def run(self):
        raise NotImplementedError('abstract')

if hasattr(sys, 'is_epydoc') and sys.is_epydoc:
    EventLoop = BaseEventLoop
    EventLoop.__name__ = 'EventLoop'
    del BaseEventLoop
else:
    if sys.platform == 'darwin':
        from pyglet.app.carbon import CarbonEventLoop as EventLoop
    elif sys.platform in ('win32', 'cygwin'):
        from pyglet.app.win32 import Win32EventLoop as EventLoop
    else:
        from pyglet.app.xlib import XlibEventLoop as EventLoop

def run():
    EventLoop().run()
