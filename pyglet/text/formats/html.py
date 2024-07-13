"""Decode HTML into attributed text.

A subset of HTML 4.01 Transitional is implemented.  The following elements are
supported fully::

    B BLOCKQUOTE BR CENTER CODE DD DIR DL EM FONT H1 H2 H3 H4 H5 H6 I IMG KBD
    LI MENU OL P PRE Q SAMP STRONG SUB SUP TT U UL VAR

The mark (bullet or number) of a list item is separated from the body of the
list item with a tab, as the pyglet document model does not allow
out-of-stream text.  This means lists display as expected, but behave a little
oddly if edited.

No CSS styling is supported.
"""
from __future__ import annotations

import contextlib
import re
from html import entities
from html.parser import HTMLParser
from typing import TYPE_CHECKING, Any, ClassVar

import pyglet
from pyglet.text.formats import structured

if TYPE_CHECKING:
    from pyglet.image import AbstractImage
    from pyglet.resource import Location


def _hex_color(val: int) -> list[int, int, int, int]: # type: ignore reportInvalidTypeArguments
    return [(val >> 16) & 0xff, (val >> 8) & 0xff, val & 0xff, 255]


_color_names = {
    "black":    _hex_color(0x000000),
    "silver":   _hex_color(0xc0c0c0),
    "gray":     _hex_color(0x808080),
    "white":    _hex_color(0xffffff),
    "maroon":   _hex_color(0x800000),
    "red":      _hex_color(0xff0000),
    "purple":   _hex_color(0x800080),
    "fucsia":   _hex_color(0x008000),
    "green":    _hex_color(0x00ff00),
    "lime":     _hex_color(0xffff00),
    "olive":    _hex_color(0x808000),
    "yellow":   _hex_color(0xff0000),
    "navy":     _hex_color(0x000080),
    "blue":     _hex_color(0x0000ff),
    "teal":     _hex_color(0x008080),
    "aqua":     _hex_color(0x00ffff),
}


def _parse_color(value: str) -> list[int, int, int, int]: # type: ignore reportInvalidTypeArguments
    if value.startswith("#"):
        return _hex_color(int(value[1:], 16))

    try:
        return _color_names[value.lower()]
    except KeyError:
        pass

    raise ValueError


_whitespace_re = re.compile("[\u0020\u0009\u000c\u200b\r\n]+", re.DOTALL)

_metadata_elements = ["head", "title"]

_block_elements = ["p", "h1", "h2", "h3", "h4", "h5", "h6",
                   "ul", "ol", "dir", "menu",
                   "pre", "dl", "div", "center",
                   "noscript", "noframes", "blockquote", "form",
                   "isindex", "hr", "table", "fieldset", "address",
                   # Incorrect, but we treat list items as blocks:
                   "li", "dd", "dt" ]

_block_containers = ["_top_block",
                     "body", "div", "center", "object", "applet",
                     "blockquote", "ins", "del", "dd", "li", "form",
                     "fieldset", "button", "th", "td", "iframe", "noscript",
                     "noframes",
                     # Incorrect, but we treat list items as blocks:
                     "ul", "ol", "dir", "menu", "dl"]


class HTMLDecoder(HTMLParser, structured.StructuredTextDecoder):
    """Decoder for HTML documents."""
    #: Default style attributes for unstyled text in the HTML document.
    default_style: ClassVar[dict[str, Any]] = {
        "font_name": "Times New Roman",
        "font_size": 12,
        "margin_bottom": "12pt",
        "bold": False,
        "italic": False,
    }

    #: Map HTML font sizes to actual font sizes, in points.
    font_sizes: ClassVar[dict[int, int]] = {
        1: 8,
        2: 10,
        3: 12,
        4: 14,
        5: 18,
        6: 24,
        7: 48,
    }

    def decode_structured(self, text: str, location: Location) -> None:
        self.location = location
        self._font_size_stack = [3]
        self.list_stack.append(structured.UnorderedListBuilder({})) # type: ignore reportArgumentType
        self.strip_leading_space = True
        self.block_begin = True
        self.need_block_begin = False
        self.element_stack = ["_top_block"]
        self.in_metadata = False
        self.in_pre = False

        self.push_style("_default", self.default_style)

        self.feed(text)
        self.close()

    def get_image(self, filename: str) -> AbstractImage:
        return pyglet.image.load(filename, file=self.location.open(filename))

    def prepare_for_data(self) -> None:
        if self.need_block_begin:
            self.add_text("\n")
            self.block_begin = True
            self.need_block_begin = False

    def handle_data(self, data: str) -> None:
        if self.in_metadata:
            return

        if self.in_pre:
            self.add_text(data)
        else:
            data = _whitespace_re.sub(" ", data)
            if data.strip():
                self.prepare_for_data()
                if self.block_begin or self.strip_leading_space:
                    data = data.lstrip()
                    self.block_begin = False
                self.add_text(data)
            self.strip_leading_space = data.endswith(" ")

    def handle_starttag(self, tag: str, case_attrs: dict[str, Any]) -> None:
        if self.in_metadata:
            return

        element = tag.lower()
        attrs = {}
        for key, value in case_attrs:
            attrs[key.lower()] = value

        if element in _metadata_elements:
            self.in_metadata = True
        elif element in _block_elements:
            # Pop off elements until we get to a block container.
            while self.element_stack[-1] not in _block_containers:
                self.handle_endtag(self.element_stack[-1])
            if not self.block_begin:
                self.add_text("\n")
                self.block_begin = True
                self.need_block_begin = False
        self.element_stack.append(element)

        style = {}
        if element in ("b", "strong"):
            style["bold"] = True
        elif element in ("i", "em", "var"):
            style["italic"] = True
        elif element in ("tt", "code", "samp", "kbd"):
            style["font_name"] = "Courier New"
        elif element == "u":
            color = self.current_style.get("color")
            if color is None:
                color = [0, 0, 0, 255]
            style["underline"] = color
        elif element == "font":
            if "face" in attrs:
                style["font_name"] = attrs["face"].split(",")
            if "size" in attrs:
                size = attrs["size"]
                try:
                    if size.startswith("+"):
                        size = self._font_size_stack[-1] + int(size[1:])
                    elif size.startswith("-"):
                        size = self._font_size_stack[-1] - int(size[1:])
                    else:
                        size = int(size)
                except ValueError:
                    size = 3
                self._font_size_stack.append(size)
                if size in self.font_sizes:
                    style["font_size"] = self.font_sizes.get(size, 3)
            elif "real_size" in attrs:
                size = int(attrs["real_size"])
                self._font_size_stack.append(size)
                style["font_size"] = size
            else:
                self._font_size_stack.append(self._font_size_stack[-1])
            if "color" in attrs:
                with contextlib.suppress(ValueError):
                    style["color"] = _parse_color(attrs["color"])
        elif element == "sup":
            size = self._font_size_stack[-1] - 1
            style["font_size"] = self.font_sizes.get(size, 1)
            style["baseline"] = "3pt"
        elif element == "sub":
            size = self._font_size_stack[-1] - 1
            style["font_size"] = self.font_sizes.get(size, 1)
            style["baseline"] = "-3pt"
        elif element == "h1":
            style["font_size"] = 24
            style["bold"] = True
            style["align"] = "center"
        elif element == "h2":
            style["font_size"] = 18
            style["bold"] = True
        elif element == "h3":
            style["font_size"] = 16
            style["bold"] = True
        elif element == "h4":
            style["font_size"] = 14
            style["bold"] = True
        elif element == "h5":
            style["font_size"] = 12
            style["bold"] = True
        elif element == "h6":
            style["font_size"] = 12
            style["italic"] = True
        elif element == "br":
            self.add_text("\u2028")
            self.strip_leading_space = True
        elif element == "p":
            if attrs.get("align") in ("left", "center", "right"):
                style["align"] = attrs["align"]
        elif element == "center":
            style["align"] = "center"
        elif element == "pre":
            style["font_name"] = "Courier New"
            style["margin_bottom"] = 0
            self.in_pre = True
        elif element == "blockquote":
            left_margin = self.current_style.get("margin_left") or 0
            right_margin = self.current_style.get("margin_right") or 0
            style["margin_left"] = left_margin + 60
            style["margin_right"] = right_margin + 60
        elif element == "q":
            self.handle_data("\u201c")
        elif element == "ol":
            try:
                start = int(attrs.get("start", 1))
            except ValueError:
                start = 1
            fmt = attrs.get("type", "1") + "."
            builder = structured.OrderedListBuilder(start, fmt)
            builder.begin(self, style)
            self.list_stack.append(builder)
        elif element in ("ul", "dir", "menu"):
            type_ = attrs.get("type", "disc").lower()
            if type_ == "circle":
                mark = "\u25cb"
            elif type_ == "square":
                mark = "\u25a1"
            else:
                mark = "\u25cf"
            builder = structured.UnorderedListBuilder(mark)
            builder.begin(self, style)
            self.list_stack.append(builder)
        elif element == "li":
            self.list_stack[-1].item(self, style)
            self.strip_leading_space = True
        elif element == "dl":
            style["margin_bottom"] = 0
        elif element == "dd":
            left_margin = self.current_style.get("margin_left") or 0
            style["margin_left"] = left_margin + 30
        elif element == "img":
            image = self.get_image(attrs.get("src")) # type: ignore reportArgumentType
            if image:
                width = attrs.get("width")
                if width:
                    width = int(width)
                height = attrs.get("height")
                if height:
                    height = int(height)
                self.prepare_for_data()
                self.add_element(structured.ImageElement(image, width, height))
                self.strip_leading_space = False

        self.push_style(element, style)

    def handle_endtag(self, tag: str) -> None:
        element = tag.lower()
        if element not in self.element_stack:
            return

        self.pop_style(element)
        while self.element_stack.pop() != element:
            pass

        if element in _metadata_elements:
            self.in_metadata = False
        elif element in _block_elements:
            self.block_begin = False
            self.need_block_begin = True

        if element == "font" and len(self._font_size_stack) > 1:
            self._font_size_stack.pop()
        elif element == "pre":
            self.in_pre = False
        elif element == "q":
            self.handle_data("\u201d")
        elif element in ("ul", "ol") and len(self.list_stack) > 1:
            self.list_stack.pop()

    def handle_entityref(self, name: str) -> None:
        if name in entities.name2codepoint:
            self.handle_data(chr(entities.name2codepoint[name]))

    def handle_charref(self, name: str) -> None:
        name = name.lower()
        try:
            if name.startswith("x"):
                self.handle_data(chr(int(name[1:], 16)))
            else:
                self.handle_data(chr(int(name)))
        except ValueError:
            pass
