"""UIKit input methods for an incremental layout's existing document and caret."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any
from ctypes import c_bool, c_long

from pyglet.libs.darwin.cocoapy import (
    NSPointEncoding, NSRange, NSRangeEncoding, NSRectEncoding, NSMakeRect,
    ObjCClass, ObjCInstance, PyObjectEncoding, cfstring_to_string, get_NSString, objc_method, send_super,
    send_message,
)
from pyglet.util import from_utf16, to_utf16
from pyglet.window.textinput import AbstractTextInput

if TYPE_CHECKING:
    from pyglet.libs.darwin.cocoapy import CGPoint, CGRect
    from pyglet.window.textinput import TextInputSession
    from pyglet.window.apple.ios import IOSWindow

NSObject = ObjCClass('NSObject')
UITextView = ObjCClass('UITextView')
UIView = ObjCClass('UIView')
UIColor = ObjCClass('UIColor')

_KEYBOARD_TYPES = {'text': 0, 'url': 3, 'numeric': 4, 'tel': 5, 'email': 7, 'decimal': 8, 'search': 10}
_RETURN_KEY_TYPES = {'newline': 0, 'go': 1, 'next': 4, 'search': 6, 'send': 7, 'done': 9}


class _PygletIOSTextView(UITextView):  # type: ignore[valid-type, misc]
    _text_input: IOSTextInput | None

    @objc_method(b'@' + NSRectEncoding + PyObjectEncoding)
    def initWithFrame_textInput_(self: Any, frame: CGRect, text_input: IOSTextInput) -> ObjCInstance | None:
        self = ObjCInstance(send_super(self, 'initWithFrame:', frame,
                                       superclass_name='UITextView', argtypes=[type(frame)]))
        if self:
            self._text_input = text_input
        return self

    @objc_method(b'@' + NSPointEncoding + b'@')
    def hitTest_withEvent_(self, point: CGPoint, event: ObjCInstance) -> None:
        # GL handles taps and selection. The transparent native editor only receives keyboard input.
        return None

    @objc_method('v')
    def unmarkText(self) -> None:
        send_super(self, 'unmarkText', superclass_name='UITextView', restype=None)
        text_input = getattr(self, '_text_input', None)
        if text_input is not None:
            text_input.read()


class _PygletIOSTextInputDelegate(NSObject):  # type: ignore[valid-type, misc]
    _text_input: IOSTextInput | None

    @objc_method(b'@' + PyObjectEncoding)
    def initWithTextInput_(self: Any, text_input: IOSTextInput) -> ObjCInstance | None:
        self = ObjCInstance(send_super(self, 'init', superclass_name='NSObject'))
        if self:
            self._text_input = text_input
        return self

    @objc_method('v@')
    def textViewDidChange_(self, text_view: ObjCInstance) -> None:
        if self._text_input is not None:
            self._text_input.read()

    @objc_method('v@')
    def textViewDidChangeSelection_(self, text_view: ObjCInstance) -> None:
        if self._text_input is not None:
            self._text_input.read()

    @objc_method(b'B@' + NSRangeEncoding + b'@')
    def textView_shouldChangeTextInRange_replacementText_(self, text_view: ObjCInstance,
                                                        replacement_range: NSRange, text: ObjCInstance) -> bool:
        text_input = self._text_input
        if text_input is None or not text_input.session.active:
            return False
        if text_view.markedTextRange():
            # Return may confirm an IME candidate instead of submitting the field.
            return True
        session = text_input.session
        if cfstring_to_string(text) in ('\n', '\r') and not session.caret.layout.multiline:
            session.perform_action()
            if session.options.enter_action == 'done':
                session.close()
            return False
        return True

    @objc_method('v@')
    def textViewDidEndEditing_(self, text_view: ObjCInstance) -> None:
        if self._text_input is not None:
            self._text_input.session.close()


class IOSTextInput(AbstractTextInput['IOSWindow']):
    """Connect UIKit text editing to a layout.

    UIKit owns keyboard and marked-text handling. Committed replacements and
    selections are applied through the existing caret. Inline marked text and
    native selection handles over the GL layout are not implemented.
    """

    view: ObjCInstance | None
    _delegate: ObjCInstance | None
    _syncing: bool
    _composition_text: str | None

    def __init__(self, window: IOSWindow, session: TextInputSession) -> None:
        super().__init__(window, session)
        self.view = None
        self._delegate = None
        self._syncing = False
        self._composition_text = None

    def start(self) -> None:
        if self.window._uiview is None:  # noqa: SLF001
            raise RuntimeError('The iOS window has no native view.')
        self.view = _PygletIOSTextView.alloc().initWithFrame_textInput_(NSMakeRect(0, 0, 1, 1), self)
        self._delegate = _PygletIOSTextInputDelegate.alloc().initWithTextInput_(self)
        if self.view is None or self._delegate is None:
            raise RuntimeError('UIKit could not create a text input view.')
        self.view.setBackgroundColor_(UIColor.clearColor())
        self.view.setTextColor_(UIColor.clearColor())
        self.view.setTintColor_(UIColor.clearColor())
        self.view.setOpaque_(False)
        self.view.setShowsVerticalScrollIndicator_(False)
        self.view.setShowsHorizontalScrollIndicator_(False)
        send_message(self.view, 'setKeyboardType:', _KEYBOARD_TYPES[self.session.options.input_type],
                     restype=None, argtypes=[c_long])
        send_message(self.view, 'setReturnKeyType:', _RETURN_KEY_TYPES[self.session.options.enter_action],
                     restype=None, argtypes=[c_long])
        send_message(self.view, 'setSecureTextEntry:', self.session.options.password,
                     restype=None, argtypes=[c_bool])
        if self.session.options.password:
            send_message(self.view, 'setAutocorrectionType:', 1, restype=None, argtypes=[c_long])
            send_message(self.view, 'setAutocapitalizationType:', 0, restype=None, argtypes=[c_long])
            send_message(self.view, 'setSpellCheckingType:', 1, restype=None, argtypes=[c_long])
        if self.session.options.screen_keyboard == 'hide':
            # Keep a first responder for hardware input, with no software keyboard.
            empty_input = UIView.alloc().initWithFrame_(NSMakeRect(0, 0, 0, 0))
            self.view.setInputView_(empty_input)
            empty_input.release()
        self.view.setDelegate_(self._delegate)
        self.window._uiview.addSubview_(self.view)  # noqa: SLF001
        self.sync()
        # Both auto and show use UIKit's normal keyboard policy, including its
        # choice to keep the software keyboard hidden with hardware attached.
        if not self.view.becomeFirstResponder():
            raise RuntimeError('UIKit rejected text-input focus. The window must be visible and active.')

    def close(self) -> None:
        view, delegate = self.view, self._delegate
        self.view = None
        self._delegate = None
        if view is not None:
            # Resigning focus can call the delegate synchronously. Detach callbacks
            # before releasing either object so cleanup cannot re-enter the session.
            view.setDelegate_(None)
            setattr(view, '_text_input', None)
            view.resignFirstResponder()
            view.removeFromSuperview()
            view.release()
        if delegate is not None:
            setattr(delegate, '_text_input', None)
            delegate.release()

    def _update_geometry(self) -> None:
        x, y, width, height = self.session.caret_rect
        self.view.setFrame_(NSMakeRect(x, self.window.height - y - height,
                                       max(1, width), max(1, height)))

    def sync(self) -> None:
        if self._syncing or not self.session.active or self.view is None:
            return
        caret = self.session.caret
        text = caret.layout.document.text
        if self.view.markedTextRange():
            # Do not replace UIKit's uncommitted text. If the document changes
            # independently, end the session rather than later overwrite that edit.
            if self._composition_text is None:
                self._composition_text = text
            elif text != self._composition_text:
                self.session.close()
            return
        self._syncing = True
        try:
            if cfstring_to_string(self.view.text()) != text:
                self.view.setText_(get_NSString(text))
            anchor = caret.position if caret.mark is None else caret.mark
            start, end = sorted((anchor, caret.position))
            start, end = to_utf16(text, start), to_utf16(text, end)
            selected = self.view.selectedRange()
            if (selected.location, selected.length) != (start, end - start):
                self.view.setSelectedRange_(NSRange(start, end - start))
            self._update_geometry()
        finally:
            self._syncing = False

    def read(self) -> None:
        if self._syncing or not self.session.active or self.view is None:
            return
        caret = self.session.caret
        previous = caret.layout.document.text
        if self.view.markedTextRange():
            if self._composition_text is None:
                self._composition_text = previous
            return
        self._composition_text = None
        text = cfstring_to_string(self.view.text()) or ''
        selected = self.view.selectedRange()
        start = from_utf16(text, selected.location)
        end = from_utf16(text, selected.location + selected.length)
        self._syncing = True
        try:
            if text != previous:
                # Replace only the changed range so surrounding document styles survive.
                prefix = 0
                while prefix < min(len(previous), len(text)) and previous[prefix] == text[prefix]:
                    prefix += 1
                old_end, new_end = len(previous), len(text)
                while old_end > prefix and new_end > prefix and previous[old_end - 1] == text[new_end - 1]:
                    old_end -= 1
                    new_end -= 1
                anchor = caret.position if caret.mark is None else caret.mark
                if sorted((anchor, caret.position)) != [prefix, old_end]:
                    caret.mark = prefix
                    caret.position = old_end
                caret.on_text(text[prefix:new_end])
            anchor = caret.position if caret.mark is None else caret.mark
            # NSRange has no selection direction. Retain the existing anchor when possible.
            selection_anchor, position = (end, start) if start != end and anchor == end else (start, end)
            mark = None if start == end else selection_anchor
            if caret.mark != mark:
                caret.mark = mark
            if caret.position != position:
                caret.position = position
        finally:
            self._syncing = False
        self.session.update()
