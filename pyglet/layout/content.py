#!/usr/bin/env python

'''Describes document content (element) tree.  

Use a module from pyglet.layout.builders to create the tree.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.layout.css import SelectableElement, parse_style_declaration_set

__all__ = ['Document',
           'DocumentListener',
           'ContentElement', 
           'AnonymousElement',
           'AnonymousTextElement', 
          ]

class DocumentListener(object):
    def on_set_root(self, root):
        pass

    def on_element_modified(self, element):
        pass

    def on_element_style_modified(self, element):
        pass


class Document(object):
    root = None
    stylesheets = ()
    title = ''

    def __init__(self):
        self.stylesheets = []
        self.listeners = []

    def add_listener(self, listener):
        self.listeners.append(listener)

    def remove_listener(self, listener):
        self.listeners.remove(listener)

    def set_root(self, root):
        self.root = root
        for l in self.listeners:
            l.on_set_root(root)

    def element_modified(self, element):
        '''Notify that an element's children or text have changed.
        '''
        for l in self.listeners:
            l.on_element_modified(element)

    def element_style_modified(self, element):
        '''Notify that the element's style has changed.
        '''
        for l in self.listeners:
            l.on_element_style_modified(element)

class ContentElement(SelectableElement):
    # Either there are children or text; not both.  AnonymousTextElements
    # are created where necessary.
    children = ()
    text = ''

    is_anonymous = False
    element_declaration_set = None      # style from style attribute
    intrinsic_declaration_set = None    # style on HTML presentation elements
    frame = None

    def __init__(self, name, attributes, parent, previous_sibling):
        self.name = name
        self.attributes = attributes
        self.parent = parent
        self.previous_sibling = previous_sibling

    def add_child(self, element):
        if self.text:
            # Anonymous inline boxes, 9.2.2.1
            anon = AnonymousTextElement(self.text, self, None)
            self.text = None
            self.children = [anon, element]
        elif not self.children:
            self.children = [element]
        else:
            self.children.append(element)

    def add_text(self, text):
        if self.children and type(self.children[-1]) == AnonymousTextElement:
            self.children[-1].add_text(text)
        elif self.children:
            # Anonymous inline boxes, 9.2.2.1
            anon = AnonymousTextElement(text, self, self.children[-1])
            self.children.append(anon)
        else:
            self.text += text

    def set_element_style(self, style):
        self.element_declaration_set = parse_style_declaration_set(style)

    def pprint(self, indent=''):
        import textwrap
        print '\n'.join(textwrap.wrap(repr(self), 
                                      initial_indent=indent,
                                      subsequent_indent=indent))
        for child in self.children:
            child.pprint(indent + '  ')
        if self.text:
            print '\n'.join(textwrap.wrap(repr(self.text),
                                          initial_indent=(indent+'  '),
                                          subsequent_indent=(indent+'  ')))

class AnonymousElement(ContentElement):
    is_anonymous = True
    attributes = {}

    def __init__(self, parent):
        self.parent = parent
        self.computed_properties = {}

    def short_repr(self):
        return '<%s>' % self.__class__.__name__

    def __repr__(self):
        return '<%s>(parent=%s)' % \
            (self.__class__.__name__, self.parent.short_repr())
                                

class AnonymousTextElement(AnonymousElement):
    def __init__(self, text, parent, previous_sibling):
        self.text = text
        self.parent = parent
        self.previous_sibling = previous_sibling
        self.computed_properties = {}

    def add_child(self, element):
        assert False, "Can't add child to text element."

    def add_text(self, text):
        self.text += text


