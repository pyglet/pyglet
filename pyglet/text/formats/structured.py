"""Base class for structured (hierarchical) document formats.
"""
from __future__ import annotations
import re
from typing import List, TYPE_CHECKING, Optional, Any

import pyglet
import pyglet.text.layout

from pyglet.gl import GL_TEXTURE0, glActiveTexture, glBindTexture, glEnable, GL_BLEND, glBlendFunc, GL_SRC_ALPHA, \
    GL_ONE_MINUS_SRC_ALPHA, glDisable


if TYPE_CHECKING:
    from pyglet.text.layout import TextLayout
    from pyglet.image import AbstractImage


class _InlineElementGroup(pyglet.graphics.Group):
    def __init__(self, texture, program, order=0, parent=None):
        super().__init__(order, parent)
        self.texture = texture
        self.program = program

    def set_state(self):
        self.program.use()

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(self.texture.target, self.texture.id)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def unset_state(self):
        glDisable(GL_BLEND)
        self.program.stop()

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
                self._order == other.order and
                self.program == other.program and
                self.parent == other.parent and
                self.texture.target == other.texture.target and
                self.texture.id == other.texture.id)

    def __hash__(self):
        return hash((self._order, self.program, self.parent,
                     self.texture.target, self.texture.id))


class ImageElement(pyglet.text.document.InlineElement):
    height: int
    width: int

    def __init__(self, image: AbstractImage, width: Optional[int]=None, height: Optional[int]=None):
        self.image = image.get_texture()
        self.width = width is None and image.width or width
        self.height = height is None and image.height or height
        self.vertex_lists = {}

        anchor_y = self.height // image.height * image.anchor_y
        ascent = max(0, self.height - anchor_y)
        descent = min(0, -anchor_y)
        super().__init__(ascent, descent, self.width)

    def place(self, layout: TextLayout, x: float, y: float, z: float, line_x: float, line_y: float, rotation: float,
              visible: bool, anchor_x: float, anchor_y: float) -> None:
        program = pyglet.text.layout.get_default_image_layout_shader()
        group = _InlineElementGroup(self.image.get_texture(), program, 0, layout.group)
        x1 = line_x
        y1 = line_y + self.descent
        x2 = line_x + self.width
        y2 = line_y + self.height + self.descent

        vertex_list = program.vertex_list_indexed(4, pyglet.gl.GL_TRIANGLES, [0, 1, 2, 0, 2, 3],
                                                  layout.batch, group,
                                                  position=('f', (x1, y1, z, x2, y1, z, x2, y2, z, x1, y2, z)),
                                                  translation=('f', (x, y, z) * 4),
                                                  tex_coords=('f', self.image.tex_coords),
                                                  visible=('f', (visible,) * 4),
                                                  rotation=('f', (rotation,) * 4),
                                                  anchor=('f', (anchor_x, anchor_y) * 4)
                                                  )

        self.vertex_lists[layout] = vertex_list

    def update_translation(self, x: float, y: float, z: float) -> None:
        translation = (x, y, z)
        for _vertex_list in self.vertex_lists.values():
            _vertex_list.translation[:] = translation * _vertex_list.count

    def update_color(self, color: List[int]) -> None:
        # No color blending in shader. Optional.
        ...

    def update_view_translation(self, translate_x: float, translate_y: float) -> None:
        view_translation = (-translate_x, -translate_y, 0)
        for _vertex_list in self.vertex_lists.values():
            _vertex_list.view_translation[:] = view_translation * _vertex_list.count

    def update_rotation(self, rotation: float) -> None:
        rot_tuple = (rotation,)
        for _vertex_list in self.vertex_lists.values():
           _vertex_list.rotation[:] = rot_tuple * _vertex_list.count

    def update_visibility(self, visible: bool) -> None:
        visible_tuple = (visible,)
        for _vertex_list in self.vertex_lists.values():
           _vertex_list.visible[:] = visible_tuple * _vertex_list.count

    def update_anchor(self, anchor_x: float, anchor_y: float) -> None:
        anchor = (anchor_x, anchor_y)
        for _vertex_list in self.vertex_lists.values():
            _vertex_list.anchor[:] = anchor * _vertex_list.count

    def remove(self, layout: TextLayout) -> None:
        self.vertex_lists[layout].delete()
        del self.vertex_lists[layout]


def _int_to_roman(number: int) -> str:
    # From http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/81611
    if not 0 < number < 4000:
        raise ValueError("Argument must be between 1 and 3999")
    integers = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,   4,  1)
    numerals = ('M',  'CM', 'D', 'CD','C', 'XC','L','XL','X','IX','V','IV','I')
    result = ""
    for i in range(len(integers)):
        count = int(number // integers[i])
        result += numerals[i] * count
        number -= integers[i] * count
    return result


class ListBuilder:

    def begin(self, decoder, style):
        """Begin a list.

        :Parameters:
            `decoder` : `StructuredTextDecoder`
                Decoder.
            `style` : dict
                Style dictionary that applies over the entire list.

        """
        left_margin = decoder.current_style.get('margin_left') or 0
        tab_stops = decoder.current_style.get('tab_stops')
        if tab_stops:
            tab_stops = list(tab_stops)
        else:
            tab_stops = []
        tab_stops.append(left_margin + 50)
        style['margin_left'] = left_margin + 50
        style['indent'] = -30
        style['tab_stops'] = tab_stops

    def item(self, decoder, style, value=None):
        """Begin a list item.

        :Parameters:
            `decoder` : `StructuredTextDecoder`
                Decoder.
            `style` : dict
                Style dictionary that applies over the list item.
            `value` : str
                Optional value of the list item.  The meaning is list-type
                dependent.

        """
        mark = self.get_mark(value)
        if mark:
            decoder.add_text(mark)
        decoder.add_text('\t')

    def get_mark(self, value=None):
        """Get the mark text for the next list item.

        :Parameters:
            `value` : str
                Optional value of the list item.  The meaning is list-type
                dependent.

        :rtype: str
        """
        return ''


class UnorderedListBuilder(ListBuilder):

    def __init__(self, mark):
        """Create an unordered list with constant mark text.

        :Parameters:
            `mark` : str
                Mark to prepend to each list item.

        """
        self.mark = mark

    def get_mark(self, value):
        return self.mark


class OrderedListBuilder(ListBuilder):
    format_re = re.compile('(.*?)([1aAiI])(.*)')

    def __init__(self, start, fmt):
        """Create an ordered list with sequentially numbered mark text.

        The format is composed of an optional prefix text, a numbering
        scheme character followed by suffix text. Valid numbering schemes
        are:

        ``1``
            Decimal Arabic
        ``a``
            Lowercase alphanumeric
        ``A``
            Uppercase alphanumeric
        ``i``
            Lowercase Roman
        ``I``
            Uppercase Roman

        Prefix text may typically be ``(`` or ``[`` and suffix text is
        typically ``.``, ``)`` or empty, but either can be any string.

        :Parameters:
            `start` : int
                First list item number.
            `fmt` : str
                Format style, for example ``"1."``.

        """
        self.next_value = start

        self.prefix, self.numbering, self.suffix = self.format_re.match(fmt).groups()
        assert self.numbering in '1aAiI'

    def get_mark(self, value):
        if value is None:
            value = self.next_value
        self.next_value = value + 1
        if self.numbering in 'aA':
            try:
                mark = 'abcdefghijklmnopqrstuvwxyz'[value - 1]
            except ValueError:
                mark = '?'
            if self.numbering == 'A':
                mark = mark.upper()
            return f'{self.prefix}{mark}{self.suffix}'
        elif self.numbering in 'iI':
            try:
                mark = _int_to_roman(value)
            except ValueError:
                mark = '?'
            if self.numbering == 'i':
                mark = mark.lower()
            return f'{self.prefix}{mark}{self.suffix}'
        else:
            return f'{self.prefix}{value}{self.suffix}'


class StructuredTextDecoder(pyglet.text.DocumentDecoder):
    def decode(self, text, location=None):
        self.len_text = 0
        self.current_style = {}
        self.next_style = {}
        self.stack = []
        self.list_stack = []
        self.document = pyglet.text.document.FormattedDocument()
        if location is None:
            location = pyglet.resource.FileLocation('')
        self.decode_structured(text, location)
        return self.document

    def decode_structured(self, text, location):
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
