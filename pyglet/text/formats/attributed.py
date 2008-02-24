#!/usr/bin/env python

'''Extensible attributed text format for representing pyglet formatted
documents.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import operator
import parser
import re
import symbol
import token

import pyglet

_pattern = re.compile(r'''
    (?P<escape_hex>\{\#x(?P<escape_hex_val>[0-9a-fA-F]+)\})
  | (?P<escape_dec>\{\#(?P<escape_dec_val>[0-9]+)\})
  | (?P<escape_lbrace>\{\{)
  | (?P<escape_rbrace>\}\})
  | (?P<attr>\{
        (?P<attr_name>[^ \{\}]+)\s+
        (?P<attr_val>[^\}]+)\})
  | (?P<nl_hard1>\n(?=[ \t]))
  | (?P<nl_hard2>\{\}\n)
  | (?P<nl_soft>\n(?=\S))
  | (?P<nl_para>\n\n+)
  | (?P<text>[^\{\}\n]+)
    ''', re.VERBOSE | re.DOTALL)

class AttributedTextDecoder(pyglet.text.DocumentDecoder):
    def decode(self, text, path=None):
        self.doc = pyglet.text.document.FormattedDocument()

        self.length = 0
        self.attributes = {}
        next_trailing_space = True
        trailing_newline = True

        for m in _pattern.finditer(text):
            group = m.lastgroup
            trailing_space = True
            if group == 'text':
                t = m.group('text')
                self.append(t)
                trailing_space = t.endswith(' ')
                trailing_newline = False
            elif group == 'nl_soft':
                if not next_trailing_space:
                    self.append(' ')
                trailing_newline = False
            elif group in ('nl_hard1', 'nl_hard2'):
                self.append('\n')
                trailing_newline = True
            elif group == 'nl_para':
                self.append(m.group('nl_para'))
                trailing_newline = True
            elif group == 'attr':
                try:
                    ast = parser.expr(m.group('attr_val'))
                    if self.safe(ast):
                        val = eval(ast.compile())
                    else:
                        val = None
                except (parser.ParserError, SyntaxError):
                    val = None
                name = m.group('attr_name')
                if name[0] == '.':
                    if trailing_newline:
                        self.attributes[name[1:]] = val
                    else:
                        self.doc.set_paragraph_style(self.length, self.length, 
                                                     {name[1:]: val})
                else:
                    self.attributes[name] = val
            elif group == 'escape_dec':
                self.append(unichr(int(m.group('escape_dec_val'))))
            elif group == 'escape_hex':
                self.append(unichr(int(m.group('escape_hex_val'), 16)))
            elif group == 'escape_lbrace':
                self.append('{')
            elif group == 'escape_rbrace':
                self.append('}')
            next_trailing_space = trailing_space

        return self.doc

    def append(self, text):
        self.doc.insert_text(self.length, text, self.attributes)
        self.length += len(text)
        self.attributes.clear()

    _safe_names = ('True', 'False', 'None')

    def safe(self, ast):
        tree = ast.totuple()
        return self.safe_node(tree)

    def safe_node(self, node):
        if token.ISNONTERMINAL(node[0]):
            return reduce(operator.and_, map(self.safe_node, node[1:]))
        elif node[0] == token.NAME:
            return node[1] in self._safe_names
        else:
            return True
