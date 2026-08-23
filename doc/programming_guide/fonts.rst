.. _guide_fonts:

Fonts
=====

pyglet can render system-installed fonts and font files distributed with an
application. This chapter explains how font names and faces are selected. To
display the resulting text with labels, documents, and layouts, see
:doc:`text`.

Families and faces
------------------

A **font family** is a group of related designs that share one family name.
Each weight, slant, or width within that family is a **font face**. For
example, ``Arial`` is a family; its regular, bold, italic, and narrow designs
are faces within that family.

For a portable cross-platform selection, pass the family name to :py:func:`pyglet.font.load`
and describe the desired face separately with ``weight``, ``style``, and ``stretch``::

    from pyglet import font
    from pyglet.enums import Stretch, Style, Weight

    regular = font.load("Arial", 16)
    bold = font.load("Arial", 16, weight=Weight.BOLD)
    italic = font.load("Arial", 16, style=Style.ITALIC)
    narrow = font.load("Arial", 16, stretch=Stretch.CONDENSED)

The enum members are strings, so their string values can also be used::

    bold_italic = font.load(
        "Arial",
        16,
        weight="bold",
        style="italic",
    )

pyglet asks the platform renderer for the closest available face. A family
does not necessarily contain every weight, style, or stretch, so the result
may be an approximation.

Alternative font names
^^^^^^^^^^^^^^^^^^^^^^

Font files can contain several kinds of names. The family name groups related
faces, while the OpenType Full Name usually identifies one specific face,
such as **Action Man Bold Italic**. Fonts may also contain legacy, platform-specific, or
localized names that combine family and face information in different ways. These
names are not always consistent: they may use different formatting, spelling, or even
entirely different names for the same face. Operating systems may also choose or
interpret these fields differently, so the name reported for a font can vary
between platforms.

Set :attr:`pyglet.Options.font_name_compatibility` before resolving fonts when
an application needs pyglet to perform additional lookup for Full Names and
platform-specific aliases::

    import pyglet

    pyglet.options.font_name_compatibility = True
    narrow = pyglet.font.load("Arial Narrow", 16)

A native font API may recognize them without help from pyglet. Enabling it only adds
pyglet's compatibility lookup, which can improve cross-platform matching at the cost of
additional font-resolution time.

On Windows, DirectWrite does not index some names historically exposed by the
older Windows font renderer like GDI. Finding such a name requires inspecting installed
families and faces. The first lookup can therefore be noticeably slower on a
system with many fonts; successful results are cached.

If a name does not resolve as expected, see :ref:`Troubleshooting font loading
<troubleshooting-font-loading>` for ways to identify the names pyglet found.

Because a Full Name identifies a concrete face, its embedded traits take
precedence over separately requested ``weight``, ``style``, or ``stretch``.
Family name plus explicit traits remains the recommended portable form.

Font sizes and metrics
----------------------

Font sizes are specified in points. pyglet uses the PostScript definition of
one point as 1/72 inch and assumes 96 DPI unless another value is supplied::

    font_144_dpi = pyglet.font.load("Arial", 16, dpi=144)

The loaded font exposes pixel metrics through ``ascent`` and ``descent``.
Descent is normally negative because it extends below the baseline. A basic
line advance can be calculated as::

    line_advance = loaded_font.ascent - loaded_font.descent + leading

.. figure:: img/font_metrics.png

   Font metrics relative to the baseline.

Labels and layouts accept a ``dpi`` argument as well. Keep the DPI consistent
when comparing or combining their measurements.

Loading system fonts
--------------------

The text layout classes load fonts when needed, but applications can also load
one explicitly::

    times = pyglet.font.load("Times New Roman", 16)

A sequence provides fallbacks in preference order. The first available family
is selected::

    sans_serif = pyglet.font.load(
        ("Inter", "Helvetica Neue", "Segoe UI", "Arial"),
        16,
    )

Use :py:func:`pyglet.font.have_font` to check one name::

    if pyglet.font.have_font("Inter"):
        print("Inter is available")

Passing ``None`` selects pyglet's platform default::

    default_font = pyglet.font.load(None, 16)

Applications should not assume that a particular commercial font is installed
on every operating system. Use a fallback sequence, bundle a suitably licensed
font, or use the platform default.

Loading custom fonts
--------------------

Applications can bundle fonts that are not normally installed on the target
system. Confirm that the font's license permits redistribution.

Add every required face, then select it by family and traits::

    import pyglet
    from pyglet.enums import Weight

    pyglet.font.add_file("action_man.ttf")
    pyglet.font.add_file("action_man_bold.ttf")

    regular = pyglet.font.load("Action Man", 16)
    bold = pyglet.font.load("Action Man", 16, weight=Weight.BOLD)

The filename is not the font family name. The family is read from metadata
inside the file, and several differently named files can contribute faces to
the same family. :py:func:`pyglet.font.add_file` also accepts a binary file-like
object or bytes. :py:func:`pyglet.font.add_directory` loads supported files
from a directory.

Fonts can also be loaded through :ref:`guide_resources`. On Pyodide, custom
font registration is asynchronous; see the Fonts section in :doc:`pyodide`.

Supported formats
^^^^^^^^^^^^^^^^^

Font-format support is provided primarily by the operating system's font
stack, so it varies by platform and OS version. TrueType (``.ttf``) and
OpenType (``.otf``) are the most portable choices. Platform-specific bitmap,
collection, and legacy formats may work only on the backend that supports
them. Test every bundled font on each target platform, since malformed or
incomplete metadata can also change family and face matching.

.. _troubleshooting-font-loading:

Troubleshooting font loading
----------------------------

A font's filename, family name, and Full Name can all be different. After
adding custom font files, query the family names that pyglet actually
discovered instead of guessing from the filenames::

    import pyglet

    pyglet.font.add_file("fonts/example-sans-bold.otf")
    print(pyglet.font.get_custom_font_names())

The result contains family names, such as ``("Example Sans",)``, which can be
passed to :py:func:`pyglet.font.load`. It does not list every face filename or
Full Name. On Pyodide, check it after the ``on_font_loaded`` event because
browser font registration is asynchronous.

Check system-font availability before constructing application-specific
fallback behavior::

    if not pyglet.font.have_font("Example Sans"):
        print("Example Sans is unavailable; pyglet will use a fallback")

If no requested family is available, :py:func:`pyglet.font.load` selects the
platform default.

For detailed resolution messages, enable ``debug_font`` before importing the
font module::

    import pyglet

    pyglet.options.debug_font = True
    from pyglet import font

    font.add_file("fonts/example-sans-bold.otf")
    print(font.get_custom_font_names())
    selected = font.load("Example Sans", 16)
    print(selected.name)

The debug output reports missing requested families, compatibility-name
searches, and fallback to the platform default. Also inspect ``selected.name``
to see the family ultimately returned by the renderer.


Font groups
-----------

Automatic fallback
^^^^^^^^^^^^^^^^^^

:py:class:`~pyglet.font.group.FontGroup` gives an ordered set of families one
logical name. For each character, pyglet selects the first family containing a
glyph for it. This allows an application supply font fallbacks if one font
does not contain all of the characters needed.::

    import pyglet

    ui_font = pyglet.font.FontGroup("ui-font")
    ui_font.add("Noto Sans")
    ui_font.add("Noto Sans CJK JP")
    ui_font.add("Noto Color Emoji")
    pyglet.font.add_group(ui_font)

    label = pyglet.text.Label(
        "Hello こんにちは 😀",
        font_name="ui-font",
        font_size=18,
    )

Range-based fallback
^^^^^^^^^^^^^^^^^^^^

If an application needs fixed, predictable routing instead, use
:py:class:`~pyglet.font.group.FontRangeGroup`. It assigns families to explicit
Unicode ranges, and uses the first matching range::

    script_font = pyglet.font.FontRangeGroup("script-font")
    script_font.add("Noto Sans", 0x0000, 0x024F)
    script_font.add("Noto Sans CJK JP", 0x3040, 0x30FF)
    script_font.add("Noto Color Emoji", 0x1F300, 0x1FAFF)
    pyglet.font.add_group(script_font)

    label = pyglet.text.Label(
        "Hello こんにちは 😀",
        font_name="script-font",
        font_size=18,
    )

Use ``Font.has_character`` to check whether the selected font face contains
one Unicode character. It does not include implicit system font fallback. This
is useful when diagnosing missing bundled glyphs::

    if not ui_font.get_font(16).has_character("😀"):
        print("The configured font group has no emoji glyph")


Rendering and graphics contexts
-------------------------------

pyglet rasterizes glyphs as needed and stores them in texture atlases. Font
objects are cached per graphics-context object space. Applications using
contexts that do not share object space must load the font in each object
space, and must keep the appropriate context current when new glyphs may be
uploaded.

Normal label and layout drawing configures the required rendering state. Code
that renders font glyph textures directly is responsible for compatible
texture and blending state; most applications do not need to manage these
details.

Preloading glyphs
-----------------

Font glyph bitmaps are normally rasterized and added to a texture atlas when
text first needs them. That first use can cause a small, noticeable pause in
latency-sensitive applications. Call ``Font.preload_glyphs`` after loading a
font::

    ui_font = pyglet.font.load("Action Man", 16)
    ui_font.preload_glyphs()

With no argument, this preloads all 95 printable ASCII characters: a space,
uppercase and lowercase letters, digits, and keyboard punctuation such as
``!@#$%^``. Pass a string to preload the characters that matter to an
application instead, or to include non-ASCII text::

    ui_font.preload_glyphs("Loading... 0123456789 \N{HORIZONTAL ELLIPSIS}")

This only preloads bitmap glyphs for the particular loaded font face and size.
Load and prewarm each size, weight, style, or stretch that an application uses.

.. _guide_font_shaping:

Font shaping
------------

Font shaping applies kerning, ligatures, substitutions, and complex-script
glyph placement. The ``pyglet.options.text_shaping`` option selects the
application-wide shaping backend and defaults to ``"platform"``. Platform
shaping is available through DirectWrite on Windows and CoreText on macOS.
Linux does not provide a platform shaper, so the default platform mode uses
unshaped glyph metrics there.

Shaping is enabled by default on ``Label``, ``HTMLLabel``, ``DocumentLabel``,
and text layouts. A frequently updated label that does not need these
typographic features can disable it. Bypassing shaping reduces the work needed
to create and regenerate the label, which can help for text such as FPS
counters, timers, scores, and damage numbers::

    fps_label = pyglet.text.Label("FPS: 0", shaping=False)

For longer or typographically complex text, shaping produces more accurate
glyph selection and placement. Rich text does not require shaping merely
because it uses HTML, but an ``HTMLLabel`` containing paragraphs, mixed styles,
ligatures, or complex scripts will generally benefit from it::

    paragraph = pyglet.text.HTMLLabel(
        "<p>Typography-aware paragraph text.</p>",
        width=400,
        multiline=True,
        shaping=True,
    )

HarfBuzz
^^^^^^^^

Some platforms, including Linux, do not provide native text shaping. For a
cross-platform shaping solution, pyglet can use HarfBuzz. HarfBuzz is an
explicit opt-in rather than being selected automatically when installed. This
keeps existing text metrics stable and avoids making an optional native
dependency affect an application unexpectedly. To enable it, set
``pyglet.options.text_shaping`` to ``"harfbuzz"`` before loading fonts or
creating text layouts::

    import pyglet
    pyglet.options.text_shaping = "harfbuzz"

If HarfBuzz is not available, pyglet falls back to platform behavior. On a
platform without a native shaper, that means unshaped glyph metrics.

See the `HarfBuzz installation documentation
<https://harfbuzz.github.io/install-harfbuzz.html>`_ for platform-specific
instructions. pyglet uses the HarfBuzz shared library; command-line programs
such as ``hb-shape`` are not required.

.. note:: On Windows, ``libharfbuzz-0.dll`` depends on ``libglib-*.dll`` and
   ``libintl-*.dll``.
