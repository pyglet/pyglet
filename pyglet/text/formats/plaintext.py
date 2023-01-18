"""Plain text decoder.
"""

import pyglet


class PlainTextDecoder(pyglet.text.DocumentDecoder):
    def decode(self, text, location=None):
        document = pyglet.text.document.UnformattedDocument()
        document.insert_text(0, text)
        return document
