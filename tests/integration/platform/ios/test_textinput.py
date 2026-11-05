"""Run inside the native iOS test host or simulator, not a browser."""
from __future__ import annotations

import sys
from collections.abc import Iterator
from typing import Literal

import pytest

if sys.platform != 'ios':
    pytest.skip('requires native UIKit on iOS', allow_module_level=True)

from pyglet.libs.darwin.cocoapy import NSRange, get_NSString
from pyglet.text.caret import Caret
from pyglet.text.document import UnformattedDocument
from pyglet.window.textinput import TextInputOptions
from pyglet.text.layout import IncrementalTextLayout
from pyglet.window import Window

Editor = tuple[Window, IncrementalTextLayout, Caret]


@pytest.fixture
def editor() -> Iterator[Editor]:
    window = Window()
    window.activate()
    layout = IncrementalTextLayout(UnformattedDocument('hello'), width=200, height=80)
    caret = Caret(layout)
    try:
        yield window, layout, caret
    finally:
        layout.end_text_input()
        caret.delete()
        layout.delete()
        window.close()


@pytest.mark.parametrize('policy', ['auto', 'show', 'hide'])
def test_native_responder_and_keyboard_policy(editor: Editor, policy: Literal['auto', 'show', 'hide']) -> None:
    window, layout, caret = editor
    session = layout.begin_text_input(window, caret, TextInputOptions(screen_keyboard=policy))
    view = window._ios_text_input.view
    assert view.isFirstResponder()
    assert bool(view.inputView()) == (policy == 'hide')
    session.close()
    assert window._ios_text_input is None


def test_uikit_edits_and_utf16_selection_reach_layout(editor: Editor) -> None:
    window, layout, caret = editor
    layout.begin_text_input(window, caret)
    controller = window._ios_text_input
    controller.view.setText_(get_NSString('hello😀'))
    controller.view.setSelectedRange_(NSRange(7, 0))
    controller.read()
    assert layout.document.text == 'hello😀'
    assert caret.position == 6
    controller.view.insertText_(get_NSString('!'))
    controller.read()
    assert layout.document.text == 'hello😀!'


def test_uikit_marked_text_commits_through_existing_caret(editor: Editor) -> None:
    window, layout, caret = editor
    layout.begin_text_input(window, caret)
    controller = window._ios_text_input
    controller.view.setMarkedText_selectedRange_(get_NSString('日本'), NSRange(2, 0))
    assert layout.document.text == 'hello'
    controller.view.unmarkText()
    assert layout.document.text == '日本hello'
