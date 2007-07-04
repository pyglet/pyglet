#!/usr/bin/env python

'''Describes document content (element) tree.  

Use a module from layout.builders to create the tree.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from layout.css import *

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
        self.element_ids = {}

    def add_listener(self, listener):
        self.listeners.append(listener)

    def remove_listener(self, listener):
        self.listeners.remove(listener)

    def set_root(self, root):
        self.root = root
        for l in self.listeners:
            l.on_set_root(root)

    def get_element(self, id):
        return self.element_ids.get(id, None)

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

class ContentElementStyle(object):
    '''The style of an element is proxied by this class, which provides
    a friendly dict-like interface for changing properties.
    '''

    __slots__ = ['element']

    def __init__(self, element):
        self.element = element

    def __getitem__(self, key):
        if not self.element.element_declaration_set:
            return None
        for decl in self.element.element_declaration_set.declarations:
            if decl.property == key:
                return ''.join([str(v) for v in decl.values])

    def __setitem__(self, key, value):
        element = self.element
        if element.element_declaration_set:
            declarations = \
                [d for d in element.element_declaration_set.declarations \
                 if d.property != key] 
        else:
            declarations = []

        if type(value) in (str, unicode):
            value = parse_style_expression(value)
        elif type(value) != list:
            value = [list]

        decl = Declaration(key, value, None)
        declarations.append(decl)

        # XXX Can't reuse old DeclarationSet because there is already a
        # StyleNode that uses it.  Unfortunately this can mean we leak
        # memory as the StyleTree retains a reference to a potentially
        # unused node.  This will build incrementally for all changes
        # to element style.  One solution could be to maintain a declaration
        # set cache.
        element.element_declaration_set = DeclarationSet(declarations)

        element.document.element_style_modified(element)

    def __delitem__(self, key):
        element = self.element
        if element.element_declaration_set:
            element.element_declaration_set = DeclarationSet(
                [d for d in element.element_declaration_set.declarations \
                 if d.property != key]) 
        element.document.element_style_modified(element)

    def __contains__(self, key):
        element = self.element
        if not element.element_declaration_set:
            return False
        return len([d for d in element.element_declaration_set.declarations \
                    if d.property == key]) != 0
 
    def __str__(self):
        if not self.element.element_declaration_set:
            return ''
        return '; '.join([str(d) for d in \
                          self.element.element_declaration_set.declarations])

class ContentElement(SelectableElement):
    # Either there are children or text; not both.  AnonymousTextElements
    # are created where necessary.
    children = ()
    text = ''

    is_anonymous = False
    element_declaration_set = None      # style from style attribute
    intrinsic_declaration_set = None    # style on HTML presentation elements
    frame = None

    def __init__(self, document, name, attributes, parent, previous_sibling):
        self.document = document
        self.name = name
        self.parent = parent
        self.previous_sibling = previous_sibling

        # Make attributes more like a dict
        #self.attributes = attributes
        self.attributes = {}
        for key, value in attributes.items():
            self.attributes[key] = value

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
        self.document.element_modified(self)

    def add_text(self, text):
        if self.children and type(self.children[-1]) == AnonymousTextElement:
            self.children[-1].add_text(text)
        elif self.children:
            # Anonymous inline boxes, 9.2.2.1
            anon = AnonymousTextElement(text, self, self.children[-1])
            self.children.append(anon)
        else:
            self.text += text
        self.document.element_modified(self)

    def set_element_style(self, style):
        self.element_declaration_set = parse_style_declaration_set(style)
        self.document.element_style_modified(self)

    style = property(lambda self: ContentElementStyle(self),
                     set_element_style)
        
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


