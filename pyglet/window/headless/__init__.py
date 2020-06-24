# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2020 pyglet contributors
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

from pyglet.window import BaseWindow, _PlatformEventHandler, _ViewEventHandler
from pyglet.window import WindowException, NoSuchDisplayException, MouseCursorException
from pyglet.window import MouseCursor, DefaultMouseCursor, ImageMouseCursor

# from pyglet.window import key
# from pyglet.window import mouse
# from pyglet.event import EventDispatcher

# Platform event data is single item, so use platform event handler directly.
HeadlessEventHandler = _PlatformEventHandler
ViewEventHandler = _ViewEventHandler


class HeadlessWindow(BaseWindow):

    def __init__(self, *args, **kwargs):
        print("Makin window")
        super().__init__(*args, **kwargs)
        print("Made it!")

    def _recreate(self, changes):
        pass

    def flip(self):
        pass

    def switch_to(self):
        pass

    def set_caption(self, caption):
        pass

    def set_minimum_size(self, width, height):
        pass

    def set_maximum_size(self, width, height):
        pass

    def set_size(self, width, height):
        pass

    def get_size(self):
        pass

    def set_location(self, x, y):
        pass

    def get_location(self):
        pass

    def activate(self):
        pass

    def set_visible(self, visible=True):
        pass

    def minimize(self):
        pass

    def maximize(self):
        pass

    def set_vsync(self, vsync):
        pass

    def set_mouse_platform_visible(self, platform_visible=None):
        pass

    def set_exclusive_mouse(self, exclusive=True):
        pass

    def set_exclusive_keyboard(self, exclusive=True):
        pass

    def get_system_mouse_cursor(self, name):
        pass

    def dispatch_events(self):
        pass

    def _create(self):
        pass
