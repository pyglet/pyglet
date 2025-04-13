"""Extensible attributed text format for representing pyglet formatted documents."""
from __future__ import annotations

import ast
import re
from typing import TYPE_CHECKING

import pyglet

if TYPE_CHECKING:
    from pyglet.resource import Location

_pattern = re.compile(r"""
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
    """, re.VERBOSE | re.DOTALL)


class AttributedTextDecoder(pyglet.text.DocumentDecoder):  # noqa: D101

    def __init__(self) -> None:  # noqa: D107
        self.doc = pyglet.text.document.FormattedDocument()
        self.length = 0
        self.attributes = {}

    def decode(self, text: str, location: Location | None = None) -> pyglet.text.document.FormattedDocument:  # noqa: ARG002
        next_trailing_space = True
        trailing_newline = True

        for m in _pattern.finditer(text):
            group = m.lastgroup
            trailing_space = True
            if group == "text":
                t = m.group("text")
                self.append(t)
                trailing_space = t.endswith(" ")
                trailing_newline = False
            elif group == "nl_soft":
                if not next_trailing_space:
                    self.append(" ")
                trailing_newline = False
            elif group in ("nl_hard1", "nl_hard2"):
                self.append("\n")
                trailing_newline = True
            elif group == "nl_para":
                self.append(m.group("nl_para")[1:])  # ignore the first \n
                trailing_newline = True
            elif group == "attr":
                value = ast.literal_eval(m.group("attr_val"))
                name = m.group("attr_name")
                if name[0] == ".":
                    if trailing_newline:
                        self.attributes[name[1:]] = value
                    else:
                        self.doc.set_paragraph_style(self.length, self.length, {name[1:]: value})
                else:
                    self.attributes[name] = value
            elif group == "escape_dec":
                self.append(chr(int(m.group("escape_dec_val"))))
            elif group == "escape_hex":
                self.append(chr(int(m.group("escape_hex_val"), 16)))
            elif group == "escape_lbrace":
                self.append("{")
            elif group == "escape_rbrace":
                self.append("}")
            next_trailing_space = trailing_space

        return self.doc

    def append(self, text: str) -> None:
        self.doc.insert_text(self.length, text, self.attributes)
        self.length += len(text)
        self.attributes.clear()
