# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2021 pyglet contributors
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

from pyglet.libs.darwin.cocoapy import ObjCClass, ObjCSubclass, ObjCInstance
from pyglet.libs.darwin.cocoapy import NSApplicationDidHideNotification
from pyglet.libs.darwin.cocoapy import NSApplicationDidUnhideNotification
from pyglet.libs.darwin.cocoapy import send_super, get_selector
from pyglet.libs.darwin.cocoapy import PyObjectEncoding
from pyglet.libs.darwin.cocoapy import quartz
from .systemcursor import SystemCursor

NSNotificationCenter = ObjCClass('NSNotificationCenter')
NSApplication = ObjCClass('NSApplication')


class PygletDelegate_Implementation:
    PygletDelegate = ObjCSubclass('NSObject', 'PygletDelegate')

    @PygletDelegate.method(b'@'+PyObjectEncoding)
    def initWithWindow_(self, window):
        self = ObjCInstance(send_super(self, 'init'))

        if not self:
            return None

        # CocoaWindow object.
        self._window = window
        window._nswindow.setDelegate_(self)

        # Register delegate for hide and unhide notifications so that we
        # can dispatch the corresponding pyglet events.
        notificationCenter = NSNotificationCenter.defaultCenter()

        notificationCenter.addObserver_selector_name_object_(
            self, get_selector('applicationDidHide:'),
            NSApplicationDidHideNotification, None)

        notificationCenter.addObserver_selector_name_object_(
            self, get_selector('applicationDidUnhide:'),
            NSApplicationDidUnhideNotification, None)

        # Flag set when we pause exclusive mouse mode if window loses key status.
        self.did_pause_exclusive_mouse = False
        return self

    @PygletDelegate.method('v')
    def dealloc(self):
        # Unregister delegate from notification center.
        notificationCenter = NSNotificationCenter.defaultCenter()
        notificationCenter.removeObserver_(self)
        self._window = None
        send_super(self, 'dealloc')

    @PygletDelegate.method('v@')
    def applicationDidHide_(self, notification):
        self._window.dispatch_event("on_hide")

    @PygletDelegate.method('v@')
    def applicationDidUnhide_(self, notification):
        if self._window._mouse_exclusive and quartz.CGCursorIsVisible():
            # The cursor should be hidden, but for some reason it's not;
            # try to force the cursor to hide (without over-hiding).
            SystemCursor.unhide()
            SystemCursor.hide()
            pass
        self._window.dispatch_event("on_show")

    @PygletDelegate.method('B@')
    def windowShouldClose_(self, notification):
        # The method is not called if [NSWindow close] was used.
        self._window.dispatch_event("on_close")
        return False

    @PygletDelegate.method('v@')
    def windowDidMove_(self, notification):
        x, y = self._window.get_location()
        self._window.dispatch_event("on_move", x, y)

    @PygletDelegate.method('v@')
    def windowDidBecomeKey_(self, notification):
         # Restore exclusive mouse mode if it was active before we lost key status.
         if self.did_pause_exclusive_mouse:
             self._window.set_exclusive_mouse(True)
             self.did_pause_exclusive_mouse = False
             self._window._nswindow.setMovable_(True)  # Mac OS 10.6
         # Restore previous mouse visibility settings.
         self._window.set_mouse_platform_visible()
         self._window.dispatch_event("on_activate")

    @PygletDelegate.method('v@')
    def windowDidResignKey_(self, notification):
        # Pause exclusive mouse mode if it is active.
        if self._window._mouse_exclusive:
            self._window.set_exclusive_mouse(False)
            self.did_pause_exclusive_mouse = True
            # We need to prevent the window from being unintentionally dragged
            # (by the call to set_mouse_position in set_exclusive_mouse) when
            # the window is reactivated by clicking on its title bar.
            self._window._nswindow.setMovable_(False)  # Mac OS X 10.6
        # Make sure that cursor is visible.
        self._window.set_mouse_platform_visible(True)
        self._window.dispatch_event("on_deactivate")

    @PygletDelegate.method('v@')
    def windowDidMiniaturize_(self, notification):
        self._window.dispatch_event("on_hide")

    @PygletDelegate.method('v@')
    def windowDidDeminiaturize_(self, notification):
        if self._window._mouse_exclusive and quartz.CGCursorIsVisible():
            # The cursor should be hidden, but for some reason it's not;
            # try to force the cursor to hide (without over-hiding).
            SystemCursor.unhide()
            SystemCursor.hide()
            pass
        self._window.dispatch_event("on_show")

    @PygletDelegate.method('v@')
    def windowDidExpose_(self,  notification):
        self._window.dispatch_event("on_expose")

    @PygletDelegate.method('v@')
    def terminate_(self, sender):
        NSApp = NSApplication.sharedApplication()
        NSApp.terminate_(self)

    @PygletDelegate.method('B@')
    def validateMenuItem_(self, menuitem):
        # Disable quitting with command-q when in keyboard exclusive mode.
        if menuitem.action() == get_selector('terminate:'):
            return not self._window._keyboard_exclusive
        return True


PygletDelegate = ObjCClass('PygletDelegate')
