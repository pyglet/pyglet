# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2022 pyglet contributors
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

import unicodedata

from pyglet.window import key

from pyglet.libs.darwin.cocoapy import ObjCClass, ObjCSubclass, ObjCInstance
from pyglet.libs.darwin.cocoapy import PyObjectEncoding, send_super
from pyglet.libs.darwin.cocoapy import CFSTR, cfstring_to_string

NSArray = ObjCClass('NSArray')
NSApplication = ObjCClass('NSApplication')

# This custom NSTextView subclass is used for capturing all of the
# on_text, on_text_motion, and on_text_motion_select events.
class PygletTextView_Implementation:
    PygletTextView = ObjCSubclass('NSTextView', 'PygletTextView')

    @PygletTextView.method(b'@'+PyObjectEncoding)
    def initWithCocoaWindow_(self, window):
        self = ObjCInstance(send_super(self, 'init'))
        if not self:
            return None
        self._window = window
        # Interpret tab and return as raw characters
        self.setFieldEditor_(False)
        self.empty_string = CFSTR("")
        return self

    @PygletTextView.method('v')
    def dealloc(self):
        self.empty_string.release()

    @PygletTextView.method('v@')
    def keyDown_(self, nsevent):
        array = NSArray.arrayWithObject_(nsevent)
        self.interpretKeyEvents_(array)

    @PygletTextView.method('v@')
    def insertText_(self, text):
        text = cfstring_to_string(text)
        self.setString_(self.empty_string)
        # Don't send control characters (tab, newline) as on_text events.
        if unicodedata.category(text[0]) != 'Cc':
            self._window.dispatch_event("on_text", text)

    @PygletTextView.method('v@')
    def insertNewline_(self, sender):
        # Distinguish between carriage return (u'\r') and enter (u'\x03').
        # Only the return key press gets sent as an on_text event.
        event = NSApplication.sharedApplication().currentEvent()
        chars = event.charactersIgnoringModifiers()
        ch = chr(chars.characterAtIndex_(0))
        if ch == u'\r':
            self._window.dispatch_event("on_text", u'\r')

    @PygletTextView.method('v@')
    def moveUp_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_UP)

    @PygletTextView.method('v@')
    def moveDown_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_DOWN)

    @PygletTextView.method('v@')
    def moveLeft_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_LEFT)

    @PygletTextView.method('v@')
    def moveRight_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_RIGHT)

    @PygletTextView.method('v@')
    def moveWordLeft_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_PREVIOUS_WORD)

    @PygletTextView.method('v@')
    def moveWordRight_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_NEXT_WORD)

    @PygletTextView.method('v@')
    def moveToBeginningOfLine_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_BEGINNING_OF_LINE)

    @PygletTextView.method('v@')
    def moveToEndOfLine_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_END_OF_LINE)

    @PygletTextView.method('v@')
    def scrollPageUp_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_PREVIOUS_PAGE)

    @PygletTextView.method('v@')
    def scrollPageDown_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_NEXT_PAGE)

    @PygletTextView.method('v@')
    def scrollToBeginningOfDocument_(self, sender):   # Mac OS X 10.6
        self._window.dispatch_event("on_text_motion", key.MOTION_BEGINNING_OF_FILE)

    @PygletTextView.method('v@')
    def scrollToEndOfDocument_(self, sender):         # Mac OS X 10.6
        self._window.dispatch_event("on_text_motion", key.MOTION_END_OF_FILE)

    @PygletTextView.method('v@')
    def deleteBackward_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_BACKSPACE)

    @PygletTextView.method('v@')
    def deleteForward_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_DELETE)

    @PygletTextView.method('v@')
    def moveUpAndModifySelection_(self, sender):
        self._window.dispatch_event("on_text_motion_select", key.MOTION_UP)

    @PygletTextView.method('v@')
    def moveDownAndModifySelection_(self, sender):
        self._window.dispatch_event("on_text_motion_select", key.MOTION_DOWN)

    @PygletTextView.method('v@')
    def moveLeftAndModifySelection_(self, sender):
        self._window.dispatch_event("on_text_motion_select", key.MOTION_LEFT)

    @PygletTextView.method('v@')
    def moveRightAndModifySelection_(self, sender):
        self._window.dispatch_event("on_text_motion_select", key.MOTION_RIGHT)

    @PygletTextView.method('v@')
    def moveWordLeftAndModifySelection_(self, sender):
        self._window.dispatch_event("on_text_motion_select", key.MOTION_PREVIOUS_WORD)

    @PygletTextView.method('v@')
    def moveWordRightAndModifySelection_(self, sender):
        self._window.dispatch_event("on_text_motion_select", key.MOTION_NEXT_WORD)

    @PygletTextView.method('v@')
    def moveToBeginningOfLineAndModifySelection_(self, sender):      # Mac OS X 10.6
        self._window.dispatch_event("on_text_motion_select", key.MOTION_BEGINNING_OF_LINE)

    @PygletTextView.method('v@')
    def moveToEndOfLineAndModifySelection_(self, sender):            # Mac OS X 10.6
        self._window.dispatch_event("on_text_motion_select", key.MOTION_END_OF_LINE)

    @PygletTextView.method('v@')
    def pageUpAndModifySelection_(self, sender):                     # Mac OS X 10.6
        self._window.dispatch_event("on_text_motion_select", key.MOTION_PREVIOUS_PAGE)

    @PygletTextView.method('v@')
    def pageDownAndModifySelection_(self, sender):                   # Mac OS X 10.6
        self._window.dispatch_event("on_text_motion_select", key.MOTION_NEXT_PAGE)

    @PygletTextView.method('v@')
    def moveToBeginningOfDocumentAndModifySelection_(self, sender):  # Mac OS X 10.6
        self._window.dispatch_event("on_text_motion_select", key.MOTION_BEGINNING_OF_FILE)

    @PygletTextView.method('v@')
    def moveToEndOfDocumentAndModifySelection_(self, sender):        # Mac OS X 10.6
        self._window.dispatch_event("on_text_motion_select", key.MOTION_END_OF_FILE)


PygletTextView = ObjCClass('PygletTextView')
