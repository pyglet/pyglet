#!/usr/bin/env python

'''Content tree builders.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from layout.content import *

class ContentBuilder(object):
    element_class = ContentElement

    def __init__(self, document):
        self.document = document
        self.parent_stack = [None]
        self.sibling_stack = [None]

    def feed(self, data):
        raise NotImplementedError('abstract')

    def begin_element(self, name, attributes):
        parent = self.parent_stack[-1]
        previous_sibling = self.sibling_stack.pop()
        element = self.element_class(
            self.document, name, attributes, parent, previous_sibling)
        if parent:
            parent.add_child(element)
            self.document.element_modified(parent)
        else:
            self.document.set_root(element)

        self.parent_stack.append(element)
        self.sibling_stack.append(element)
        self.sibling_stack.append(None)
        if element.id:
            self.document.element_ids[element.id] = element

    def end_element(self, name):
        self.parent_stack.pop()
        self.sibling_stack.pop()

    def text(self, text):
        if self.document.root:
            self.parent_stack[-1].add_text(text)
            self.document.element_modified(self.parent_stack[-1])

