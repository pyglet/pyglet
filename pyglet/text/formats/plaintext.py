"""Plain text decoder."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pyglet

if TYPE_CHECKING:
    from pyglet.resource import Location
    from pyglet.text import UnformattedDocument


class PlainTextDecoder(pyglet.text.DocumentDecoder):  # noqa: D101
    def decode(self, text: str, location: Location | None=None) -> UnformattedDocument:  # noqa: ARG002
        document = pyglet.text.document.UnformattedDocument()
        document.append_text(text)
        return document
