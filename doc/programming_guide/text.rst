.. _guide_text:

Displaying text
===============

pyglet provides the :py:mod:`~pyglet.text` module for displaying and editing
Unicode text. Font selection, font faces, metrics, and custom font files are
covered separately in :doc:`fonts`.

Simple text rendering
---------------------

The following complete example creates a window that displays
"Hello, World"  centered vertically and horizontally::

    window = pyglet.window.Window()
    label = pyglet.text.Label('Hello, world',
                              font_name='Times New Roman',
                              font_size=36,
                              x=window.width//2, y=window.height//2,
                              anchor_x='center', anchor_y='center')

    @window.event
    def on_draw():
        window.clear()
        label.draw()

    pyglet.app.run()

The example demonstrates the most common uses of text rendering:

* The font name and size are specified directly in the constructor.
  The ``weight``, ``style``, and ``stretch`` parameters select a font face;
  see :doc:`fonts`. The ``color`` parameter controls the text color.
* The position of the text is given by the ``x`` and ``y`` coordinates.  The
  meaning of these coordinates is given by the ``anchor_x`` and ``anchor_y``
  parameters.
* The actual drawing of the text to the screen is done with the
  :py:meth:`pyglet.text.Label.draw` method.  Labels can also be added to a
  graphics batch; see :ref:`guide_batched-rendering` for details.

The :py:func:`~pyglet.text.HTMLLabel` class is used similarly, but accepts
an HTML formatted string instead of parameters describing the style.
This allows the label to display text with mixed style::

    label = pyglet.text.HTMLLabel(
        '<font face="Times New Roman" size="4">Hello, <i>world</i></font>',
        x=window.width//2, y=window.height//2,
        anchor_x='center', anchor_y='center')

See :ref:`guide_formatted-text` for details on the subset of HTML that is
supported.

The document/layout model
-------------------------

The :py:func:`~pyglet.text.Label` class demonstrated above presents a
simplified interface to pyglet's complete text rendering capabilities.
The underlying :py:func:`~pyglet.text.layout.TextLayout` and
:py:class:`~pyglet.text.document.AbstractDocument` classes provide a
"model/view" interface to all of pyglet's text features.

    .. image:: img/text_classes.png

Documents
^^^^^^^^^

A `document` is the "model" part of the architecture, and describes the
content and style of the text to be displayed.  There are two concrete
document classes: :py:class:`~pyglet.text.document.UnformattedDocument`
and :py:class:`~pyglet.text.document.FormattedDocument`.
:py:class:`~pyglet.text.document.UnformattedDocument` models a document
containing text in just one style, whereas
:py:class:`~pyglet.text.document.FormattedDocument` allows the style to
change within the text.

An empty, unstyled document can be created by constructing either of the
classes directly.  Usually you will want to initialise the document with some
text, however. The :py:func:`~pyglet.text.decode_text`,
:py:func:`~pyglet.text.decode_attributed` and
:py:func:`~pyglet.text.decode_html` functions return a document given a
source string. For :py:func:`~pyglet.text.decode_text`,
this is simply a plain text string, and the return value is an
:py:class:`~pyglet.text.document.UnformattedDocument`::

    document = pyglet.text.decode_text('Hello, world.')

:py:func:`~pyglet.text.decode_attributed` and
:py:func:`~pyglet.text.decode_html` are described in detail in the next
section.

The text of a document can be modified directly as a property on the object::

    document.text = 'Goodbye, cruel world.'

However, if small changes are being made to the document it can be more
efficient (when coupled with an appropriate layout; see below) to use the
:py:func:`~pyglet.text.document.AbstractDocument.delete_text` and
:py:func:`~pyglet.text.document.AbstractDocument.insert_text` methods instead.

Layouts
^^^^^^^

The actual layout and rendering of a document is performed by the
:py:func:`~pyglet.text.layout.TextLayout` classes.
This split exists to reduce the complexity of the code, and to allow
a single document to be displayed in multiple layouts simultaneously (in other
words, many layouts can display one document).

Each of the :py:func:`~pyglet.text.layout.TextLayout` classes perform layout
in the same way, but represent a trade-off in efficiency of update against
efficiency of drawing and memory usage.

The base :py:func:`~pyglet.text.layout.TextLayout` class uses little memory,
and shares its graphics group with other
:py:func:`~pyglet.text.layout.TextLayout` instances in the same batch
(see :ref:`guide_batched-rendering`). When the text or style of the document
is modified, or the layout constraints change (for example, the width of the
layout changes), the entire text layout is recalculated.
This is a potentially expensive operation, especially for long documents.
This makes :py:func:`~pyglet.text.layout.TextLayout` suitable
for relatively short or unchanging documents.

:py:class:`~pyglet.text.layout.ScrollableTextLayout` is a small extension to
:py:func:`~pyglet.text.layout.TextLayout` that culls the
text outside of a specified view rectangle, and allows text to be scrolled within that
rectangle without performing the layout calculation again.  Because of this
clipping rectangle the graphics group cannot be shared with other text
layouts, so for ideal performance
:py:class:`~pyglet.text.layout.ScrollableTextLayout` should be used only
if scrolling is required.

:py:class:`~pyglet.text.layout.IncrementalTextLayout` uses a more sophisticated
layout algorithm that performs less work for small changes to documents.
For example, if a document is being edited by the user, only the immediately
affected lines of text are recalculated when a character is typed or deleted.
:py:class:`~pyglet.text.layout.IncrementalTextLayout`
also performs view rectangle culling, reducing the amount of layout and
rendering required when the document is larger than the view.
:py:class:`~pyglet.text.layout.IncrementalTextLayout` should be used for
large documents or documents that change rapidly.

All the layout classes can be constructed given a document and display
dimensions::

    layout = pyglet.text.layout.TextLayout(document, width, height)

Additional arguments to the constructor allow the specification of a graphics
batch and group (recommended if many layouts are to be rendered), and the
optional `multiline` and `wrap_lines` flags.

`multiline`
  To honor newlines in the document you will need to set this to ``True``. If
  you do not then newlines will be rendered as plain spaces.

`wrap_lines`
  If you expect that your document lines will be wider than the display width
  then pyglet can automatically wrap them to fit the width by setting this
  option to ``True``. Note that wrapping only works if there are spaces in the
  text, so it may not be suitable for languages without spaces.

Like labels, layouts are positioned through their `x`, `y`,
`anchor_x` and `anchor_y` properties.
The `anchor` properties accept a string such as ``"bottom"`` or ``"center"`` instead of a
numeric displacement.

Rendering layouts to textures
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:py:meth:`~pyglet.text.layout.TextLayout.get_as_texture` draws a layout into a
new caller-owned GPU texture. Texture allocation and rendering can be slow when
performed in bulk or every frame. For an occasional conversion, no additional
setup is needed::

    texture = layout.get_as_texture()

When converting many layouts, pass a
:py:class:`~pyglet.graphics.framebuffer.TextureRenderTarget` to reuse its
framebuffer and camera. This reduces setup overhead, but each result still
requires a new texture allocation and GPU render::

    target = pyglet.graphics.TextureRenderTarget()
    textures = [layout.get_as_texture(target) for layout in layouts]
    target.delete()

Deleting the target does not delete the returned textures. Delete each texture
when it is no longer needed. See :ref:`guide_drawing-into-a-texture` for render
target lifecycle and ownership details.

.. _guide_formatted-text:

Formatted text
--------------

The :py:class:`~pyglet.text.document.FormattedDocument` class maintains
style information for individual characters in the text, rather than a
single style for the whole document.
Styles can be accessed and modified by name, for example::

    # Get the font name used at character index 0
    font_name = document.get_style('font_name', 0)

    # Set the font name and size for the first 5 characters
    document.set_style(0, 5, dict(font_name='Arial', font_size=12))

Internally, character styles are run-length encoded over the document text; so
longer documents with few style changes do not use excessive memory.

From the document's point of view, there are no predefined style names: it
simply maps names and character ranges to arbitrary Python values.
It is the :py:class:`~pyglet.text.layout.TextLayout` classes that interpret
this style information; for example, by selecting a different font based on the
``font_name`` style.  Unrecognised style names are ignored by the layout
-- you can use this knowledge to store additional data alongside the
document text (for example, a URL behind a hyperlink).

Character styles
^^^^^^^^^^^^^^^^

The following character styles are recognised by all
:py:func:`~pyglet.text.layout.TextLayout` classes.

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

Paragraph styles
^^^^^^^^^^^^^^^^

Although :py:class:`~pyglet.text.document.FormattedDocument` does not
distinguish between character- and paragraph-level styles,
:py:func:`~pyglet.text.layout.TextLayout` interprets the following styles
only at the paragraph level. You should take care to set these styles for
complete paragraphs only, for example, by using
:py:meth:`~pyglet.text.document.AbstractDocument.set_paragraph_style`.

These styles are ignored for layouts without the ``multiline`` flag set.

``align``
    ``"left"`` (default), ``"center"`` or ``"right"``.
``indent``
    Additional horizontal space to insert before the first glyph of the
    first line of a paragraph, as a distance.
``leading``
    Additional space to insert between consecutive lines within a paragraph,
    as a distance.  Defaults to 0.
    Unicode text of ``\u2028`` is treated as the start of a new paragraph.
``line_spacing``
    Distance between consecutive baselines in a paragraph, as a distance.
    Defaults to ``None``, which automatically calculates the tightest line
    spacing for each line based on the maximum font ascent and descent.
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
    Boolean.  If True (the default), text wraps within the width of the layout.

For the purposes of these attributes, paragraphs are split by the newline
character (U+0010) or the paragraph break character (U+2029).  Line breaks
within a paragraph can be forced with character U+2028.

Tabs
....

A tab character in pyglet text is interpreted as 'move to the next tab stop'.
Tab stops are specified in pixels, not in some font unit; by default
there is a tab stop every 50 pixels and because of that a tab can look too
small for big fonts or too big for small fonts.

Additionally, when rendering text with tabs using a `monospace` font,
character boxes may not align vertically.

To avoid these visualization issues the simpler solution is to convert
the tabs to spaces before sending a string to a pyglet text-related class.

Attributed text
^^^^^^^^^^^^^^^

pyglet provides two formats for decoding formatted documents from plain text.
These are useful for loading pre-prepared documents such as help screens.  At
this time there is no facility for saving (encoding) formatted documents.

The *attributed text* format is an encoding specific to pyglet that can
exactly describe any :py:class:`~pyglet.text.document.FormattedDocument`.
You must use this encoding to access all of the features of pyglet text layout.
For a more accessible, yet less featureful encoding,
see the `HTML` encoding, described below.

The following example shows a simple attributed text encoded document:

.. rst-class:: plain

  ::

    Chapter 1

    My father's family name being Pirrip, and my Christian name Philip,
    my infant tongue could make of both names nothing longer or more
    explicit than Pip.  So, I called myself Pip, and came to be called
    Pip.

    I give Pirrip as my father's family name, on the authority of his
    tombstone and my sister - Mrs. Joe Gargery, who married the
    blacksmith.  As I never saw my father or my mother, and never saw
    any likeness of either of them (for their days were long before the
    days of photographs), my first fancies regarding what they were
    like, were unreasonably derived from their tombstones.

Newlines are ignored, unless two are made in succession, indicating a
paragraph break.  Line breaks can be forced with the ``\\`` sequence:

.. rst-class:: plain

  ::

    This is the way the world ends \\
    This is the way the world ends \\
    This is the way the world ends \\
    Not with a bang but a whimper.

Line breaks are also forced when the text is indented with one or more spaces
or tabs, which is useful for typesetting code:

.. rst-class:: plain

  ::

    The following paragraph has hard line breaks for every line of code:

        import pyglet

        window = pyglet.window.Window()
        pyglet.app.run()

Text can be styled using a attribute tag:

.. rst-class:: plain

  ::

    This sentence makes a {bold True}bold{bold False} statement.

The attribute tag consists of the attribute name (in this example, ``bold``)
followed by a Python bool, int, float, string, tuple or list.

Unlike most structured documents such as HTML, attributed text has no concept
of the "end" of a style; styles merely change within the document.
This corresponds exactly to the representation used by
:py:class:`~pyglet.text.document.FormattedDocument` internally.

Some more examples follow:

.. rst-class:: plain

  ::

    {font_name 'Times New Roman'}{font_size 28}Hello{font_size 12},
    {color (255, 0, 0, 255)}world{color (0, 0, 0, 255)}!

(This example uses 28pt Times New Roman for the word "Hello", and 12pt
red text for the word "world").

Paragraph styles can be set by prefixing the style name with a period (.).
This ensures the style range exactly encompasses the paragraph:

.. rst-class:: plain

  ::

    {.margin_left "12px"}This is a block quote, as the margin is inset.

    {.margin_left "24px"}This paragraph is inset yet again.

Attributed text can be loaded as a Unicode string.  In addition, any character
can be inserted given its Unicode code point in numeric form, either in
decimal:

.. rst-class:: plain

  ::

    This text is Copyright {#169}.

or hexadecimal:

.. rst-class:: plain

  ::

    This text is Copyright {#xa9}.

The characters ``{`` and ``}`` can be escaped by duplicating them:

.. rst-class:: plain

  ::

    Attributed text uses many "{{" and "}}" characters.

Use the ``decode_attributed`` function to decode attributed text into a
:py:class:`~pyglet.text.document.FormattedDocument`::

    document = pyglet.text.decode_attributed('Hello, {bold True}world')

HTML
^^^^

While attributed text gives access to all of the features of
:py:class:`~pyglet.text.document.FormattedDocument` and
:py:func:`~pyglet.text.layout.TextLayout`, it is quite verbose and difficult
produce text in.  For convenience, pyglet provides an HTML 4.01 decoder that
can translate a small, commonly used subset of HTML into a
:py:class:`~pyglet.text.document.FormattedDocument`.

Note that the decoder does not preserve the structure of the HTML document --
all notion of element hierarchy is lost in the translation, and only the
visible style changes are preserved.

The following example uses :py:func:`~pyglet.text.decode_html` to create a
:py:class:`~pyglet.text.document.FormattedDocument` from a string of HTML::

    document = pyglet.text.decode_html('Hello, <b>world</b>')

The following elements are supported:

.. rst-class:: plain

  ::

    B BLOCKQUOTE BR CENTER CODE DD DIR DL EM FONT H1 H2 H3 H4 H5 H6 I IMG KBD
    LI MENU OL P PRE Q SAMP STRONG SUB SUP TT U UL VAR

The ``style`` attribute is not supported, so font sizes must be given as HTML
logical sizes in the range 1 to 7, rather than as point sizes.  The
corresponding font sizes, and some other stylesheet parameters, can be
modified by subclassing `HTMLDecoder`.

Custom elements
---------------

Graphics and other visual elements can be inserted inline into a document
using :py:meth:`~pyglet.text.document.AbstractDocument.insert_element`.
For example, inline elements are used to render HTML images included with
the ``IMG`` tag.  There is currently no support for floating or
absolutely-positioned elements.

Elements must subclass :py:class:`~pyglet.text.document.InlineElement`
and override the `place` and `remove` methods.  These methods are called by
:py:func:`~pyglet.text.layout.TextLayout` when the element becomes
or ceases to be visible.  For :py:func:`~pyglet.text.layout.TextLayout`
and :py:class:`~pyglet.text.layout.ScrollableTextLayout`,
this is when the element is added or removed from the document;
but for :py:class:`~pyglet.text.layout.IncrementalTextLayout` the methods
are also called as the element scrolls in and out of the viewport.

The constructor of :py:class:`~pyglet.text.document.InlineElement`
gives the width and height (separated into the ascent above the baseline,
and descent below the baseline) of the element.

Typically an :py:class:`~pyglet.text.document.InlineElement` subclass will
add graphics primitives to the layout's graphics batch; though applications
may choose to simply record the position of the element and render it
separately.

The position of the element in the document text is marked with a NUL
character (U+0000) placeholder.  This has the effect that inserting an element
into a document increases the length of the document text by one.  Elements
can also be styled as if they were ordinary character text, though the layout
ignores any such style attributes.

User-editable text
------------------

While pyglet does not come with any complete GUI widgets for applications to
use, it does implement many of the features required to implement interactive
text editing.  These can be used as a basis for a more complete GUI system, or
to present a simple text entry field, as demonstrated in the
``examples/text_input.py`` example.

:py:class:`~pyglet.text.layout.IncrementalTextLayout` should always be used for
text that can be edited by the user.
This class maintains information about the placement of glyphs on screen,
and so can map window coordinates to a document position and vice-versa.
These methods are
:py:meth:`~pyglet.text.layout.IncrementalTextLayout.get_position_from_point`,
:py:meth:`~pyglet.text.layout.IncrementalTextLayout.get_point_from_position`,
:py:meth:`~pyglet.text.layout.IncrementalTextLayout.get_line_from_point`,
:py:meth:`~pyglet.text.layout.IncrementalTextLayout.get_point_from_line`,
:py:meth:`~pyglet.text.layout.IncrementalTextLayout.get_line_from_position`,
:py:meth:`~pyglet.text.layout.IncrementalTextLayout.get_position_from_line`,
:py:meth:`~pyglet.text.layout.IncrementalTextLayout.get_position_on_line`
and
:py:meth:`~pyglet.text.layout.IncrementalTextLayout.get_line_count`.

The viewable rectangle of the document can be adjusted using a document
position instead of a scrollbar using the
:py:meth:`~pyglet.text.layout.IncrementalTextLayout.ensure_line_visible` and
:py:meth:`~pyglet.text.layout.IncrementalTextLayout.ensure_x_visible` methods.

:py:class:`~pyglet.text.layout.IncrementalTextLayout` can display a current
text selection by temporarily overriding the foreground and background colour
of the selected text. The
:py:attr:`~pyglet.text.layout.IncrementalTextLayout.selection_start` and
:py:attr:`~pyglet.text.layout.IncrementalTextLayout.selection_end` properties
give the range of the selection, and
:py:attr:`~pyglet.text.layout.IncrementalTextLayout.selection_color` and
:py:attr:`~pyglet.text.layout.IncrementalTextLayout.selection_background_color`
the colors to use (defaulting to white on blue).

The :py:class:`~pyglet.text.caret.Caret` class implements an insertion caret
(cursor) for :py:class:`~pyglet.text.layout.IncrementalTextLayout`.
This includes displaying the blinking caret at the correct location,
and handling keyboard, text and mouse events.
The behaviour in response to the events is similar to native text controls on
Windows, macOS, and Linux. Using :py:class:`~pyglet.text.caret.Caret`
frees you from using the :py:class:`~pyglet.text.layout.IncrementalTextLayout`
methods described above directly.

The following example creates a document, a layout and a caret and attaches
the caret to the window to listen for events::

    import pyglet

    window = pyglet.window.Window()
    document = pyglet.text.document.FormattedDocument()
    layout = pyglet.text.layout.IncrementalTextLayout(document, width, height)
    caret = pyglet.text.caret.Caret(layout)
    window.push_handlers(caret)

When the layout is drawn, the caret will also be drawn, so this example is
nearly complete enough to display the user input.  However, it is suitable for
use when only one editable text layout is to be in the window.  If multiple
text widgets are to be shown, some mechanism is needed to dispatch events to
the widget that has keyboard focus.  An example of how to do this is given in
the `examples/text_input.py` example program.

Choosing fonts
--------------

Labels and layouts load fonts automatically from their ``font_name``,
``font_size``, ``weight``, ``style``, and ``stretch`` properties. See
:doc:`fonts` for family and face names, fallback families, custom font files,
font groups, sizes, and metrics.

Font shaping
------------

Shaping controls how a selected font converts text into glyphs. See the
:ref:`font shaping section <guide_font_shaping>` in :doc:`fonts` for backend
selection, HarfBuzz, and when to disable shaping for an individual label or
layout.
