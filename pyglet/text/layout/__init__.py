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
    and may overflow the layout width.

Other attributes can be used to store additional style information within the
document; they will be ignored by the built-in text classes.

"""
from __future__ import annotations

from pyglet.text.layout.base import (
    TextDecorationGroup,
    TextLayout,
    TextLayoutGroup,
    decoration_fragment_source,
    decoration_vertex_source,
    get_default_decoration_shader,
    get_default_image_layout_shader,
    get_default_layout_shader,
    layout_fragment_image_source,
    layout_fragment_source,
    layout_vertex_source,
)
from pyglet.text.layout.incremental import (
    IncrementalTextDecorationGroup,
    IncrementalTextLayout,
    IncrementalTextLayoutGroup,
)
from pyglet.text.layout.scrolling import ScrollableTextDecorationGroup, ScrollableTextLayout, ScrollableTextLayoutGroup

__all__ = ["TextLayout", "IncrementalTextLayout", "ScrollableTextLayout", "TextLayoutGroup", "TextDecorationGroup",
           "IncrementalTextLayoutGroup", "IncrementalTextDecorationGroup", "ScrollableTextLayoutGroup",
           "ScrollableTextDecorationGroup", "get_default_layout_shader", "get_default_image_layout_shader",
           "get_default_decoration_shader", "decoration_fragment_source", "layout_fragment_image_source",
           "layout_fragment_source", "layout_vertex_source", "decoration_vertex_source"]
