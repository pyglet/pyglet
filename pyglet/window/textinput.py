"""Text input sessions and platform support for pyglet windows."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, Literal

from pyglet.customtypes import WindowT
from pyglet.event import EventDispatcher

if TYPE_CHECKING:
    from collections.abc import Callable
    from pyglet.text.caret import Caret


@dataclass(frozen=True)
class TextInputOptions:
    """Hints for a platform keyboard. These do not validate or mask text.

    ``screen_keyboard`` defaults to ``'auto'``, leaving activation to platform
    policy. ``'show'`` requests a software keyboard when available. ``'hide'``
    suppresses that request. These are preferences, not visibility guarantees.
    """

    input_type: Literal['text', 'numeric', 'decimal', 'tel', 'email', 'url', 'search'] = 'text'
    enter_action: Literal['done', 'next', 'go', 'search', 'send', 'newline'] = 'done'
    password: bool = False
    screen_keyboard: Literal['auto', 'show', 'hide'] = 'auto'


class TextInputSession(EventDispatcher):
    """Keep an editor connected to the system's text input.

    Backends use ``caret.layout.document`` for text and the caret's ``position``
    and ``mark`` for selection. The layout also supplies its multiline setting.
    Edits go through those existing APIs. The session
    stores no duplicate text, selection, or composition model.

    The session listens for changes to the caret and updates the platform's
    text field automatically. Call :meth:`update` when other things change,
    such as an application camera that moves the editor on screen.

    Use ``push_handlers`` or ``@session.event`` to listen for ``on_update``,
    ``on_action``, and ``on_close``. These events report changes after the
    window callbacks run. Handling an event does not cancel window cleanup.
    ``get_caret_rect`` can supply window-space bounds as ``(x, y, width, height)``,
    with an origin at the bottom left. A callback allows the application to
    account for its camera and layout transforms. Otherwise, bounds come from
    ``caret.rect``.

    This class does not open a keyboard or implement composition. Those require
    platform input integration with the existing text editor.
    """

    _caret: Caret
    _options: TextInputOptions
    _active: bool
    _get_caret_rect: Callable[[], tuple[float, float, float, float] | None] | None
    _on_update: Callable[[TextInputSession], None] | None
    _on_close: Callable[[TextInputSession], None] | None
    _on_action: Callable[[str], None] | None

    def __init__(self, caret: Caret, options: TextInputOptions | None = None, *,
                 get_caret_rect: Callable[[], tuple[float, float, float, float] | None] | None = None,
                 on_update: Callable[[TextInputSession], None] | None = None,
                 on_close: Callable[[TextInputSession], None] | None = None,
                 on_action: Callable[[str], None] | None = None) -> None:
        super().__init__()
        self._caret = caret
        self._options = options or TextInputOptions()
        self._active = True
        self._get_caret_rect = get_caret_rect
        self._on_update = on_update
        self._on_close = on_close
        self._on_action = on_action
        caret.push_handlers(on_change=self._on_caret_change)

    @property
    def caret(self) -> Caret:
        return self._caret

    @property
    def options(self) -> TextInputOptions:
        return self._options

    @property
    def active(self) -> bool:
        return self._active

    @property
    def caret_rect(self) -> tuple[float, float, float, float]:
        """The caret's bounds, optionally overridden for application transforms."""
        if self._get_caret_rect is not None:
            bounds = self._get_caret_rect()
            if bounds is not None:
                return bounds
        return self._caret.rect

    def _require_active(self) -> None:
        if not self._active:
            raise RuntimeError('Text input session has ended.')

    def _on_caret_change(self) -> None:
        if self._active:
            self.update()

    def update(self) -> None:
        """Update the platform's text field and notify listeners."""
        self._require_active()
        if self._on_update is not None:
            self._on_update(self)
        if self._active:
            self.dispatch_event('on_update')

    def perform_action(self) -> None:
        """Notify the application that the user requested search, next, or another action.

        Call this after the user confirms any character or word they were choosing.
        """
        self._require_active()
        if self._on_action is not None:
            self._on_action(self.options.enter_action)
        self.dispatch_event('on_action', self.options.enter_action)

    def close(self) -> None:
        """End text input, stop listening to caret changes, and notify listeners."""
        if not self._active:
            return
        self._active = False
        self._caret.remove_handlers(on_change=self._on_caret_change)
        if self._on_close is not None:
            self._on_close(self)
        self.dispatch_event('on_close')

    def on_update(self) -> None:
        """The editor or its position changed and the window was notified."""

    def on_action(self, action: str) -> None:
        """The user requested an action such as search, next, or done."""

    def on_close(self) -> None:
        """Text input ended and the window finished its cleanup."""


TextInputSession.register_event_type('on_update')
TextInputSession.register_event_type('on_action')
TextInputSession.register_event_type('on_close')


class AbstractTextInput(ABC, Generic[WindowT]):
    """Provide text input for an editor on a particular platform.

    The window calls :meth:`start` when editing begins and :meth:`close` when
    editing ends. It calls :meth:`sync` to keep the system's text field up to
    date as the editor changes.

    Call :meth:`read` when the user changes text or selection in the system's
    text field. Use the session's caret to pass those changes back to the editor.

    Native selection offsets may use UTF-16 code units. Convert them to and
    from the caret's Python string positions at the platform boundary. Guard
    synchronization against callbacks triggered by your own updates, and avoid
    also applying native edits through legacy keyboard events. Confirming an
    IME composition must not submit the field via ``session.perform_action()``.
    """

    window: WindowT
    session: TextInputSession

    def __init__(self, window: WindowT, session: TextInputSession) -> None:
        self.window = window
        self.session = session

    @abstractmethod
    def start(self) -> None:
        """Set up text input and give the editor keyboard focus."""

    @abstractmethod
    def sync(self) -> None:
        """Update the system's text field to match the editor's text, selection, and cursor position."""

    @abstractmethod
    def read(self) -> None:
        """Copy text and selection changes from the system's text field to the editor.

        If the user is still choosing a character or word, wait until they
        confirm it before copying the changes.
        """

    @abstractmethod
    def close(self) -> None:
        """Clean up the text field and its event handlers.

        Calling this again after cleanup should do nothing.
        """
