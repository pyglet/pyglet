from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING

from pyglet.libs.darwin.cocoapy import (
    CFSTR,
    ObjCClass,
    ObjCInstance,
    PyObjectEncoding,
    cf,
    cfstring_to_string,
    send_super,
    objc_method,
)
from pyglet.window import key

if TYPE_CHECKING:
    from pyglet.window.apple.cocoa import CocoaWindow

NSArray = ObjCClass('NSArray')
NSApplication = ObjCClass('NSApplication')
NSColor = ObjCClass('NSColor')
NSTextView = ObjCClass('NSTextView')

# This custom NSTextView subclass is used for capturing all of the
# on_text, on_text_motion, and on_text_motion_select events.
class PygletTextView(NSTextView):

    @objc_method(b'@' + PyObjectEncoding)
    def initWithCocoaWindow_(self, window: CocoaWindow) -> ObjCInstance | None:
        self = ObjCInstance(send_super(self, 'init'))
        if not self:
            return None
        self._window = window
        # Interpret tab and return as raw characters
        self.setFieldEditor_(False)
        empty_string = CFSTR('')
        self.associate("empty_string", empty_string)

        # Prevent a blinking cursor in bottom left corner Python 3.9 w/ ARM mac.
        self.setInsertionPointColor_(NSColor.clearColor())
        return self

    @objc_method("v@")
    def mouseMoved_(self, event):
        # prevent cursor from being set to I-beam
        self.nextResponder().mouseMoved_(event)

    @objc_method('v')
    def dealloc(self) -> None:
        self._window = None
        cf.CFRelease(self.empty_string)
        send_super(self, 'dealloc')

    # Other functions still seem to work?
    @objc_method('v@')
    def keyDown_(self, nsevent: ObjCInstance) -> None:

        # Ignore F5 key text editing action
        # to prevent showing autocomplete suggestions
        if nsevent.keyCode() != 96:
            array = NSArray.arrayWithObject_(nsevent)
            self.interpretKeyEvents_(array)

        if not self.performKeyEquivalent_(nsevent):
            self.nextResponder().keyDown_(nsevent)

    @objc_method('v@')
    def keyUp_(self, nsevent: ObjCInstance) -> None:
        self.nextResponder().keyUp_(nsevent)

    @objc_method('v@')
    def insertText_(self, text: CFSTR) -> None:
        text = cfstring_to_string(text)
        self.setString_(self.empty_string)
        # Don't send control characters (tab, newline) as on_text events.
        if text and unicodedata.category(text[0]) != 'Cc':
            self._window.dispatch_event('on_text', text)

    @objc_method('v@')
    def insertNewline_(self, sender: ObjCInstance) -> None:
        # Distinguish between carriage return (u'\r') and enter (u'\x03').
        # Only the return key press gets sent as an on_text event.
        event = NSApplication.sharedApplication().currentEvent()
        chars = event.charactersIgnoringModifiers()
        ch = chr(chars.characterAtIndex_(0))
        if ch == '\r':
            self._window.dispatch_event('on_text', '\r')

    @objc_method('v@')
    def moveUp_(self, sender: ObjCInstance) -> None:
        self._window.dispatch_event('on_text_motion', key.MOTION_UP)

    @objc_method('v@')
    def moveDown_(self, sender: ObjCInstance) -> None:
        self._window.dispatch_event('on_text_motion', key.MOTION_DOWN)

    @objc_method('v@')
    def moveLeft_(self, sender: ObjCInstance) -> None:
        self._window.dispatch_event('on_text_motion', key.MOTION_LEFT)

    @objc_method('v@')
    def moveRight_(self, sender: ObjCInstance) -> None:
        self._window.dispatch_event('on_text_motion', key.MOTION_RIGHT)

    @objc_method('v@')
    def moveWordLeft_(self, sender: ObjCInstance) -> None:
        self._window.dispatch_event('on_text_motion', key.MOTION_PREVIOUS_WORD)

    @objc_method('v@')
    def moveWordRight_(self, sender: ObjCInstance) -> None:
        self._window.dispatch_event('on_text_motion', key.MOTION_NEXT_WORD)

    @objc_method('v@')
    def moveToBeginningOfLine_(self, sender: ObjCInstance) -> None:
        self._window.dispatch_event('on_text_motion', key.MOTION_BEGINNING_OF_LINE)

    @objc_method('v@')
    def moveToEndOfLine_(self, sender: ObjCInstance) -> None:
        self._window.dispatch_event('on_text_motion', key.MOTION_END_OF_LINE)

    @objc_method('v@')
    def scrollPageUp_(self, sender: ObjCInstance) -> None:
        self._window.dispatch_event('on_text_motion', key.MOTION_PREVIOUS_PAGE)

    @objc_method('v@')
    def scrollPageDown_(self, sender: ObjCInstance) -> None:
        self._window.dispatch_event('on_text_motion', key.MOTION_NEXT_PAGE)

    @objc_method('v@')
    def scrollToBeginningOfDocument_(self, sender: ObjCInstance) -> None:  # Mac OS X 10.6
        self._window.dispatch_event('on_text_motion', key.MOTION_BEGINNING_OF_FILE)

    @objc_method('v@')
    def scrollToEndOfDocument_(self, sender: ObjCInstance) -> None:  # Mac OS X 10.6
        self._window.dispatch_event('on_text_motion', key.MOTION_END_OF_FILE)

    @objc_method('v@')
    def deleteBackward_(self, sender: ObjCInstance) -> None:
        self._window.dispatch_event('on_text_motion', key.MOTION_BACKSPACE)

    @objc_method('v@')
    def deleteForward_(self, sender: ObjCInstance) -> None:
        self._window.dispatch_event('on_text_motion', key.MOTION_DELETE)

    @objc_method('v@')
    def moveUpAndModifySelection_(self, sender: ObjCInstance) -> None:
        self._window.dispatch_event('on_text_motion_select', key.MOTION_UP)

    @objc_method('v@')
    def moveDownAndModifySelection_(self, sender: ObjCInstance) -> None:
        self._window.dispatch_event('on_text_motion_select', key.MOTION_DOWN)

    @objc_method('v@')
    def moveLeftAndModifySelection_(self, sender: ObjCInstance) -> None:
        self._window.dispatch_event('on_text_motion_select', key.MOTION_LEFT)

    @objc_method('v@')
    def moveRightAndModifySelection_(self, sender: ObjCInstance) -> None:
        self._window.dispatch_event('on_text_motion_select', key.MOTION_RIGHT)

    @objc_method('v@')
    def moveWordLeftAndModifySelection_(self, sender: ObjCInstance) -> None:
        self._window.dispatch_event('on_text_motion_select', key.MOTION_PREVIOUS_WORD)

    @objc_method('v@')
    def moveWordRightAndModifySelection_(self, sender: ObjCInstance) -> None:
        self._window.dispatch_event('on_text_motion_select', key.MOTION_NEXT_WORD)

    @objc_method('v@')
    def moveToBeginningOfLineAndModifySelection_(self, sender: ObjCInstance) -> None:  # Mac OS X 10.6
        self._window.dispatch_event('on_text_motion_select', key.MOTION_BEGINNING_OF_LINE)

    @objc_method('v@')
    def moveToEndOfLineAndModifySelection_(self, sender: ObjCInstance) -> None:  # Mac OS X 10.6
        self._window.dispatch_event('on_text_motion_select', key.MOTION_END_OF_LINE)

    @objc_method('v@')
    def pageUpAndModifySelection_(self, sender: ObjCInstance) -> None:  # Mac OS X 10.6
        self._window.dispatch_event('on_text_motion_select', key.MOTION_PREVIOUS_PAGE)

    @objc_method('v@')
    def pageDownAndModifySelection_(self, sender: ObjCInstance) -> None:  # Mac OS X 10.6
        self._window.dispatch_event('on_text_motion_select', key.MOTION_NEXT_PAGE)

    @objc_method('v@')
    def moveToBeginningOfDocumentAndModifySelection_(self, sender: ObjCInstance) -> None:  # Mac OS X 10.6
        self._window.dispatch_event('on_text_motion_select', key.MOTION_BEGINNING_OF_FILE)

    @objc_method('v@')
    def moveToEndOfDocumentAndModifySelection_(self, sender: ObjCInstance) -> None:  # Mac OS X 10.6
        self._window.dispatch_event('on_text_motion_select', key.MOTION_END_OF_FILE)
