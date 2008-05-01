#!/usr/bin/python
# $Id:$

from docutils.core import publish_doctree
from docutils import nodes

import pyglet
from pyglet.text.formats import structured

class Stylesheet(object):
    default = dict(
        font_name='Times New Roman',
        font_size=12,
        margin_bottom=12)

    emphasis = dict(
        italic=True)
        
    strong = dict(
        bold=True)

    literal = dict(
        font_name='Courier New')

    literal_block = dict(
        font_name='Courier New',
        font_size=10,
        margin_left=20,
        )

    def get_title(self, level):
        return {
            0: dict(
                font_size=24,
                bold=True,
                align='center'),
            1: dict(
                font_size=16,
                bold=True),
            2: dict(
                font_size=14,
                bold=True),
            3: dict(
                font_size=12,
                italic=True),
        }.get(level, {})

class Section(object):
    def __init__(self, level):
        self.level = level

class DocutilsDecoder(structured.StructuredTextDecoder):
    def __init__(self, stylesheet=None):
        if not stylesheet:
            stylesheet = Stylesheet()
        self.stylesheet = stylesheet

    def decode_structured(self, text, location):
        self.location = location
        if isinstance(location, pyglet.resource.FileLocation):
            doctree = publish_doctree(text, source_path=location.path)
        else:
            doctree = publish_doctree(text)
        self.decode_doctree(doctree)

    def decode_doctree(self, doctree):
        self.push_style('_default', self.stylesheet.default)
        self.section_stack = [Section(0)]
        self.in_literal = False

        doctree.walkabout(DocutilsVisitor(doctree, self))

    def visit_Text(self, node):
        text = node.astext()
        if self.in_literal:
            text = text.replace('\n', u'\u2028')
        self.add_text(text)

    def visit_unknown(self, node):
        pass

    def depart_unknown(self, node):
        pass

    # Structural elements

    def visit_title(self, node):
        level = self.section_stack[-1].level
        self.push_style(node, self.stylesheet.get_title(level))

    def depart_title(self, node):
        self.add_text('\n')

    def visit_section(self, node):
        self.section_stack.append(Section(len(self.section_stack)))

    def depart_section(self, node):
        self.section_stack.pop()

    # Body elements

    def depart_paragraph(self, node):
        self.add_text('\n')

    def visit_literal_block(self, node):
        self.push_style(node, self.stylesheet.literal_block)
        self.in_literal = True

    def depart_literal_block(self, node):
        self.in_literal = False
        self.add_text('\n')

    # Inline elements
    def visit_emphasis(self, node):
        self.push_style(node, self.stylesheet.emphasis)

    def visit_strong(self, node):
        self.push_style(node, self.stylesheet.strong)
        
    def visit_literal(self, node):
        self.push_style(node, self.stylesheet.literal)

    def visit_superscript(self, node):
        self.push_style(node, self.stylesheet.superscript)

    def visit_subscript(self, node):
        self.push_style(node, self.stylesheet.subscript)

class DocutilsVisitor(nodes.NodeVisitor):
    def __init__(self, document, decoder):
        nodes.NodeVisitor.__init__(self, document)
        self.decoder = decoder

    def dispatch_visit(self, node):
        node_name = node.__class__.__name__
        method = getattr(self.decoder, 'visit_%s' % node_name,
                         self.decoder.visit_unknown)
        method(node)

    def dispatch_departure(self, node):
        self.decoder.pop_style(node)

        node_name = node.__class__.__name__
        method = getattr(self.decoder, 'depart_%s' % node_name, 
                         self.decoder.depart_unknown)
        method(node)

