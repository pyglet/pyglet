#!/usr/bin/env python

'''Build content tree from HTML source.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from HTMLParser import HTMLParser
from htmlentitydefs import entitydefs

from layout.content import *
from layout.css import *
from layout.builders import *
from layout.builders.htmlstylesheet import *
from layout.builders.xhtmlbuilder import *

__all__ = ['HTMLElement', 'HTMLBuilder']

class HTMLElement(ContentElement):
    font_sizes = {
        '1': Ident('xx-small'),
        '2': Ident('small'),
        '3': Ident('medium'),
        '4': Ident('large'),
        '5': Ident('x-large'),
        '6': Ident('xx-large'),
        '7': Ident('xx-large'),
        '-6': Dimension('0.2em'),
        '-5': Dimension('0.2em'),
        '-4': Dimension('0.2em'),
        '-3': Dimension('0.4em'),
        '-2': Dimension('0.6em'),
        '-1': Dimension('0.8em'),
        '+0': Dimension('1em'),     # TODO: twiddle these to good effect
        '+1': Dimension('1.2em'),
        '+2': Dimension('1.4em'),
        '+3': Dimension('1.6em'),
        '+4': Dimension('1.8em'),
        '+5': Dimension('2.0em'),
        '+6': Dimension('2.2em'),
    }
    
    def __init__(self, document, name, attributes, parent, previous_sibling):
        super(HTMLElement, self).__init__(
            document, name, attributes, parent, previous_sibling)
        if attributes.has_key('id'):
            self.id = attributes['id']
        if attributes.has_key('class'):
            self.classes = attributes['class'].lower().split()
        if attributes.has_key('style'):
            self.set_element_style(attributes['style'])

        # Apply CSS to HTML presentation elements
        if name == 'font':
            declarations = []
            if 'size' in attributes:
                size = self.font_sizes.get(attributes['size'], 'medium')
                declarations.append(
                    Declaration('font-size', [size], None))
            if 'face' in attributes:
                faces = []
                for face in attributes['face'].split(','):
                    faces.append(Ident(face.strip()))
                    faces.append(Delim(','))
                declarations.append(
                    Declaration('font-family', faces, None))
            if 'color' in attributes:
                if attributes['color'][:1] == '#':
                    color = Hash(attributes['color'])
                else:
                    color = Ident(attributes['color'])
                declarations.append(
                    Declaration('color', [color], None))
            self.intrinsic_declaration_set = DeclarationSet(declarations)

class DTDElement(object):
    ANY = ()
    NONE = []  # dirty trick
    parent = None
    def __init__(self, name, children=NONE):
        self.name = name
        self.children = children
        for child in self.children:
            child.parent = self

    def apply_missing_start_tags(self, name, parser):
        # Construct path to 'name' from here.
        path = self.get_path(name)
        if path is None:
            path = self.get_default_path()
        if path and path[0][0]:
            # First path is self if open
            path = path[1:]
        for (open, child) in path: 
            if open:
                if child.name != name:
                    parser.handle_starttag(child.name, (), use_dtd=False)
                parser.current_dtd = child
            else:
                parser.handle_endtag(child.name)
                parser.current_dtd = parser.current_dtd.parent

    def get_path(self, name, skip=None, recurse_up=True):
        if name == self.name:
            return [(True, self)]
        for child in self.children:
            if child is skip:
                continue
            path = child.get_path(name, recurse_up=False)
            if path is not None:
                return [(True, self)] + path
        if self.parent and recurse_up:
            path = self.parent.get_path(name, self)
            if path:
                if path[0][0]:
                    path = path[1:]
                return [(False, self)] + path

    def get_default_path(self, skip=None, recurse_up=True):
        if self.children is self.ANY:
            return [(True, self)]
        for child in self.children:
            if child is skip:
                continue
            path = child.get_default_path(recurse_up=False)
            if type(path) == list:
                return [(True, self)] + path
        if recurse_up:
            if not self.parent:
                assert False, 'No default DTD path found'
            path = self.parent.get_default_path(self)
            if path[0][0]:
                path = path[1:]
            return [(False, self)] + path

    def __repr__(self):
        return 'DTD(%s)' % self.name

class HTMLBuilderParser(HTMLParser):
    # Rough DTD is used to close and open tags to "get to" the required
    # element.  For example, if the document is::
    #
    #    <title>My pie</title>
    #    <p>My pie is nice.</p>
    #
    # the builder will receive these tags instead::
    #
    #    <html>
    #      <head>
    #        <title>My pie</title>
    #      </head>
    #      <body>
    #        <p>My pie is nice.</p>
    #      
    #  (the final body and html tags are closed in the 'close' method).
    dtd = DTDElement(None, [ 
            DTDElement('html', [
              DTDElement('head', [
                DTDElement('base'),
                DTDElement('link'),
                DTDElement('meta'),
                DTDElement('object'),
                DTDElement('script'),
                DTDElement('style'),
                DTDElement('title'),
              ]),
              DTDElement('body', DTDElement.ANY),
            ])
          ])

    # List of elements in which a start-tag also closes the element of the
    # same name.  (e.g. a <P> can close a <P>, but nothing else).
    # This list is actually just the list of all elements that have optional
    # end tags (http://www.w3.org/TR/html4/index/elements.html); some
    # are meaningless in this list (e.g. <HTML>) but do no harm for valid
    # HTML.
    force_close = set([
        'body', 'colgroup', 'dd', 'dt', 'head', 'html', 'li', 'option',
        'p', 'tbody', 'td', 'tfoot', 'th', 'thead', 'tr'])
        
    # List of elements that must have no content (assumed closed as soon as
    # open tag is encountered). 
    force_empty = set([
        'area', 'base', 'basefont', 'br', 'col', 'frame', 'hr', 'img',
        'input', 'isindex', 'link', 'meta', 'param'])

    def __init__(self, builder):
        HTMLParser.__init__(self)
        self.builder = builder
        self.tag_stack = [None]
        self.current_dtd = self.dtd

    def close(self):
        HTMLParser.close(self)

        # Close any open elements
        for tag in self.tag_stack[::-1]:
            self.handle_endtag(tag)

    def handle_starttag(self, tag, attrs, use_dtd=True):
        if tag == 'html':
            import pdb
            #pdb.set_trace()
        # Convert attrs to a dict
        a = {}
        for key, value in attrs:
            if key in ('class', 'id'):
                value = value.lower()
            a[key] = value
        attrs = a

        # Check DTD for missing start tags
        if use_dtd and self.current_dtd.children is not DTDElement.ANY:
            self.current_dtd.apply_missing_start_tags(tag, self)

        # Close element of same tag name if required
        if tag in self.force_close and self.tag_stack[-1] == tag:
            self.handle_endtag(tag)

        self.tag_stack.append(tag)
        self.builder.begin_element(tag, attrs)

        # Insert close tag if required
        if tag in self.force_empty:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        # Search up tag stack and close all open elements iff this tag is 
        # in the stack.
        if tag in self.tag_stack:
            for t in self.tag_stack[::-1]:
                if t == tag:
                    break
                self.handle_endtag(t)
        
            assert self.tag_stack[-1] == tag
            self.tag_stack.pop()

            self.builder.end_element(tag)
            if self.current_dtd.name == tag:
                self.current_dtd = self.current_dtd.parent

    def handle_data(self, data):
        # Special case: no tags before text data, assume <body>
        if self.current_dtd is self.dtd:
            self.handle_starttag('body', ())
        self.builder.text(data)

    def handle_charref(self, name):
        raise NotImplementedError('charref')

    def handle_entityref(self, name):
        self.builder.text(entitydefs.get(name, ''))

class HTMLBuilder(XHTMLBuilder):
    element_class = HTMLElement

    def __init__(self, document):
        super(HTMLBuilder, self).__init__(document)
        self.document.stylesheets.append(html4_default_stylesheet)
        self.parser = HTMLBuilderParser(self)

    def feed(self, data):
        self.parser.feed(data)

    def close(self):
        self.parser.close()

