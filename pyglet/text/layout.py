# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2022 pyglet contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

"""Render simple text and formatted documents efficiently.

Three layout classes are provided:

:py:class:`~pyglet.text.layout.TextLayout`
    The entire document is laid out before it is rendered.  The layout will
    be grouped with other layouts in the same batch (allowing for efficient
    rendering of multiple layouts).

    Any change to the layout or document,
    and even querying some properties, will cause the entire document
    to be laid out again.

:py:class:`~pyglet.text.layout.ScrollableTextLayout`
    Based on :py:func:`~pyglet.text.layout.TextLayout`.

    A separate group is used for layout which crops the contents of the
    layout to the layout rectangle.  Additionally, the contents of the
    layout can be "scrolled" within that rectangle with the ``view_x`` and
    ``view_y`` properties.

:py:class:`~pyglet.text.layout.IncrementalTextLayout`
    Based on :py:class:`~pyglet.text.layout.ScrollableTextLayout`.

    When the layout or document are modified, only the affected regions
    are laid out again.  This permits efficient interactive editing and
    styling of text.

    Only the visible portion of the layout is actually rendered; as the
    viewport is scrolled additional sections are rendered and discarded as
    required.  This permits efficient viewing and editing of large documents.

    Additionally, this class provides methods for locating the position of a
    caret in the document, and for displaying interactive text selections.

All three layout classes can be used with either :py:class:`~pyglet.text.document.UnformattedDocument` or
:py:class:`~pyglet.text.document.FormattedDocument`, and can be either single-line or ``multiline``.  The
combinations of these options effectively provides 12 different text display
possibilities.

Style attributes
================

The following character style attribute names are recognised by the layout
classes.  Data types and units are as specified.

Where an attribute is marked "as a distance" the value is assumed to be
in pixels if given as an int or float, otherwise a string of the form
``"0u"`` is required, where ``0`` is the distance and ``u`` is the unit; one
of ``"px"`` (pixels), ``"pt"`` (points), ``"pc"`` (picas), ``"cm"``
(centimeters), ``"mm"`` (millimeters) or ``"in"`` (inches).  For example,
``"14pt"`` is the distance covering 14 points, which at the default DPI of 96
is 18 pixels.

``font_name``
    Font family name, as given to :py:func:`pyglet.font.load`.
``font_size``
    Font size, in points.
``bold``
    Boolean.
``italic``
    Boolean.
``underline``
    4-tuple of ints in range (0, 255) giving RGBA underline color, or None
    (default) for no underline.
``kerning``
    Additional space to insert between glyphs, as a distance.  Defaults to 0.
``baseline``
    Offset of glyph baseline from line baseline, as a distance.  Positive
    values give a superscript, negative values give a subscript.  Defaults to
    0.
``color``
    4-tuple of ints in range (0, 255) giving RGBA text color
``background_color``
    4-tuple of ints in range (0, 255) giving RGBA text background color; or
    ``None`` for no background fill.

The following paragraph style attribute names are recognised.  Note
that paragraph styles are handled no differently from character styles by the
document: it is the application's responsibility to set the style over an
entire paragraph, otherwise results are undefined.

``align``
    ``left`` (default), ``center`` or ``right``.
``indent``
    Additional horizontal space to insert before the first glyph of the
    first line of a paragraph, as a distance.
``leading``
    Additional space to insert between consecutive lines within a paragraph,
    as a distance.  Defaults to 0.
``line_spacing``
    Distance between consecutive baselines in a paragraph, as a distance.
    Defaults to ``None``, which automatically calculates the tightest line
    spacing for each line based on the font ascent and descent.
``margin_left``
    Left paragraph margin, as a distance.
``margin_right``
    Right paragraph margin, as a distance.
``margin_top``
    Margin above paragraph, as a distance.
``margin_bottom``
    Margin below paragraph, as a distance.  Adjacent margins do not collapse.
``tab_stops``
    List of horizontal tab stops, as distances, measured from the left edge of
    the text layout.  Defaults to the empty list.  When the tab stops
    are exhausted, they implicitly continue at 50 pixel intervals.
``wrap``
    ``char``, ``word``, True (default) or False.  The boundaries at which to
    wrap text to prevent it overflowing a line.  With ``char``, the line
    wraps anywhere in the text; with ``word`` or True, the line wraps at
    appropriate boundaries between words; with False the line does not wrap,
    and may overflow the layout width.  ``char`` and ``word`` styles are
    since pyglet 1.2.

Other attributes can be used to store additional style information within the
document; they will be ignored by the built-in text classes.

.. versionadded:: 1.1
"""

import re
import sys

import pyglet

from pyglet import graphics
from pyglet.gl import *
from pyglet.event import EventDispatcher
from pyglet.text import runlist
from pyglet.graphics import shader
from pyglet.font.base import grapheme_break

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run

_distance_re = re.compile(r'([-0-9.]+)([a-zA-Z]+)')


def _parse_distance(distance, dpi):
    """Parse a distance string and return corresponding distance in pixels as
    an integer.
    """
    if isinstance(distance, int):
        return distance
    elif isinstance(distance, float):
        return int(distance)

    match = _distance_re.match(distance)
    assert match, 'Could not parse distance %s' % distance
    if not match:
        return 0

    value, unit = match.groups()
    value = float(value)
    if unit == 'px':
        return int(value)
    elif unit == 'pt':
        return int(value * dpi / 72.0)
    elif unit == 'pc':
        return int(value * dpi / 6.0)
    elif unit == 'in':
        return int(value * dpi)
    elif unit == 'mm':
        return int(value * dpi * 0.0393700787)
    elif unit == 'cm':
        return int(value * dpi * 0.393700787)
    else:
        assert False, 'Unknown distance unit %s' % unit


class _Line:
    align = 'left'

    margin_left = 0
    margin_right = 0

    length = 0

    ascent = 0
    descent = 0
    width = 0
    paragraph_begin = False
    paragraph_end = False

    x = None
    y = None

    def __init__(self, start):
        self.vertex_lists = []
        self.start = start
        self.boxes = []

    def __repr__(self):
        return '_Line(%r)' % self.boxes

    def add_box(self, box):
        self.boxes.append(box)
        self.length += box.length
        self.ascent = max(self.ascent, box.ascent)
        self.descent = min(self.descent, box.descent)
        self.width += box.advance

    def delete(self, layout):
        for vertex_list in self.vertex_lists:
            vertex_list.delete()
        self.vertex_lists = []

        for box in self.boxes:
            box.delete(layout)


class _LayoutContext:
    def __init__(self, layout, document, colors_iter, background_iter):
        self.colors_iter = colors_iter
        underline_iter = document.get_style_runs('underline')
        self.decoration_iter = runlist.ZipRunIterator((background_iter, underline_iter))
        self.baseline_iter = runlist.FilteredRunIterator(
            document.get_style_runs('baseline'),
            lambda value: value is not None, 0)


class _StaticLayoutContext(_LayoutContext):
    def __init__(self, layout, document, colors_iter, background_iter):
        super().__init__(layout, document, colors_iter, background_iter)
        self.vertex_lists = layout._vertex_lists
        self.boxes = layout._boxes

    def add_list(self, vertex_list):
        self.vertex_lists.append(vertex_list)

    def add_box(self, box):
        self.boxes.append(box)


class _IncrementalLayoutContext(_LayoutContext):
    line = None

    def add_list(self, vertex_list):
        self.line.vertex_lists.append(vertex_list)

    def add_box(self, box):
        pass


class _AbstractBox:
    owner = None

    def __init__(self, ascent, descent, advance, length):
        self.ascent = ascent
        self.descent = descent
        self.advance = advance
        self.length = length

    def place(self, layout, i, x, y, context):
        raise NotImplementedError('abstract')

    def delete(self, layout):
        raise NotImplementedError('abstract')

    def get_position_in_box(self, x):
        raise NotImplementedError('abstract')

    def get_point_in_box(self, position):
        raise NotImplementedError('abstract')


class _GlyphBox(_AbstractBox):
    def __init__(self, owner, font, glyphs, advance):
        """Create a run of glyphs sharing the same texture.

        :Parameters:
            `owner` : `pyglet.image.Texture`
                Texture of all glyphs in this run.
            `font` : `pyglet.font.base.Font`
                Font of all glyphs in this run.
            `glyphs` : list of (int, `pyglet.font.base.Glyph`)
                Pairs of ``(kern, glyph)``, where ``kern`` gives horizontal
                displacement of the glyph in pixels (typically 0).
            `advance` : int
                Width of glyph run; must correspond to the sum of advances
                and kerns in the glyph list.

        """
        super().__init__(font.ascent, font.descent, advance, len(glyphs))
        assert owner
        self.owner = owner
        self.font = font
        self.glyphs = glyphs
        self.advance = advance

    def place(self, layout, i, x, y, context):
        assert self.glyphs
        program = get_default_layout_shader()

        try:
            group = layout.group_cache[self.owner]
        except KeyError:
            group = layout.group_class(self.owner, program, order=1, parent=layout.group)
            layout.group_cache[self.owner] = group

        n_glyphs = self.length
        vertices = []
        tex_coords = []
        baseline = 0
        x1 = x
        for start, end, baseline in context.baseline_iter.ranges(i, i + n_glyphs):
            baseline = layout.parse_distance(baseline)
            assert len(self.glyphs[start - i:end - i]) == end - start
            for kern, glyph in self.glyphs[start - i:end - i]:
                x1 += kern
                v0, v1, v2, v3 = glyph.vertices
                v0 += x1
                v2 += x1
                v1 += y + baseline
                v3 += y + baseline
                vertices.extend(map(int, [v0, v1, v2, v1, v2, v3, v0, v3]))
                t = glyph.tex_coords
                tex_coords.extend(t)
                x1 += glyph.advance

        # Text color
        colors = []
        for start, end, color in context.colors_iter.ranges(i, i + n_glyphs):
            if color is None:
                color = (0, 0, 0, 255)
            if len(color) != 4:
                raise ValueError("Color requires 4 values (R, G, B, A). Value received: {}".format(color))
            colors.extend(color * ((end - start) * 4))

        indices = []
        # Create indices for each glyph quad:
        for glyph_idx in range(n_glyphs):
            indices.extend([element + (glyph_idx * 4) for element in [0, 1, 2, 0, 2, 3]])

        vertex_list = program.vertex_list_indexed(n_glyphs * 4, GL_TRIANGLES, indices, layout.batch, group,
                                                  position=('f', vertices),
                                                  colors=('Bn', colors),
                                                  tex_coords=('f', tex_coords))

        context.add_list(vertex_list)

        # Decoration (background color and underline)
        # -------------------------------------------
        # Should iterate over baseline too, but in practice any sensible
        # change in baseline will correspond with a change in font size,
        # and thus glyph run as well.  So we cheat and just use whatever
        # baseline was seen last.
        background_vertices = []
        background_colors = []
        underline_vertices = []
        underline_colors = []
        y1 = y + self.descent + baseline
        y2 = y + self.ascent + baseline
        x1 = x

        for start, end, decoration in context.decoration_iter.ranges(i, i + n_glyphs):
            bg, underline = decoration
            x2 = x1
            for kern, glyph in self.glyphs[start - i:end - i]:
                x2 += glyph.advance + kern

            if bg is not None:
                if len(bg) != 4:
                    raise ValueError("Background color requires 4 values (R, G, B, A). Value received: {}".format(bg))

                background_vertices.extend([x1, y1, x2, y1, x2, y2, x1, y2])
                background_colors.extend(bg * 4)

            if underline is not None:
                if len(underline) != 4:
                    raise ValueError("Underline color requires 4 values (R, G, B, A). Value received: {}".format(underline))

                underline_vertices.extend([x1, y + baseline - 2, x2, y + baseline - 2])
                underline_colors.extend(underline * 2)

            x1 = x2

        if background_vertices:
            background_indices = []
            bg_count = len(background_vertices) // 2
            for glyph_idx in range(bg_count):
                background_indices.extend([element + (glyph_idx * 4) for element in [0, 1, 2, 0, 2, 3]])

            background_list = program.vertex_list_indexed(bg_count, GL_TRIANGLES, background_indices,
                                                          layout.batch, layout.background_decoration_group,
                                                          position=('f', background_vertices),
                                                          colors=('Bn', background_colors))
            context.add_list(background_list)

        if underline_vertices:
            underline_list = program.vertex_list(len(underline_vertices) // 2, GL_LINES,
                                                 layout.batch, layout.foreground_decoration_group,
                                                 position=('f',underline_vertices),
                                                 colors=('Bn', underline_colors))
            context.add_list(underline_list)

    def delete(self, layout):
        pass

    def get_point_in_box(self, position):
        x = 0
        for (kern, glyph) in self.glyphs:
            if position == 0:
                break
            position -= 1
            x += glyph.advance + kern
        return x

    def get_position_in_box(self, x):
        position = 0
        last_glyph_x = 0
        for kern, glyph in self.glyphs:
            last_glyph_x += kern
            if last_glyph_x + glyph.advance // 2 > x:
                return position
            position += 1
            last_glyph_x += glyph.advance
        return position

    def __repr__(self):
        return '_GlyphBox(%r)' % self.glyphs


class _InlineElementBox(_AbstractBox):
    def __init__(self, element):
        """Create a glyph run holding a single element.
        """
        super().__init__(element.ascent, element.descent, element.advance, 1)
        self.element = element
        self.placed = False

    def place(self, layout, i, x, y, context):
        self.element.place(layout, x, y)
        self.placed = True
        context.add_box(self)

    def delete(self, layout):
        # font == element
        if self.placed:
            self.element.remove(layout)
            self.placed = False

    def get_point_in_box(self, position):
        if position == 0:
            return 0
        else:
            return self.advance

    def get_position_in_box(self, x):
        if x < self.advance // 2:
            return 0
        else:
            return 1

    def __repr__(self):
        return '_InlineElementBox(%r)' % self.element


class _InvalidRange:
    # Used by the IncrementalTextLayout

    def __init__(self):
        self.start = sys.maxsize
        self.end = 0

    def insert(self, start, length):
        if self.start >= start:
            self.start += length
        if self.end >= start:
            self.end += length
        self.invalidate(start, start + length)

    def delete(self, start, end):
        if self.start > end:
            self.start -= end - start
        elif self.start > start:
            self.start = start
        if self.end > end:
            self.end -= end - start
        elif self.end > start:
            self.end = start

    def invalidate(self, start, end):
        if end <= start:
            return
        self.start = min(self.start, start)
        self.end = max(self.end, end)

    def validate(self):
        start, end = self.start, self.end
        self.start = sys.maxsize
        self.end = 0
        return start, end

    def is_invalid(self):
        return self.end > self.start


layout_vertex_source = """#version 330 core
    in vec2 position;
    in vec4 colors;
    in vec3 tex_coords;
    in vec2 translation;

    out vec4 text_colors;
    out vec2 texture_coords;
    out vec4 vert_position;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    void main()
    {
        gl_Position = window.projection * window.view * vec4(position + translation, 0.0, 1.0);

        vert_position = vec4(position + translation, 0.0, 1.0);
        text_colors = colors;
        texture_coords = tex_coords.xy;
    }
"""

layout_fragment_source = """#version 330 core
    in vec4 text_colors;
    in vec2 texture_coords;
    in vec4 vert_position;

    out vec4 final_colors;

    uniform sampler2D text;
    uniform bool scissor;
    uniform vec4 scissor_area;

    void main()
    {
        final_colors = vec4(text_colors.rgb, texture(text, texture_coords).a * text_colors.a);
        if (scissor == true) {
            if (vert_position.x < scissor_area[0]) discard;                     // left
            if (vert_position.y < scissor_area[1]) discard;                     // bottom
            if (vert_position.x > scissor_area[0] + scissor_area[2]) discard;   // right
            if (vert_position.y > scissor_area[1] + scissor_area[3]) discard;   // top
        }
    }
"""

decoration_vertex_source = """#version 330 core
    in vec2 position;
    in vec4 colors;
    in vec2 translation;

    out vec4 vert_colors;
    out vec4 vert_position;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    void main()
    {
        gl_Position = window.projection * window.view * vec4(position + translation, 0.0, 1.0);

        vert_position = vec4(position + translation, 0.0, 1.0);
        vert_colors = colors;
    }
"""

decoration_fragment_source = """#version 330 core
    in vec4 vert_colors;
    in vec4 vert_position;

    out vec4 final_colors;

    uniform bool scissor;
    uniform vec4 scissor_area;

    void main()
    {   
        final_colors = vert_colors;
        if (scissor == true) {
            if (vert_position.x < scissor_area[0]) discard;                     // left
            if (vert_position.y < scissor_area[1]) discard;                     // bottom
            if (vert_position.x > scissor_area[0] + scissor_area[2]) discard;   // right
            if (vert_position.y > scissor_area[1] + scissor_area[3]) discard;   // top
        }
    }
"""


def get_default_layout_shader():
    try:
        return pyglet.gl.current_context.pyglet_text_layout_shader
    except AttributeError:
        pyglet.gl.current_context.pyglet_text_layout_shader = shader.ShaderProgram(
            shader.Shader(layout_vertex_source, 'vertex'),
            shader.Shader(layout_fragment_source, 'fragment'),
        )
        return pyglet.gl.current_context.pyglet_text_layout_shader


def get_default_decoration_shader():
    try:
        return pyglet.gl.current_context.pyglet_text_decoration_shader
    except AttributeError:
        pyglet.gl.current_context.pyglet_text_decoration_shader = shader.ShaderProgram(
            shader.Shader(decoration_vertex_source, 'vertex'),
            shader.Shader(decoration_fragment_source, 'fragment'),
        )
        return pyglet.gl.current_context.pyglet_text_decoration_shader


class TextLayoutGroup(graphics.Group):
    def __init__(self, texture, program, order=1, parent=None):
        """Create a text layout rendering group.

        The group is created internally when a :py:class:`~pyglet.text.Label`
        is created; applications usually do not need to explicitly create it.
        """
        super().__init__(order=order, parent=parent)
        self.texture = texture
        self.program = program

    def set_state(self):
        self.program.use()
        self.program['scissor'] = False

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(self.texture.target, self.texture.id)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def unset_state(self):
        glDisable(GL_BLEND)
        self.program.stop()

    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__, self.texture)

    def __eq__(self, other):
        return (other.__class__ is self.__class__ and
                self.parent is other.parent and
                self.program.id is other.program.id and
                self.order == other.order and
                self.texture.target == other.texture.target and
                self.texture.id == other.texture.id)

    def __hash__(self):
        return hash((id(self.parent), self.program.id, self.order, self.texture.target, self.texture.id))


class ScrollableTextLayoutGroup(graphics.Group):
    scissor_area = 0, 0, 0, 0

    def __init__(self, texture, program, order=1, parent=None):
        """Default rendering group for :py:class:`~pyglet.text.layout.ScrollableTextLayout`.

        The group maintains internal state for specifying the viewable
        area, and for scrolling. Because the group has internal state
        specific to the text layout, the group is never shared.
        """
        super().__init__(order=order, parent=parent)
        self.texture = texture
        self.program = program

    def set_state(self):
        self.program.use()
        self.program['scissor'] = True
        self.program['scissor_area'] = self.scissor_area

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(self.texture.target, self.texture.id)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def unset_state(self):
        glDisable(GL_BLEND)
        self.program.stop()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.texture})"

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)


class IncrementalTextLayoutGroup(ScrollableTextLayoutGroup):
    # Subclass so that the scissor_area isn't shared with the
    # ScrollableTextLayout. We use a class variable here so
    # that it can be set before the document glyphs are created.
    scissor_area = 0, 0, 0, 0


class TextDecorationGroup(graphics.Group):
    def __init__(self, program, order=0, parent=None):
        """Create a text decoration rendering group.

        The group is created internally when a :py:class:`~pyglet.text.Label`
        is created; applications usually do not need to explicitly create it.
        """
        super().__init__(order=order, parent=parent)
        self.program = program

    def set_state(self):
        self.program.use()
        self.program['scissor'] = False

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def unset_state(self):
        glDisable(GL_BLEND)
        self.program.stop()


class ScrollableTextDecorationGroup(graphics.Group):
    scissor_area = 0, 0, 0, 0

    def __init__(self, program, order=0, parent=None):
        """Create a text decoration rendering group.

        The group is created internally when a :py:class:`~pyglet.text.Label`
        is created; applications usually do not need to explicitly create it.
        """
        super().__init__(order=order, parent=parent)
        self.program = program

    def set_state(self):
        self.program.use()
        self.program['scissor'] = True
        self.program['scissor_area'] = self.scissor_area

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def unset_state(self):
        glDisable(GL_BLEND)
        self.program.stop()


class IncrementalTextDecorationGroup(ScrollableTextDecorationGroup):
    # Subclass so that the scissor_area isn't shared with the
    # ScrollableTextDecorationGroup. We use a class variable here so
    # that it can be set before the document glyphs are created.
    scissor_area = 0, 0, 0, 0


# ####################


class TextLayout:
    """Lay out and display documents.

    This class is intended for displaying documents that do not change
    regularly -- any change will cost some time to lay out the complete
    document again and regenerate all vertex lists.

    The benefit of this class is that texture state is shared between
    all layouts of this class.  The time to draw one :py:func:`~pyglet.text.layout.TextLayout` may be
    roughly the same as the time to draw one :py:class:`~pyglet.text.layout.IncrementalTextLayout`; but
    drawing ten :py:func:`~pyglet.text.layout.TextLayout` objects in one batch is much faster than drawing
    ten incremental or scrollable text layouts.

    :py:func:`~pyglet.text.Label` and :py:func:`~pyglet.text.HTMLLabel` provide a convenient interface to this class.

    :Ivariables:
        `content_width` : int
            Calculated width of the text in the layout.  This may overflow
            the desired width if word-wrapping failed.
        `content_height` : int
            Calculated height of the text in the layout.
        `group_class` : `~pyglet.graphics.Group`
            Top-level rendering group.
        `background_decoration_group` : `~pyglet.graphics.Group`
            Rendering group for background color.
        `foreground_decoration_group` : `~pyglet.graphics.Group`
            Rendering group for glyph underlines.

    """
    _document = None
    _vertex_lists = []
    _boxes = []

    _update_enabled = True
    _own_batch = False
    group_class = TextLayoutGroup
    decoration_class = TextDecorationGroup

    _x = 0
    _y = 0
    _width = None
    _height = None
    _anchor_x = 'left'
    _anchor_y = 'bottom'
    _content_valign = 'top'
    _multiline = False
    _visible = True

    def __init__(self, document, width=None, height=None,
                 multiline=False, dpi=None, batch=None, group=None,
                 wrap_lines=True):
        """Create a text layout.

        :Parameters:
            `document` : `AbstractDocument`
                Document to display.
            `width` : int
                Width of the layout in pixels, or None
            `height` : int
                Height of the layout in pixels, or None
            `multiline` : bool
                If False, newline and paragraph characters are ignored, and
                text is not word-wrapped.
                If True, text is wrapped only if the `wrap_lines` is True.
            `dpi` : float
                Font resolution; defaults to 96.
            `batch` : `~pyglet.graphics.Batch`
                Optional graphics batch to add this layout to.
            `group` : `~pyglet.graphics.Group`
                Optional Group to parent all internal Groups that this text
                layout uses.  Note that layouts with the same Groups will
                be rendered simultaneously in a Batch.
            `wrap_lines` : bool
                If True and `multiline` is True, the text is word-wrapped using
                the specified width.

        """
        self.content_width = 0
        self.content_height = 0

        self._user_group = group
        self.group_cache = {}
        self._initialize_groups()

        if batch is None:
            batch = graphics.Batch()
            self._own_batch = True
        self._batch = batch

        self._width = width
        self._height = height
        self._multiline = multiline

        # Alias the correct flow method:
        self._flow_glyphs = self._flow_glyphs_wrap if multiline else self._flow_glyphs_single_line

        self._wrap_lines_flag = wrap_lines
        self._wrap_lines_invariant()

        self._dpi = dpi or 96
        self.document = document

    def _initialize_groups(self):
        decoration_shader = get_default_decoration_shader()
        self.background_decoration_group = self.decoration_class(decoration_shader, order=0, parent=self._user_group)
        self.foreground_decoration_group = self.decoration_class(decoration_shader, order=2, parent=self._user_group)

    @property
    def group(self):
        return self._user_group

    @group.setter
    def group(self, group):
        self._user_group = group
        self._initialize_groups()
        self._update()

    @property
    def dpi(self):
        """Get DPI used by this layout.

        :type: float
        """
        return self._dpi

    @property
    def document(self):
        """Document to display.

         For :py:class:`~pyglet.text.layout.IncrementalTextLayout` it is
         far more efficient to modify a document in-place than to replace
         the document instance on the layout.

         :type: `AbstractDocument`
         """
        return self._document

    @document.setter
    def document(self, document):
        if self._document:
            self._document.remove_handlers(self)
            self._uninit_document()
        document.push_handlers(self)
        self._document = document
        self._init_document()

    @property
    def batch(self):
        """The Batch that this Layout is assigned to.

        If no Batch is assigned, an internal Batch is
        created and used.

        :type: :py:class:`~pyglet.graphics.Batch`

        """
        return self._batch

    @batch.setter
    def batch(self, batch):
        if self._batch == batch:
            return

        if batch is None:
            self._batch = graphics.Batch()
            self._own_batch = True
            self._update()
        elif batch is not None:
            self._batch = batch
            self._own_batch = False
            self._update()

    @property
    def x(self):
        """X coordinate of the layout.

        See also :py:attr:`~pyglet.text.layout.TextLayout.anchor_x`.

        :type: int
        """
        return self._x

    @x.setter
    def x(self, x):
        self._set_x(x)

    def _set_x(self, x):
        if self._boxes:
            self._x = x
            self._update()
        else:
            dx = x - self._x
            for vertex_list in self._vertex_lists:
                vertices = vertex_list.position[:]
                vertices[::2] = [x + dx for x in vertices[::2]]
                vertex_list.position[:] = vertices
            self._x = x

    @property
    def y(self):
        """Y coordinate of the layout.

        See also `anchor_y`.

        :type: int
        """
        return self._y

    @y.setter
    def y(self, y):
        self._set_y(y)

    def _set_y(self, y):
        if self._boxes:
            self._y = y
            self._update()
        else:
            dy = y - self._y
            for vertex_list in self._vertex_lists:
                vertices = vertex_list.position[:]
                vertices[1::2] = [y + dy for y in vertices[1::2]]
                vertex_list.position[:] = vertices
            self._y = y

    @property
    def position(self):
        """The (X, Y) coordinates of the layout, as a tuple.

        See also :py:attr:`~pyglet.text.layout.TextLayout.anchor_x`,
        and :py:attr:`~pyglet.text.layout.TextLayout.anchor_y`.

        :type: (int, int)
        """
        return self._x, self._y

    @position.setter
    def position(self, values):
        x, y = values
        if self._boxes:
            self._x = x
            self._y = y
            self._update()
        else:
            dx = x - self._x
            dy = y - self._y
            for vertex_list in self._vertex_lists:
                vertices = vertex_list.position[:]
                vertices[::2] = [x + dx for x in vertices[::2]]
                vertices[1::2] = [y + dy for y in vertices[1::2]]
                vertex_list.position[:] = vertices
            self._x = x
            self._y = y

    @property
    def visible(self):
        """True if the layout will be drawn.

        :type: bool
        """
        return self._visible

    @visible.setter
    def visible(self, value):
        if value != self._visible:
            self._visible = value

            if value:
                self._update()
            else:
                self.delete()

    @property
    def width(self):
        """Width of the layout.

        This property has no effect if `multiline` is False or `wrap_lines` is False.

        :type: int
        """
        return self._width

    @width.setter
    def width(self, width):
        self._width = width
        self._wrap_lines_invariant()
        self._update()

    @property
    def height(self):
        """Height of the layout.

        :type: int
        """
        return self._height

    @height.setter
    def height(self, height):
        self._height = height
        self._update()

    @property
    def multiline(self):
        """Set if multiline layout is enabled.

        If multiline is False, newline and paragraph characters are ignored and
        text is not word-wrapped.
        If True, the text is word-wrapped only if the `wrap_lines` is True.

        :type: bool
        """
        return self._multiline

    @multiline.setter
    def multiline(self, multiline):
        self._multiline = multiline
        self._wrap_lines_invariant()
        self._update()

    @property
    def anchor_x(self):
        """Horizontal anchor alignment.

        This property determines the meaning of the `x` coordinate.
        It is one of the enumerants:

        ``"left"`` (default)
            The X coordinate gives the position of the left edge of the layout.
        ``"center"``
            The X coordinate gives the position of the center of the layout.
        ``"right"``
            The X coordinate gives the position of the right edge of the layout.

        For the purposes of calculating the position resulting from this
        alignment, the width of the layout is taken to be `width` if `multiline`
        is True and `wrap_lines` is True, otherwise `content_width`.

        :type: str
        """
        return self._anchor_x

    @anchor_x.setter
    def anchor_x(self, anchor_x):
        self._anchor_x = anchor_x
        self._update()

    @property
    def anchor_y(self):
        """Vertical anchor alignment.

        This property determines the meaning of the `y` coordinate.
        It is one of the enumerants:

        ``"top"``
            The Y coordinate gives the position of the top edge of the layout.
        ``"center"``
            The Y coordinate gives the position of the center of the layout.
        ``"baseline"``
            The Y coordinate gives the position of the baseline of the first
            line of text in the layout.
        ``"bottom"`` (default)
            The Y coordinate gives the position of the bottom edge of the layout.

        For the purposes of calculating the position resulting from this
        alignment, the height of the layout is taken to be the smaller of
        `height` and `content_height`.

        See also `content_valign`.

        :type: str
        """
        return self._anchor_y

    @anchor_y.setter
    def anchor_y(self, anchor_y):
        self._anchor_y = anchor_y
        self._update()

    @property
    def content_valign(self):
        """Vertical alignment of content within larger layout box.

        This property determines how content is positioned within the layout
        box when ``content_height`` is less than ``height``.  It is one
        of the enumerants:

        ``top`` (default)
            Content is aligned to the top of the layout box.
        ``center``
            Content is centered vertically within the layout box.
        ``bottom``
            Content is aligned to the bottom of the layout box.

        This property has no effect when ``content_height`` is greater
        than ``height`` (in which case the content is aligned to the top) or when
        ``height`` is ``None`` (in which case there is no vertical layout box
        dimension).

        :type: str
        """
        return self._content_valign

    @content_valign.setter
    def content_valign(self, content_valign):
        self._content_valign = content_valign
        self._update()

    def _wrap_lines_invariant(self):
        self._wrap_lines = self._multiline and self._wrap_lines_flag
        assert not self._wrap_lines or self._width, \
            "When the parameters 'multiline' and 'wrap_lines' are True, the parameter 'width' must be a number."

    def parse_distance(self, distance):
        if distance is None:
            return None
        return _parse_distance(distance, self._dpi)

    def begin_update(self):
        """Indicate that a number of changes to the layout or document
        are about to occur.

        Changes to the layout or document between calls to `begin_update` and
        `end_update` do not trigger any costly relayout of text.  Relayout of
        all changes is performed when `end_update` is called.

        Note that between the `begin_update` and `end_update` calls, values
        such as `content_width` and `content_height` are undefined (i.e., they
        may or may not be updated to reflect the latest changes).
        """
        self._update_enabled = False

    def end_update(self):
        """Perform pending layout changes since `begin_update`.

        See `begin_update`.
        """
        self._update_enabled = True
        self._update()

    def delete(self):
        """Remove this layout from its batch.
        """
        for vertex_list in self._vertex_lists:
            vertex_list.delete()
        self._vertex_lists.clear()

        for box in self._boxes:
            box.delete(self)
        self._boxes.clear()

    def draw(self):
        """Draw this text layout.

        Note that this method performs very badly if a batch was supplied to
        the constructor.  If you add this layout to a batch, you should
        ideally use only the batch's draw method.
        """
        if self._own_batch:
            self._batch.draw()
        else:
            self._batch.draw_subset(self._vertex_lists)

    def _get_lines(self):
        len_text = len(self._document.text)
        glyphs = self._get_glyphs()
        owner_runs = runlist.RunList(len_text, None)
        self._get_owner_runs(owner_runs, glyphs, 0, len_text)
        lines = [line for line in self._flow_glyphs(glyphs, owner_runs, 0, len_text)]
        self.content_width = 0
        self._flow_lines(lines, 0, len(lines))
        return lines

    def _update(self):
        if not self._update_enabled:
            return

        for _vertex_list in self._vertex_lists:
            _vertex_list.delete()
        for box in self._boxes:
            box.delete(self)
        self._vertex_lists = []
        self._boxes = []
        self.group_cache.clear()

        if not self._document or not self._document.text:
            return

        lines = self._get_lines()

        colors_iter = self._document.get_style_runs('color')
        background_iter = self._document.get_style_runs('background_color')

        left = self._get_left()
        top = self._get_top(lines)

        context = _StaticLayoutContext(self, self._document, colors_iter, background_iter)
        for line in lines:
            self._create_vertex_lists(left + line.x, top + line.y, line.start, line.boxes, context)

    def _update_color(self):
        colors_iter = self._document.get_style_runs('color')
        colors = []
        for start, end, color in colors_iter.ranges(0, colors_iter.end):
            if color is None:
                color = (0, 0, 0, 255)
            colors.extend(color * ((end - start) * 4))

        start = 0
        for _vertex_list in self._vertex_lists:
            _vertex_list.colors = colors[start:start + len(_vertex_list.colors)]
            start += len(_vertex_list.colors)

    def _get_left(self):
        if self._multiline:
            width = self._width if self._wrap_lines else self.content_width
        else:
            width = self.content_width

        if self._anchor_x == 'left':
            return self._x
        elif self._anchor_x == 'center':
            return self._x - width // 2
        elif self._anchor_x == 'right':
            return self._x - width
        else:
            assert False, '`anchor_x` must be either "left", "center", or "right".'

    def _get_top(self, lines):
        if self._height is None:
            height = self.content_height
            offset = 0
        else:
            height = self._height
            if self._content_valign == 'top':
                offset = 0
            elif self._content_valign == 'bottom':
                offset = max(0, self._height - self.content_height)
            elif self._content_valign == 'center':
                offset = max(0, self._height - self.content_height) // 2
            else:
                assert False, '`content_valign` must be either "top", "bottom", or "center".'

        if self._anchor_y == 'top':
            return self._y - offset
        elif self._anchor_y == 'baseline':
            return self._y + lines[0].ascent - offset
        elif self._anchor_y == 'bottom':
            return self._y + height - offset
        elif self._anchor_y == 'center':
            if len(lines) == 1 and self._height is None:
                # This "looks" more centered than considering all of the descent.
                line = lines[0]
                return self._y + line.ascent // 2 - line.descent // 4
            else:
                return self._y + height // 2 - offset
        else:
            assert False, '`anchor_y` must be either "top", "bottom", "center", or "baseline".'

    def _get_bottom(self, lines):
        height = self._height or self.content_height

        if self._anchor_y == 'top':
            return self._y - height
        elif self._anchor_y == 'bottom':
            return self._y
        elif self._anchor_y == 'center':
            return self._y - height // 2
        elif self._anchor_y == 'baseline':
            return self._y - height + lines[0].ascent
        else:
            assert False, '`anchor_y` must be either "top", "bottom", "center", or "baseline".'

    def _init_document(self):
        self._update()

    def _uninit_document(self):
        pass

    def on_insert_text(self, start, text):
        """Event handler for `AbstractDocument.on_insert_text`.

        The event handler is bound by the text layout; there is no need for
        applications to interact with this method.
        """
        if self._visible:
            self._init_document()
        else:
            if self.document.text:
                # Update content width and height, since text may change while hidden.
                self._get_lines()

    def on_delete_text(self, start, end):
        """Event handler for `AbstractDocument.on_delete_text`.

        The event handler is bound by the text layout; there is no need for
        applications to interact with this method.
        """
        if self._visible:
            self._init_document()

    def on_style_text(self, start, end, attributes):
        """Event handler for `AbstractDocument.on_style_text`.

        The event handler is bound by the text layout; there is no need for
        applications to interact with this method.
        """
        if len(attributes) == 1 and 'color' in attributes.keys():
            self._update_color()
        else:
            self._init_document()

    def _get_glyphs(self):
        glyphs = []
        runs = runlist.ZipRunIterator((
            self._document.get_font_runs(dpi=self._dpi),
            self._document.get_element_runs()))
        text = self._document.text
        for start, end, (font, element) in runs.ranges(0, len(text)):
            if element:
                glyphs.append(_InlineElementBox(element))
            else:
                glyphs.extend(font.get_glyphs(text[start:end]))
        return glyphs

    def _get_owner_runs(self, owner_runs, glyphs, start, end):
        owner = glyphs[start].owner
        run_start = start
        # TODO avoid glyph slice on non-incremental
        for i, glyph in enumerate(glyphs[start:end]):
            if owner != glyph.owner:
                owner_runs.set_run(run_start, i + start, owner)
                owner = glyph.owner
                run_start = i + start
        owner_runs.set_run(run_start, end, owner)

    def _flow_glyphs_wrap(self, glyphs, owner_runs, start, end):
        """Word-wrap styled text into lines of fixed width.

        Fits `glyphs` in range `start` to `end` into `_Line` s which are
        then yielded.
        """
        owner_iterator = owner_runs.get_run_iterator().ranges(start, end)

        font_iterator = self._document.get_font_runs(dpi=self._dpi)

        align_iterator = runlist.FilteredRunIterator(self._document.get_style_runs('align'),
                                                     lambda value: value in ('left', 'right', 'center'),
                                                     'left')
        if self._width is None:
            wrap_iterator = runlist.ConstRunIterator(len(self.document.text), False)
        else:
            wrap_iterator = runlist.FilteredRunIterator(self._document.get_style_runs('wrap'),
                                                        lambda value: value in (True, False, 'char', 'word'),
                                                        True)
        margin_left_iterator = runlist.FilteredRunIterator(self._document.get_style_runs('margin_left'),
                                                           lambda value: value is not None, 0)
        margin_right_iterator = runlist.FilteredRunIterator(self._document.get_style_runs('margin_right'),
                                                            lambda value: value is not None, 0)
        indent_iterator = runlist.FilteredRunIterator(self._document.get_style_runs('indent'),
                                                      lambda value: value is not None, 0)
        kerning_iterator = runlist.FilteredRunIterator(self._document.get_style_runs('kerning'),
                                                       lambda value: value is not None, 0)
        tab_stops_iterator = runlist.FilteredRunIterator(self._document.get_style_runs('tab_stops'),
                                                         lambda value: value is not None, [])
        line = _Line(start)
        line.align = align_iterator[start]
        line.margin_left = self.parse_distance(margin_left_iterator[start])
        line.margin_right = self.parse_distance(margin_right_iterator[start])
        if start == 0 or self.document.text[start - 1] in u'\n\u2029':
            line.paragraph_begin = True
            line.margin_left += self.parse_distance(indent_iterator[start])
        wrap = wrap_iterator[start]
        if self._wrap_lines:
            width = self._width - line.margin_left - line.margin_right

        # Current right-most x position in line being laid out.
        x = 0

        # Boxes accumulated but not yet committed to a line.
        run_accum = []
        run_accum_width = 0

        # Amount of whitespace accumulated at end of line
        eol_ws = 0

        # Iterate over glyph owners (texture states); these form GlyphBoxes,
        # but broken into lines.
        font = None
        for start, end, owner in owner_iterator:
            font = font_iterator[start]

            # Glyphs accumulated in this owner but not yet committed to a
            # line.
            owner_accum = []
            owner_accum_width = 0

            # Glyphs accumulated in this owner AND also committed to the
            # current line (some whitespace has followed all of the committed
            # glyphs).
            owner_accum_commit = []
            owner_accum_commit_width = 0

            # Ignore kerning of first glyph on each line
            nokern = True

            # Current glyph index
            index = start

            # Iterate over glyphs in this owner run.  `text` is the
            # corresponding character data for the glyph, and is used to find
            # whitespace and newlines.
            for (text, glyph) in zip(self.document.text[start:end], glyphs[start:end]):
                if nokern:
                    kern = 0
                    nokern = False
                else:
                    kern = self.parse_distance(kerning_iterator[index])

                if wrap != 'char' and text in u'\u0020\u200b\t':
                    # Whitespace: commit pending runs to this line.
                    for run in run_accum:
                        line.add_box(run)
                    run_accum = []
                    run_accum_width = 0

                    if text == '\t':
                        # Fix up kern for this glyph to align to the next tab stop
                        for tab_stop in tab_stops_iterator[index]:
                            tab_stop = self.parse_distance(tab_stop)
                            if tab_stop > x + line.margin_left:
                                break
                        else:
                            # No more tab stops, tab to 100 pixels
                            tab = 50.
                            tab_stop = (((x + line.margin_left) // tab) + 1) * tab
                        kern = int(tab_stop - x - line.margin_left - glyph.advance)

                    owner_accum.append((kern, glyph))
                    owner_accum_commit.extend(owner_accum)
                    owner_accum_commit_width += owner_accum_width + glyph.advance + kern
                    eol_ws += glyph.advance + kern

                    owner_accum = []
                    owner_accum_width = 0

                    x += glyph.advance + kern
                    index += 1

                    # The index at which the next line will begin (the
                    # current index, because this is the current best
                    # breakpoint).
                    next_start = index
                else:
                    new_paragraph = text in u'\n\u2029'
                    new_line = (text == u'\u2028') or new_paragraph
                    if (wrap and self._wrap_lines and x + kern + glyph.advance >= width) or new_line:
                        # Either the pending runs have overflowed the allowed
                        # line width or a newline was encountered.  Either
                        # way, the current line must be flushed.

                        if new_line or wrap == 'char':
                            # Forced newline or char-level wrapping.  Commit
                            # everything pending without exception.
                            for run in run_accum:
                                line.add_box(run)
                            run_accum = []
                            run_accum_width = 0
                            owner_accum_commit.extend(owner_accum)
                            owner_accum_commit_width += owner_accum_width
                            owner_accum = []
                            owner_accum_width = 0

                            line.length += 1
                            next_start = index
                            if new_line:
                                next_start += 1

                        # Create the _GlyphBox for the committed glyphs in the
                        # current owner.
                        if owner_accum_commit:
                            line.add_box(_GlyphBox(owner, font, owner_accum_commit, owner_accum_commit_width))
                            owner_accum_commit = []
                            owner_accum_commit_width = 0

                        if new_line and not line.boxes:
                            # Empty line: give it the current font's default
                            # line-height.
                            line.ascent = font.ascent
                            line.descent = font.descent

                        # Flush the line, unless nothing got committed, in
                        # which case it's a really long string of glyphs
                        # without any breakpoints (in which case it will be
                        # flushed at the earliest breakpoint, not before
                        # something is committed).
                        if line.boxes or new_line:
                            # Trim line width of whitespace on right-side.
                            line.width -= eol_ws
                            if new_paragraph:
                                line.paragraph_end = True
                            yield line
                            try:
                                line = _Line(next_start)
                                line.align = align_iterator[next_start]
                                line.margin_left = self.parse_distance(margin_left_iterator[next_start])
                                line.margin_right = self.parse_distance(margin_right_iterator[next_start])
                            except IndexError:
                                # XXX This used to throw StopIteration in some cases, causing the
                                # final part of this method not to be executed. Refactoring
                                # required to fix this
                                return
                            if new_paragraph:
                                line.paragraph_begin = True

                            # Remove kern from first glyph of line
                            if run_accum and hasattr(run_accum, 'glyphs') and run_accum.glyphs:
                                k, g = run_accum[0].glyphs[0]
                                run_accum[0].glyphs[0] = (0, g)
                                run_accum_width -= k
                            elif owner_accum:
                                k, g = owner_accum[0]
                                owner_accum[0] = (0, g)
                                owner_accum_width -= k
                            else:
                                nokern = True

                            x = run_accum_width + owner_accum_width
                            if self._wrap_lines:
                                width = self._width - line.margin_left - line.margin_right

                    if isinstance(glyph, _AbstractBox):
                        # Glyph is already in a box. XXX Ignore kern?
                        run_accum.append(glyph)
                        run_accum_width += glyph.advance
                        x += glyph.advance
                    elif new_paragraph:
                        # New paragraph started, update wrap style
                        wrap = wrap_iterator[next_start]
                        line.margin_left += self.parse_distance(indent_iterator[next_start])
                        if self._wrap_lines:
                            width = self._width - line.margin_left - line.margin_right
                    elif not new_line:
                        # If the glyph was any non-whitespace, non-newline
                        # character, add it to the pending run.
                        owner_accum.append((kern, glyph))
                        owner_accum_width += glyph.advance + kern
                        x += glyph.advance + kern
                    index += 1
                    eol_ws = 0

            # The owner run is finished; create GlyphBoxes for the committed
            # and pending glyphs.
            if owner_accum_commit:
                line.add_box(_GlyphBox(owner, font, owner_accum_commit, owner_accum_commit_width))
            if owner_accum:
                run_accum.append(_GlyphBox(owner, font, owner_accum, owner_accum_width))
                run_accum_width += owner_accum_width

        # All glyphs have been processed: commit everything pending and flush
        # the final line.
        for run in run_accum:
            line.add_box(run)

        if not line.boxes:
            # Empty line gets font's line-height
            if font is None:
                font = self._document.get_font(0, dpi=self._dpi)
            line.ascent = font.ascent
            line.descent = font.descent

        yield line

    def _flow_glyphs_single_line(self, glyphs, owner_runs, start, end):
        owner_iterator = owner_runs.get_run_iterator().ranges(start, end)
        font_iterator = self.document.get_font_runs(dpi=self._dpi)
        kern_iterator = runlist.FilteredRunIterator(self.document.get_style_runs('kerning'),
                                                    lambda value: value is not None, 0)

        line = _Line(start)
        font = font_iterator[0]

        if self._width:
            align_iterator = runlist.FilteredRunIterator(
                self._document.get_style_runs('align'),
                lambda value: value in ('left', 'right', 'center'),
                'left')
            line.align = align_iterator[start]

        for start, end, owner in owner_iterator:
            font = font_iterator[start]
            width = 0
            owner_glyphs = []
            for kern_start, kern_end, kern in kern_iterator.ranges(start, end):
                gs = glyphs[kern_start:kern_end]
                width += sum([g.advance for g in gs])
                width += kern * (kern_end - kern_start)
                owner_glyphs.extend(zip([kern] * (kern_end - kern_start), gs))
            if owner is None:
                # Assume glyphs are already boxes.
                for kern, glyph in owner_glyphs:
                    line.add_box(glyph)
            else:
                line.add_box(_GlyphBox(owner, font, owner_glyphs, width))

        if not line.boxes:
            line.ascent = font.ascent
            line.descent = font.descent

        line.paragraph_begin = line.paragraph_end = True

        yield line

    def _flow_lines(self, lines, start, end):
        margin_top_iterator = runlist.FilteredRunIterator(self._document.get_style_runs('margin_top'),
                                                          lambda value: value is not None, 0)
        margin_bottom_iterator = runlist.FilteredRunIterator(self._document.get_style_runs('margin_bottom'),
                                                             lambda value: value is not None, 0)
        line_spacing_iterator = self._document.get_style_runs('line_spacing')
        leading_iterator = runlist.FilteredRunIterator(self._document.get_style_runs('leading'),
                                                       lambda value: value is not None, 0)

        if start == 0:
            y = 0
        else:
            line = lines[start - 1]
            line_spacing = self.parse_distance(line_spacing_iterator[line.start])
            leading = self.parse_distance(leading_iterator[line.start])

            y = line.y
            if line_spacing is None:
                y += line.descent
            if line.paragraph_end:
                y -= self.parse_distance(margin_bottom_iterator[line.start])

        line_index = start
        for line in lines[start:]:
            if line.paragraph_begin:
                y -= self.parse_distance(margin_top_iterator[line.start])
                line_spacing = self.parse_distance(line_spacing_iterator[line.start])
                leading = self.parse_distance(leading_iterator[line.start])
            else:
                y -= leading

            if line_spacing is None:
                y -= line.ascent
            else:
                y -= line_spacing
            if line.align == 'left' or line.width > self.width:
                line.x = line.margin_left
            elif line.align == 'center':
                line.x = (self.width - line.margin_left - line.margin_right - line.width) // 2 + line.margin_left
            elif line.align == 'right':
                line.x = self.width - line.margin_right - line.width

            self.content_width = max(self.content_width, line.width + line.margin_left)

            if line.y == y and line_index >= end:
                # Early exit: all invalidated lines have been reflowed and the
                # next line has no change (therefore subsequent lines do not
                # need to be changed).
                break
            line.y = y

            if line_spacing is None:
                y += line.descent
            if line.paragraph_end:
                y -= self.parse_distance(margin_bottom_iterator[line.start])

            line_index += 1
        else:
            self.content_height = -y

        return line_index

    def _create_vertex_lists(self, x, y, i, boxes, context):
        for box in boxes:
            box.place(self, i, x, y, context)
            x += box.advance
            i += box.length


class ScrollableTextLayout(TextLayout):
    """Display text in a scrollable viewport.

    This class does not display a scrollbar or handle scroll events; it merely
    clips the text that would be drawn in :py:func:`~pyglet.text.layout.TextLayout`
    to the bounds of the layout given by `x`, `y`, `width` and `height`;
    and offsets the text by a scroll offset.

    Use `view_x` and `view_y` to scroll the text within the viewport.
    """

    group_class = ScrollableTextLayoutGroup
    decoration_class = ScrollableTextDecorationGroup

    _translate_x = 0
    _translate_y = 0

    def __init__(self, document, width, height, multiline=False, dpi=None, batch=None, group=None, wrap_lines=True):
        super().__init__(document, width, height, multiline, dpi, batch, group, wrap_lines)
        self._update_scissor_area()

    def _update_scissor_area(self):
        if not self.document.text:
            return
        area = self._get_left(), self._get_bottom(self._get_lines()), self._width, self._height
        for group in self.group_cache.values():
            group.scissor_area = area

    def _update(self):
        super()._update()
        self._update_scissor_area()

    # Properties

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, x):
        super()._set_x(x)
        self._update_scissor_area()

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, y):
        super()._set_y(y)
        self._update_scissor_area()

    @property
    def position(self):
        return self._x, self._y

    @position.setter
    def position(self, position):
        self.x, self.y = position

    @property
    def anchor_x(self):
        return self._anchor_x

    @anchor_x.setter
    def anchor_x(self, anchor_x):
        self._anchor_x = anchor_x
        super()._update()
        self._update_scissor_area()

    @property
    def anchor_y(self):
        return self._anchor_y

    @anchor_y.setter
    def anchor_y(self, anchor_y):
        self._anchor_y = anchor_y
        super()._update()
        self._update_scissor_area()

    # Offset of content within viewport

    def _update_translation(self):
        for _vertex_list in self._vertex_lists:
            _vertex_list.translation[:] = (-self._translate_x, -self._translate_y) * _vertex_list.count

    @property
    def view_x(self):
        """Horizontal scroll offset.

            The initial value is 0, and the left edge of the text will touch the left
            side of the layout bounds.  A positive value causes the text to "scroll"
            to the right.  Values are automatically clipped into the range
            ``[0, content_width - width]``

            :type: int
        """
        return self._translate_x

    @view_x.setter
    def view_x(self, view_x):
        self._translate_x = max(0, min(self.content_width - self._width, view_x))
        self._update_translation()

    @property
    def view_y(self):
        """Vertical scroll offset.

            The initial value is 0, and the top of the text will touch the top of the
            layout bounds (unless the content height is less than the layout height,
            in which case `content_valign` is used).

            A negative value causes the text to "scroll" upwards.  Values outside of
            the range ``[height - content_height, 0]`` are automatically clipped in
            range.

            :type: int
        """
        return self._translate_y

    @view_y.setter
    def view_y(self, view_y):
        # view_y must be negative.
        self._translate_y = min(0, max(self.height - self.content_height, view_y))
        self._update_translation()


class IncrementalTextLayout(TextLayout, EventDispatcher):
    """Displayed text suitable for interactive editing and/or scrolling
    large documents.

    Unlike :py:func:`~pyglet.text.layout.TextLayout` and
    :py:class:`~pyglet.text.layout.ScrollableTextLayout`, this class generates
    vertex lists only for lines of text that are visible.  As the document is
    scrolled, vertex lists are deleted and created as appropriate to keep
    video memory usage to a minimum and improve rendering speed.

    Changes to the document are quickly reflected in this layout, as only the
    affected line(s) are reflowed.  Use `begin_update` and `end_update` to
    further reduce the amount of processing required.

    The layout can also display a text selection (text with a different
    background color).  The :py:class:`~pyglet.text.caret.Caret` class implements
    a visible text cursor and provides event handlers for scrolling, selecting and
    editing text in an incremental text layout.
    """

    _selection_start = 0
    _selection_end = 0
    _selection_color = [255, 255, 255, 255]
    _selection_background_color = [46, 106, 197, 255]

    group_class = IncrementalTextLayoutGroup
    decoration_class = IncrementalTextDecorationGroup

    _translate_x = 0
    _translate_y = 0

    def __init__(self, document, width, height, multiline=False, dpi=None, batch=None, group=None, wrap_lines=True):

        self.glyphs = []
        self.lines = []

        self.invalid_glyphs = _InvalidRange()
        self.invalid_flow = _InvalidRange()
        self.invalid_lines = _InvalidRange()
        self.invalid_style = _InvalidRange()
        self.invalid_vertex_lines = _InvalidRange()
        self.visible_lines = _InvalidRange()

        self.owner_runs = runlist.RunList(0, None)

        super().__init__(document, width, height, multiline, dpi, batch, group, wrap_lines)
        self._update_translation()
        self._update_scissor_area()

    def _update_scissor_area(self):
        if not self.document.text:
            return
        area = self._get_left(), self._get_bottom(self._get_lines()), self._width, self._height
        for group in self.group_cache.values():
            group.scissor_area = area

    def _init_document(self):
        assert self._document, 'Cannot remove document from IncrementalTextLayout'
        self.on_insert_text(0, self._document.text)

    def _uninit_document(self):
        self.on_delete_text(0, len(self._document.text))

    def _get_lines(self):
        return self.lines

    def delete(self):
        for line in self.lines:
            line.delete(self)
        self._batch = None
        if self._document:
            self._document.remove_handlers(self)
        self._document = None

    def on_insert_text(self, start, text):
        len_text = len(text)
        self.glyphs[start:start] = [None] * len_text

        self.invalid_glyphs.insert(start, len_text)
        self.invalid_flow.insert(start, len_text)
        self.invalid_style.insert(start, len_text)

        self.owner_runs.insert(start, len_text)

        for line in self.lines:
            if line.start >= start:
                line.start += len_text

        self._update()

    def on_delete_text(self, start, end):
        self.glyphs[start:end] = []

        self.invalid_glyphs.delete(start, end)
        self.invalid_flow.delete(start, end)
        self.invalid_style.delete(start, end)

        self.owner_runs.delete(start, end)

        size = end - start
        for line in self.lines:
            if line.start > start:
                line.start = max(line.start - size, start)

        if start == 0:
            self.invalid_flow.invalidate(0, 1)
        else:
            self.invalid_flow.invalidate(start - 1, start)

        self._update()

    def on_style_text(self, start, end, attributes):
        if 'font_name' in attributes or 'font_size' in attributes or 'bold' in attributes or 'italic' in attributes:
            self.invalid_glyphs.invalidate(start, end)
        elif 'color' in attributes or 'background_color' in attributes:
            self.invalid_style.invalidate(start, end)
        else:  # Attributes that change flow
            self.invalid_flow.invalidate(start, end)

        self._update()

    def _update(self):
        if not self._update_enabled:
            return

        trigger_update_event = (self.invalid_glyphs.is_invalid() or
                                self.invalid_flow.is_invalid() or
                                self.invalid_lines.is_invalid())

        # Special care if there is no text:
        if not self.glyphs:
            for line in self.lines:
                line.delete(self)
            del self.lines[:]
            self.lines.append(_Line(0))
            font = self.document.get_font(0, dpi=self._dpi)
            self.lines[0].ascent = font.ascent
            self.lines[0].descent = font.descent
            self.lines[0].paragraph_begin = self.lines[0].paragraph_end = True
            self.invalid_lines.invalidate(0, 1)

        self._update_glyphs()
        self._update_flow_glyphs()
        self._update_flow_lines()
        self._update_visible_lines()
        self._update_vertex_lists()

        # Reclamp view_y in case content height has changed and reset top of content.
        # self.view_y = self._translate_y
        # self._update_translation()

        if trigger_update_event:
            self.dispatch_event('on_layout_update')

    def _update_glyphs(self):
        invalid_start, invalid_end = self.invalid_glyphs.validate()

        if invalid_end - invalid_start <= 0:
            return

        # Find grapheme breaks and extend glyph range to encompass.
        text = self.document.text
        while invalid_start > 0:
            if grapheme_break(text[invalid_start - 1], text[invalid_start]):
                break
            invalid_start -= 1

        len_text = len(text)
        while invalid_end < len_text:
            if grapheme_break(text[invalid_end - 1], text[invalid_end]):
                break
            invalid_end += 1

        # Update glyphs
        runs = runlist.ZipRunIterator((
            self._document.get_font_runs(dpi=self._dpi),
            self._document.get_element_runs()))
        for start, end, (font, element) in runs.ranges(invalid_start, invalid_end):
            if element:
                self.glyphs[start] = _InlineElementBox(element)
            else:
                text = self.document.text[start:end]
                self.glyphs[start:end] = font.get_glyphs(text)

        # Update owner runs
        self._get_owner_runs(self.owner_runs, self.glyphs, invalid_start, invalid_end)

        # Updated glyphs need flowing
        self.invalid_flow.invalidate(invalid_start, invalid_end)

    def _update_flow_glyphs(self):
        invalid_start, invalid_end = self.invalid_flow.validate()

        if invalid_end - invalid_start <= 0:
            return

        # Find first invalid line
        line_index = 0
        for i, line in enumerate(self.lines):
            if line.start >= invalid_start:
                break
            line_index = i

        # Flow from previous line; fixes issue with adding a space into
        # overlong line (glyphs before space would then flow back onto
        # previous line).
        # TODO:  Could optimise this by keeping track of where the overlong lines are.
        line_index = max(0, line_index - 1)

        # (No need to find last invalid line; the update loop below stops
        # calling the flow generator when no more changes are necessary.)

        try:
            line = self.lines[line_index]
            invalid_start = min(invalid_start, line.start)
            line.delete(self)
            self.lines[line_index] = _Line(invalid_start)
            self.invalid_lines.invalidate(line_index, line_index + 1)
        except IndexError:
            line_index = 0
            invalid_start = 0
            line = _Line(0)
            self.lines.append(line)
            self.invalid_lines.insert(0, 1)

        content_width_invalid = False
        next_start = invalid_start

        for line in self._flow_glyphs(self.glyphs, self.owner_runs, invalid_start, len(self._document.text)):
            try:
                old_line = self.lines[line_index]
                old_line.delete(self)
                old_line_width = old_line.width + old_line.margin_left
                new_line_width = line.width + line.margin_left
                if old_line_width == self.content_width and new_line_width < old_line_width:
                    content_width_invalid = True
                self.lines[line_index] = line
                self.invalid_lines.invalidate(line_index, line_index + 1)
            except IndexError:
                self.lines.append(line)
                self.invalid_lines.insert(line_index, 1)

            next_start = line.start + line.length
            line_index += 1

            try:
                next_line = self.lines[line_index]
                if next_start == next_line.start and next_start > invalid_end:
                    # No more lines need to be modified, early exit.
                    break
            except IndexError:
                pass
        else:
            # The last line is at line_index - 1, if there are any more lines
            # after that they are stale and need to be deleted.
            if next_start == len(self._document.text) and line_index > 0:
                for line in self.lines[line_index:]:
                    old_line_width = old_line.width + old_line.margin_left
                    if old_line_width == self.content_width:
                        content_width_invalid = True
                    line.delete(self)
                del self.lines[line_index:]

        if content_width_invalid:
            # Rescan all lines to look for the new maximum content width
            content_width = 0
            for line in self.lines:
                content_width = max(line.width + line.margin_left, content_width)
            self.content_width = content_width

    def _update_flow_lines(self):
        invalid_start, invalid_end = self.invalid_lines.validate()
        if invalid_end - invalid_start <= 0:
            return

        invalid_end = self._flow_lines(self.lines, invalid_start, invalid_end)

        # Invalidate lines that need new vertex lists.
        self.invalid_vertex_lines.invalidate(invalid_start, invalid_end)

    def _update_visible_lines(self):
        start = sys.maxsize
        end = 0

        for i, line in enumerate(self.lines):
            if line.y + line.descent < self._translate_y:
                start = min(start, i)
            if line.y + line.ascent > self._translate_y - self.height:
                end = max(end, i) + 1

        # Delete newly invisible lines
        for i in range(self.visible_lines.start, min(start, len(self.lines))):
            self.lines[i].delete(self)
        for i in range(end, min(self.visible_lines.end, len(self.lines))):
            self.lines[i].delete(self)

        # Invalidate newly visible lines
        self.invalid_vertex_lines.invalidate(start, self.visible_lines.start)
        self.invalid_vertex_lines.invalidate(self.visible_lines.end, end)

        self.visible_lines.start = start
        self.visible_lines.end = end

    def _update_vertex_lists(self):
        # Find lines that have been affected by style changes
        style_invalid_start, style_invalid_end = self.invalid_style.validate()
        self.invalid_vertex_lines.invalidate(
            self.get_line_from_position(style_invalid_start),
            self.get_line_from_position(style_invalid_end) + 1)

        invalid_start, invalid_end = self.invalid_vertex_lines.validate()
        if invalid_end - invalid_start <= 0:
            return

        colors_iter = self.document.get_style_runs('color')
        background_iter = self.document.get_style_runs('background_color')
        if self._selection_end - self._selection_start > 0:
            colors_iter = runlist.OverriddenRunIterator(
                colors_iter,
                self._selection_start,
                self._selection_end,
                self._selection_color)
            background_iter = runlist.OverriddenRunIterator(
                background_iter,
                self._selection_start,
                self._selection_end,
                self._selection_background_color)

        context = _IncrementalLayoutContext(self, self._document, colors_iter, background_iter)

        left = self._get_left()
        top = self._get_top(self.lines[invalid_start:invalid_end])

        for line in self.lines[invalid_start:invalid_end]:
            line.delete(self)
            context.line = line
            y = line.y

            # Early out if not visible
            if y + line.descent > self._translate_y:
                continue
            elif y + line.ascent < self._translate_y - self.height:
                break

            self._create_vertex_lists(left + line.x, top + y, line.start, line.boxes, context)

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, x):
        self._x = x
        self._uninit_document()
        self._init_document()
        self._update_scissor_area()

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, y):
        self._y = y
        self._uninit_document()
        self._init_document()
        self._update_scissor_area()

    @property
    def position(self):
        return self._x, self._y

    @position.setter
    def position(self, position):
        self._x, self._y = position
        self._uninit_document()
        self._init_document()
        self._update_scissor_area()

    @property
    def anchor_x(self):
        return self._anchor_x

    @anchor_x.setter
    def anchor_x(self, anchor_x):
        self._anchor_x = anchor_x
        self._update_scissor_area()
        self._init_document()

    @property
    def anchor_y(self):
        return self._anchor_y

    @anchor_y.setter
    def anchor_y(self, anchor_y):
        self._anchor_y = anchor_y
        self._update_scissor_area()
        self._init_document()

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, width):
        # Invalidate everything when width changes
        if width == self._width:
            return
        self._width = width
        self.invalid_flow.invalidate(0, len(self.document.text))
        self._update_scissor_area()

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, height):
        # Recalculate visible lines when height changes
        if height == self._height:
            return
        self._height = height
        if self._update_enabled:
            self._update_visible_lines()
            self._update_vertex_lists()

    @property
    def multiline(self):
        return self._multiline

    @multiline.setter
    def multiline(self, multiline):
        self.invalid_flow.invalidate(0, len(self.document.text))
        self._multiline = multiline
        self._wrap_lines_invariant()
        self._update()

    # Offset of content within viewport

    def _update_translation(self):
        for line in self.lines:
            for vlist in line.vertex_lists:
                vlist.translation[:] = (-self._translate_x, -self._translate_y) * vlist.count

    @property
    def view_x(self):
        """Horizontal scroll offset.

        The initial value is 0, and the left edge of the text will touch the left
        side of the layout bounds.  A positive value causes the text to "scroll"
        to the right.  Values are automatically clipped into the range
        ``[0, content_width - width]``

        :type: int
        """
        return self._translate_x

    @view_x.setter
    def view_x(self, view_x):
        self._translate_x = max(0, min(self.content_width - self._width, view_x))
        self._update_translation()

    @property
    def view_y(self):
        """Vertical scroll offset.

        The initial value is 0, and the top of the text will touch the top of the
        layout bounds (unless the content height is less than the layout height,
        in which case `content_valign` is used).

        A negative value causes the text to "scroll" upwards.  Values outside of
        the range ``[height - content_height, 0]`` are automatically clipped in
        range.

        :type: int
        """
        return self._translate_y

    @view_y.setter
    def view_y(self, view_y):
        # Invalidate invisible/visible lines when y scrolls
        # view_y must be negative.
        self._translate_y = min(0, max(self.height - self.content_height, view_y))
        self._update_translation()
        self._update_visible_lines()
        self._update_vertex_lists()

    # Visible selection

    def set_selection(self, start, end):
        """Set the text selection range.

        If ``start`` equals ``end`` no selection will be visible.

        :Parameters:
            `start` : int
                Starting character position of selection.
            `end` : int
                End of selection, exclusive.

        """
        start = max(0, start)
        end = min(end, len(self.document.text))
        if start == self._selection_start and end == self._selection_end:
            return

        if end > self._selection_start and start < self._selection_end:
            # Overlapping, only invalidate difference
            self.invalid_style.invalidate(min(start, self._selection_start), max(start, self._selection_start))
            self.invalid_style.invalidate(min(end, self._selection_end), max(end, self._selection_end))
        else:
            # Non-overlapping, invalidate both ranges
            self.invalid_style.invalidate(self._selection_start, self._selection_end)
            self.invalid_style.invalidate(start, end)

        self._selection_start = start
        self._selection_end = end

        self._update()

    @property
    def selection_start(self):
        """Starting position of the active selection.

        :see: `set_selection`

        :type: int
        """
        return self._selection_start

    @selection_start.setter
    def selection_start(self, start):
        self.set_selection(start, self._selection_end)

    @property
    def selection_end(self):
        """End position of the active selection (exclusive).

        :see: `set_selection`

        :type: int
        """
        return self._selection_end

    @selection_end.setter
    def selection_end(self, end):
        self.set_selection(self._selection_start, end)

    @property
    def selection_color(self):
        """Text color of active selection.

        The color is an RGBA tuple with components in range [0, 255].

        :type: (int, int, int, int)
        """
        return self._selection_color

    @selection_color.setter
    def selection_color(self, color):
        self._selection_color = color
        self.invalid_style.invalidate(self._selection_start, self._selection_end)

    @property
    def selection_background_color(self):
        """Background color of active selection.

        The color is an RGBA tuple with components in range [0, 255].

        :type: (int, int, int, int)
        """
        return self._selection_background_color

    @selection_background_color.setter
    def selection_background_color(self, background_color):
        self._selection_background_color = background_color
        self.invalid_style.invalidate(self._selection_start, self._selection_end)

    # Coordinate translation

    def get_position_from_point(self, x, y):
        """Get the closest document position to a point.

        :Parameters:
            `x` : int
                X coordinate
            `y` : int
                Y coordinate

        """
        line = self.get_line_from_point(x, y)
        return self.get_position_on_line(line, x)

    def get_point_from_position(self, position, line=None):
        """Get the X, Y coordinates of a position in the document.

        The position that ends a line has an ambiguous point: it can be either
        the end of the line, or the beginning of the next line.  You may
        optionally specify a line index to disambiguate the case.

        The resulting Y coordinate gives the baseline of the line.

        :Parameters:
            `position` : int
                Character position within document.
            `line` : int
                Line index.

        :rtype: (int, int)
        :return: (x, y)
        """
        if line is None:
            line = self.lines[0]
            for next_line in self.lines:
                if next_line.start > position:
                    break
                line = next_line
        else:
            line = self.lines[line]

        x = line.x

        baseline = self._document.get_style('baseline', max(0, position - 1))
        if baseline is None:
            baseline = 0
        else:
            baseline = self.parse_distance(baseline)

        position -= line.start
        for box in line.boxes:
            if position - box.length <= 0:
                x += box.get_point_in_box(position)
                break
            position -= box.length
            x += box.advance

        return x + self._translate_x, line.y + self._translate_y + baseline

    def get_line_from_point(self, x, y):
        """Get the closest line index to a point.

        :Parameters:
            `x` : int
                X coordinate.
            `y` : int
                Y coordinate.

        :rtype: int
        """
        x -= self._translate_x
        y -= self._translate_y

        line_index = 0
        for line in self.lines:
            if y > line.y + line.descent:
                break
            line_index += 1
        if line_index >= len(self.lines):
            line_index = len(self.lines) - 1
        return line_index

    def get_point_from_line(self, line):
        """Get the X, Y coordinates of a line index.

        :Parameters:
            `line` : int
                Line index.

        :rtype: (int, int)
        :return: (x, y)
        """
        line = self.lines[line]
        return line.x + self._translate_x, line.y + self._translate_y

    def get_line_from_position(self, position):
        """Get the line index of a character position in the document.

        :Parameters:
            `position` : int
                Document position.

        :rtype: int
        """
        line = -1
        for next_line in self.lines:
            if next_line.start > position:
                break
            line += 1
        return line

    def get_position_from_line(self, line):
        """Get the first document character position of a given line index.

        :Parameters:
            `line` : int
                Line index.

        :rtype: int
        """
        return self.lines[line].start + self._x

    def get_position_on_line(self, line, x):
        """Get the closest document position for a given line index and X
        coordinate.

        :Parameters:
            `line` : int
                Line index.
            `x` : int
                X coordinate.

        :rtype: int
        """
        line = self.lines[line]
        x -= self._x

        if x < line.x:
            return line.start

        position = line.start
        last_glyph_x = line.x
        for box in line.boxes:
            if 0 <= x - last_glyph_x < box.advance:
                position += box.get_position_in_box(x - last_glyph_x)
                break
            last_glyph_x += box.advance
            position += box.length

        return position

    def get_line_count(self):
        """Get the number of lines in the text layout.

        :rtype: int
        """
        return len(self.lines)

    def ensure_line_visible(self, line):
        """Adjust `view_y` so that the line with the given index is visible.

        :Parameters:
            `line` : int
                Line index.

        """
        line = self.lines[line]
        y1 = line.y + line.ascent
        y2 = line.y + line.descent
        if y1 > self.view_y:
            self.view_y = y1
        elif y2 < self.view_y - self.height:
            self.view_y = y2 + self.height

    def ensure_x_visible(self, x):
        """Adjust `view_x` so that the given X coordinate is visible.

        The X coordinate is given relative to the current `view_x`.

        :Parameters:
            `x` : int
                X coordinate

        """
        if x <= self.view_x + 10:
            self.view_x = x - 10
        elif x >= self.view_x + self.width:
            self.view_x = x - self.width + 10
        elif x >= self.view_x + self.width - 10 and self.content_width > self.width:
            self.view_x = x - self.width + 10

    if _is_pyglet_doc_run:
        def on_layout_update(self):
            """Some or all of the layout text was reflowed.

            Text reflow is caused by document edits or changes to the layout's
            size.  Changes to the layout's position or active selection, and
            certain document edits such as text color, do not cause a reflow.

            Handle this event to update the position of a graphical element
            that depends on the laid out position of a glyph or line.

            :event:
            """


IncrementalTextLayout.register_event_type('on_layout_update')
