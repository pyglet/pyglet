#!/usr/bin/env python

'''Plain text decoder.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import pyglet

class PlainTextDecoder(pyglet.text.DocumentDecoder):
    def decode(self, text, path=None):
        document = pyglet.text.document.UnformattedDocument()
        document.insert_text(0, text)
        return document
