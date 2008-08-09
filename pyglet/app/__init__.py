# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright 
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

'''Application-wide functionality.

Most applications need only call `run` after creating one or more windows
to begin processing events.  For example, a simple application consisting of
one window is::

    from pyglet import app
    from pyglet import window

    win = window.Window()
    app.run()

To handle events on the main event loop, instantiate it manually.  The
following example exits the application as soon as any window is closed (the
default policy is to wait until all windows are closed)::

    event_loop = app.EventLoop()

    @event_loop.event
    def on_window_close(window):
        event_loop.exit()

:since: pyglet 1.1
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import sys
import weakref

_is_epydoc = hasattr(sys, 'is_epydoc') and sys.is_epydoc

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
#:
#: :type: `WeakSet`
displays = WeakSet()

#: Set of all open windows (including invisible windows).  Instances of
#: `Window` are automatically added to this set upon construction.  The set
#: uses weak references, so windows are removed from the set when they are no
#: longer referenced or are closed explicitly.
#:
#: :type: `WeakSet`
windows = WeakSet()

def run():
    '''Begin processing events, scheduled functions and window updates.

    This is a convenience function, equivalent to::

        pyglet.app.event_loop.run()

    '''
    event_loop.run()

def exit():
    '''Exit the application event loop.

    Causes the application event loop to finish, if an event loop is currently
    running.  The application may not necessarily exit (for example, there may
    be additional code following the `run` invocation).

    This is a convenience function, equivalent to::

        event_loop.exit()

    '''
    event_loop.exit()

if _is_epydoc:
    from pyglet.app.base import EventLoop
else:
    if sys.platform == 'darwin':
        from pyglet.app.carbon import CarbonEventLoop as EventLoop
    elif sys.platform in ('win32', 'cygwin'):
        from pyglet.app.win32 import Win32EventLoop as EventLoop
    else:
        from pyglet.app.xlib import XlibEventLoop as EventLoop

#: The global event loop.  Applications can replace this with their own
#: subclass of `pyglet.app.base.EventLoop`, but must take care to do so before
#: any pyglet.app function is called, and before any other pyglet threads
#: are started (for example, via media playback).
#:
#: :type: `EventLoop`
event_loop = EventLoop()
