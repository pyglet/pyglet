from __future__ import annotations

import sys
from collections.abc import Iterator
from typing import Any, Literal

import pytest

if sys.platform != 'emscripten':
    pytest.skip('requires the Emscripten/Pyodide runtime', allow_module_level=True)

from js import CompositionEvent, Event, InputEvent, KeyboardEvent, Object, document, window as browser_window
from pyodide.ffi import to_js

from pyglet.text.caret import Caret
from pyglet.text.document import FormattedDocument
from pyglet.window.textinput import TextInputOptions
from pyglet.text.layout import IncrementalTextLayout
from pyglet.window import Window

Editor = tuple[Window, IncrementalTextLayout, Caret]


@pytest.fixture
def editor() -> Iterator[Editor]:
    window = Window(width=300, height=100)
    text = FormattedDocument('hello 😀 world')
    text.set_style(0, 5, {'color': (255, 0, 0, 255)})
    layout = IncrementalTextLayout(text, width=280, height=80)
    caret = Caret(layout)
    try:
        yield window, layout, caret
    finally:
        layout.end_text_input()
        caret.delete()
        layout.delete()
        window.close()


def options(**kwargs: Any) -> Any:
    return to_js(kwargs, dict_converter=Object.fromEntries)


def input_text(control: Any, text: str, position: int, composing: bool = False) -> None:
    control.value = text
    control.setSelectionRange(position, position)
    control.dispatchEvent(InputEvent.new('input', options(isComposing=composing, inputType='insertText')))


def test_native_control_updates_existing_document_and_unicode_selection(editor: Editor) -> None:
    window, layout, caret = editor
    session = layout.begin_text_input(window, caret)
    control = window._browser_text_input.control
    assert document.activeElement == control
    assert control.value == layout.document.text
    input_text(control, 'hello 🐍 world', 8)
    assert layout.document.text == 'hello 🐍 world'
    assert caret.position == 7
    assert layout.document.get_style('color', 0) == (255, 0, 0, 255)
    caret.mark = 7
    caret.position = 6
    assert (control.selectionStart, control.selectionEnd, control.selectionDirection) == (6, 8, 'backward')
    session.close()
    assert not control.isConnected
    assert window._browser_text_input is None


@pytest.mark.parametrize('policy', ['auto', 'show', 'hide'])
def test_keyboard_policy_sets_browser_input_hint(editor: Editor, policy: Literal['auto', 'show', 'hide']) -> None:
    window, layout, caret = editor
    layout.begin_text_input(window, caret, TextInputOptions(screen_keyboard=policy))
    control = window._browser_text_input.control
    assert control.inputMode == ('none' if policy == 'hide' else 'text')
    assert document.activeElement == control


def test_composition_commits_once_without_editing_document_provisionally(editor: Editor) -> None:
    window, layout, caret = editor
    layout.begin_text_input(window, caret)
    control = window._browser_text_input.control
    control.dispatchEvent(CompositionEvent.new('compositionstart'))
    input_text(control, 'hello 日本 world', 8, composing=True)
    assert layout.document.text == 'hello 😀 world'
    control.dispatchEvent(CompositionEvent.new('compositionend'))
    assert layout.document.text == 'hello 日本 world'
    control.dispatchEvent(InputEvent.new('input', options(isComposing=False)))
    assert layout.document.text == 'hello 日本 world'


def test_external_edit_during_composition_does_not_get_overwritten(editor: Editor) -> None:
    window, layout, caret = editor
    session = layout.begin_text_input(window, caret)
    control = window._browser_text_input.control
    control.dispatchEvent(CompositionEvent.new('compositionstart'))
    input_text(control, 'hello 日本 world', 8, composing=True)
    layout.document.text = 'external'
    assert not session.active
    assert not control.isConnected
    control.dispatchEvent(CompositionEvent.new('compositionend'))
    assert layout.document.text == 'external'


def test_browser_selection_changes_update_caret(editor: Editor) -> None:
    window, layout, caret = editor
    layout.begin_text_input(window, caret)
    control = window._browser_text_input.control
    control.setSelectionRange(6, 8, 'backward')
    control.dispatchEvent(Event.new('select'))
    assert (caret.mark, caret.position) == (7, 6)


def test_external_document_edits_synchronize_control(editor: Editor) -> None:
    window, layout, caret = editor
    layout.begin_text_input(window, caret)
    control = window._browser_text_input.control
    layout.document.text = 'changed'
    assert control.value == 'changed'
    caret.position = 7
    assert control.selectionStart == control.selectionEnd == 7


def test_blur_closes_session_without_stealing_page_focus(editor: Editor) -> None:
    window, layout, caret = editor
    session = layout.begin_text_input(window, caret)
    outside = document.createElement('input')
    document.body.appendChild(outside)
    try:
        outside.focus()
        assert not session.active
        assert window._browser_text_input is None
        assert document.activeElement == outside
    finally:
        outside.remove()


def test_enter_submits_single_line_and_escape_closes_without_duplicate_text(editor: Editor) -> None:
    window, layout, caret = editor
    actions: list[str] = []
    events: list[str] = []
    window.push_handlers(on_text=events.append)
    session = layout.begin_text_input(window, caret, on_action=actions.append)
    control = window._browser_text_input.control
    input_text(control, 'committed', 9)
    assert events == []
    control.dispatchEvent(KeyboardEvent.new('keydown', options(key='Enter', cancelable=True)))
    assert actions == ['done']
    assert not session.active
    session = layout.begin_text_input(window, caret)
    control = window._browser_text_input.control
    control.dispatchEvent(KeyboardEvent.new('keydown', options(key='Escape', cancelable=True)))
    assert not session.active


def test_multiline_input_uses_textarea_and_preserves_newlines(editor: Editor) -> None:
    window, layout, caret = editor
    layout.multiline = True
    layout.begin_text_input(window, caret, TextInputOptions(enter_action='newline'))
    control = window._browser_text_input.control
    assert control.tagName == 'TEXTAREA'
    input_text(control, 'line one\nline two', 17)
    assert layout.document.text == 'line one\nline two'
    assert control.enterKeyHint == 'enter'


def test_viewport_changes_refresh_native_control_position(editor: Editor) -> None:
    window, layout, caret = editor
    bounds = [10.0, 20.0, 1.0, 16.0]
    layout.begin_text_input(window, caret, get_caret_rect=lambda: (bounds[0], bounds[1], bounds[2], bounds[3]))
    control = window._browser_text_input.control
    previous_left = float(control.style.left.removesuffix('px'))
    bounds[0] += 20
    browser_window.dispatchEvent(Event.new('scroll'))
    assert float(control.style.left.removesuffix('px')) > previous_left
