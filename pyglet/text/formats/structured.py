#!/usr/bin/env python

'''Base class for structured (hierarchical) document formats.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import pyglet

class StructuredTextDecoder(pyglet.text.DocumentDecoder):
    def decode(self, text, path=None):
        self.len_text = 0
        self.current_style = {}
        self.next_style = {}
        self.stack = []
        self.document = pyglet.text.document.FormattedDocument()
        self.decode_structured(text, path)
        return self.document

    def decode_structured(self, text, path):
        raise NotImplementedError('abstract') 

    def push_style(self, key, styles):
        old_styles = {}
        for name in styles.keys():
            old_styles[name] = self.current_style.get(name)
        self.stack.append((key, old_styles))
        self.current_style.update(styles)
        self.next_style.update(styles)

    def pop_style(self, key):
        # Don't do anything if key is not in stack
        for match, _ in self.stack:
            if key == match:
                break
        else:
            return

        # Remove all innermost elements until key is closed.
        while True:
            match, old_styles = self.stack.pop()
            self.next_style.update(old_styles)
            self.current_style.update(old_styles)
            if match == key:
                break

    def add_text(self, text):
        self.document.insert_text(self.len_text, text, self.next_style)
        self.next_style.clear()
        self.len_text += len(text)

    def add_element(self, element):
        self.document.insert_element(self.len_text, element, self.next_style)
        self.next_style.clear()
        self.len_text += 1
