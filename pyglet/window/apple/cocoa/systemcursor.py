from __future__ import annotations

from pyglet.libs.darwin import cocoapy


# This class is a wrapper around NSCursor which prevents us from
# sending too many hide or unhide messages in a row.  Apparently
# NSCursor treats them like retain/release messages, which can be
# problematic when we are e.g. switching between window & fullscreen.
class SystemCursor:
    cursor_is_hidden = False

    @classmethod
    def hide(cls) -> None:  # noqa: ANN102
        if not cls.cursor_is_hidden:
            cocoapy.send_message('NSCursor', 'hide')
            cls.cursor_is_hidden = True

    @classmethod
    def unhide(cls) -> None:  # noqa: ANN102
        if cls.cursor_is_hidden:
            cocoapy.send_message('NSCursor', 'unhide')
            cls.cursor_is_hidden = False
