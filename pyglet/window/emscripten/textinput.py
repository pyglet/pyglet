"""Browser input-method transport for an incremental layout's existing caret."""
from __future__ import annotations

from typing import TYPE_CHECKING

import js

from pyglet.libs.emscripten.proxies import ProxyRegistry
from pyglet.util import from_utf16, to_utf16
from pyglet.window.textinput import AbstractTextInput

if TYPE_CHECKING:
    from pyglet.libs.emscripten.dom import Event, HTMLTextControl, InputEvent, KeyboardEvent
    from pyglet.window.textinput import TextInputSession
    from pyglet.window.emscripten import EmscriptenWindow


class BrowserTextInput(AbstractTextInput['EmscriptenWindow']):
    """Own a focusable browser control while the layout owns editing state.

    Native composition stays in the control until committed. Inline preedit
    rendering in the GL layout is not implemented here. An external edit during
    composition ends the session rather than overwriting the editor's changes.
    """

    control: HTMLTextControl
    _proxies: ProxyRegistry
    _syncing: bool
    _composing: bool
    _composition_text: str | None

    def __init__(self, window: EmscriptenWindow, session: TextInputSession) -> None:
        super().__init__(window, session)
        self._proxies = ProxyRegistry()
        self._syncing = False
        self._composing = False
        self._composition_text = None
        multiline = session.caret.layout.multiline and not session.options.password
        self.control = js.document.createElement('textarea' if multiline else 'input')
        if not multiline:
            self.control.type = 'password' if session.options.password else 'text'
        self.control.setAttribute('data-pyglet-text-input', '')
        self.control.setAttribute('aria-label', 'Text input')
        self.control.inputMode = 'none' if session.options.screen_keyboard == 'hide' else session.options.input_type
        self.control.enterKeyHint = 'enter' if session.options.enter_action == 'newline' else session.options.enter_action
        if session.options.password:
            self.control.setAttribute('autocomplete', 'off')
            self.control.setAttribute('autocapitalize', 'off')
            self.control.spellcheck = False
        # A rendered, focusable control is needed by mobile keyboards. Position it
        # at the caret for native candidate UI. The GL layout displays committed text.
        self.control.style.cssText = (
            'position:fixed;width:1px;padding:0;margin:0;border:0;'
            'font-size:16px;background:transparent;color:transparent;'
            'caret-color:transparent;opacity:0.01;pointer-events:none;'
        )

    def start(self) -> None:
        js.document.body.appendChild(self.control)
        self.sync()
        for name, callback in (
            ('input', self._on_input), ('select', self._on_selection),
            ('keyup', self._on_selection), ('keydown', self._on_key_down),
            ('compositionstart', self._on_composition_start), ('compositionend', self._on_composition_end),
            ('blur', self._on_blur),
        ):
            self._proxies.add_event_listener(self.control, name, callback)
        self._proxies.add_event_listener(js.document, 'selectionchange', self._on_selection)
        self._proxies.add_event_listener(js.window, 'blur', self._on_blur)
        for target in (js.window, getattr(js.window, 'visualViewport', None)):
            if target is not None:
                self._proxies.add_event_listener(target, 'scroll', self._on_geometry, passive=True)
                self._proxies.add_event_listener(target, 'resize', self._on_geometry)
        # Must run synchronously inside the user's tap/click to retain activation.
        self.control.focus(preventScroll=True)

    def close(self) -> None:
        self._proxies.destroy()
        self.control.remove()

    def _position_control(self) -> None:
        canvas = self.window.canvas
        rect = canvas.getBoundingClientRect()
        x, y, _, height = self.session.caret_rect
        scale_x = rect.width / canvas.width if canvas.width else 1.0
        scale_y = rect.height / canvas.height if canvas.height else 1.0
        self.control.style.setProperty('left', f'{rect.left + x * scale_x}px')
        self.control.style.setProperty('top', f'{rect.top + rect.height - (y + height) * scale_y}px')
        self.control.style.height = f'{max(16, height * scale_y)}px'

    def sync(self) -> None:
        if self._syncing or not self.session.active:
            return
        caret = self.session.caret
        text = caret.layout.document.text
        if self._composing:
            if text != self._composition_text:
                self.session.close()
            return
        self._syncing = True
        try:
            if self.control.value != text:
                self.control.value = text
            anchor = caret.position if caret.mark is None else caret.mark
            start, end = sorted((anchor, caret.position))
            start, end = to_utf16(text, start), to_utf16(text, end)
            direction = 'backward' if anchor > caret.position else 'forward'
            # Browsers normalize collapsed selection direction differently. Rewriting
            # it can trigger selectionchange repeatedly even though the cursor agrees.
            if ((self.control.selectionStart, self.control.selectionEnd) != (start, end)
                    or (start != end and self.control.selectionDirection != direction)):
                self.control.setSelectionRange(start, end, direction)
            self._position_control()
        finally:
            self._syncing = False

    def read(self) -> None:
        if self._syncing or self._composing or not self.session.active:
            return
        caret = self.session.caret
        previous = caret.layout.document.text
        text = self.control.value
        start = from_utf16(text, self.control.selectionStart)
        end = from_utf16(text, self.control.selectionEnd)
        anchor, position = (end, start) if self.control.selectionDirection == 'backward' else (start, end)
        self._syncing = True
        try:
            if previous != text:
                # Apply only the changed range, preserving styles in untouched text.
                prefix = 0
                while prefix < min(len(previous), len(text)) and previous[prefix] == text[prefix]:
                    prefix += 1
                old_end, new_end = len(previous), len(text)
                while old_end > prefix and new_end > prefix and previous[old_end - 1] == text[new_end - 1]:
                    old_end -= 1
                    new_end -= 1
                selection_anchor = caret.position if caret.mark is None else caret.mark
                if sorted((selection_anchor, caret.position)) != [prefix, old_end]:
                    caret.mark = prefix
                    caret.position = old_end
                caret.on_text(text[prefix:new_end])
            mark = None if anchor == position else anchor
            if caret.mark != mark:
                caret.mark = mark
            if caret.position != position:
                caret.position = position
        finally:
            self._syncing = False
        self.session.update()

    def _on_input(self, event: InputEvent) -> None:
        if not event.isComposing:
            self.read()

    def _on_geometry(self, event: Event) -> None:
        if self.session.active:
            self._position_control()

    def _on_selection(self, event: Event) -> None:
        if js.document.activeElement == self.control and self.control.value == self.session.caret.layout.document.text:
            self.read()

    def _on_composition_start(self, event: Event) -> None:
        self._composing = True
        self._composition_text = self.session.caret.layout.document.text

    def _on_composition_end(self, event: Event) -> None:
        self._composing = False
        self._composition_text = None
        self.read()

    def _on_blur(self, event: Event) -> None:
        # Leave focus with the page element the user chose. Do not refocus the canvas.
        self.session.close()

    def _on_key_down(self, event: KeyboardEvent) -> None:
        if event.isComposing or self._composing:
            return
        if event.key == 'Escape':
            event.preventDefault()
            self.session.close()
        elif event.key == 'Enter' and not self.session.caret.layout.multiline:
            event.preventDefault()
            self.session.perform_action()
            if self.session.options.enter_action == 'done':
                self.session.close()
