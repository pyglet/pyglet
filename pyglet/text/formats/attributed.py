#!/usr/bin/env python

'''Extensible attributed text format for representing pyglet formatted
documents.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import re

from pyglet.text import document

_pattern = re.compile(r'''
    (?P<escape_hex>\{\#x(?P<escape_hex_val>[0-9a-fA-F]+)\})
  | (?P<escape_dec>\{\#(?P<escape_dec_val>[0-9]+)\})
  | (?P<escape_lbrace>\{\[\})
  | (?P<escape_rbrace>\{\]\})
  | (?P<attr_true>\{(?P<attr_true_name>[^ ]+)\s+True\})
  | (?P<attr_false>\{(?P<attr_false_name>[^ ]+)\s+False\})
  | (?P<attr_str1>\{
        (?P<attr_str1_name>[^ ]+)\s+
        "(?P<attr_str1_val>[^"]*)"\})
  | (?P<attr_str2>\{
        (?P<attr_str2_name>[^ ]+)\s+
        '(?P<attr_str2_val>[^']*)'\})
  | (?P<attr_int>\{
        (?P<attr_int_name>[^ ]+)\s+
        (?P<attr_int_val>[0-9]+)\})
  | (?P<attr_float>\{
        (?P<attr_float_name>[^ ]+)\s+
        (?P<attr_float_val>
            ([0-9]+\.[0-9]*|[0-9]*\.[0-9]+)
        )\})
  | (?P<nl_hard1>\n(?=[ \t]))
  | (?P<nl_hard2>\{\}\n)
  | (?P<nl_soft>\n(?=\S))
  | (?P<nl_para>\n\n+)
  | (?P<text>[^{\n]+)
    ''', re.VERBOSE | re.DOTALL)

class AttributedTextDecoder(object):
    def decode(self, text):
        self.doc = document.FormattedDocument()

        self.length = 0
        self.attributes = {}
        self.trailing_space = False

        for m in _pattern.finditer(text):
            group = m.lastgroup
            if group == 'text':
                self.append(m.group('text'))
                self.trailing_space = text.endswith(' ')
            elif group == 'nl_soft':
                if not self.trailing_space:
                    self.append(' ')
            elif group in ('nl_hard1', 'nl_hard2'):
                self.append('\n')
            elif group == 'nl_para':
                self.append(m.group('nl_para'))
            elif group == 'attr_float':
                self.attributes[m.group('attr_float_name')] = \
                    float(m.group('attr_float_val'))
            elif group == 'attr_int':
                self.attributes[m.group('attr_int_name')] = \
                    int(m.group('attr_int_val'))
            elif group == 'attr_str1':
                self.attributes[m.group('attr_str1_name')] = \
                    m.group('attr_str1_val')
            elif group == 'attr_str2':
                self.attributes[m.group('attr_str2_name')] = \
                    m.group('attr_str2_val')
            elif group == 'attr_false':
                self.attributes[m.group('attr_false_name')] = False
            elif group == 'attr_true':
                self.attributes[m.group('attr_true_name')] = True
            elif group == 'escape_dec':
                self.append(unichr(int(m.group('escape_dec_val'))))
            elif group == 'escape_hex':
                self.append(unichr(int(m.group('escape_hex_val'), 16)))
            elif group == 'escape_lbrace':
                self.append('{')
            elif group == 'escape_rbrace':
                self.append('}')

        return self.doc

    def append(self, text):
        self.doc.insert_text(self.length, text, self.attributes)
        self.length += len(text)
        self.attributes.clear()
        self.trailing_space = False

