"""Text formatting, layout and display.

This module provides classes for loading styled documents from text files,
HTML files and a pyglet-specific markup format.  Documents can be styled with
multiple fonts, colours, styles, text sizes, margins, paragraph alignments,
and so on.

Using the layout classes, documents can be laid out on a single line or
word-wrapped to fit a rectangle.  A layout can then be efficiently drawn in
a window or updated incrementally (for example, to support interactive text
editing).

The label classes provide a simple interface for the common case where an
application simply needs to display some text in a window.

A plain text label can be created with::

    label = pyglet.text.Label('Hello, world',
                              font_name='Times New Roman',
                              font_size=36,
                              x=10, y=10)

Alternatively, a styled text label using HTML can be created with::

    label = pyglet.text.HTMLLabel('<b>Hello</b>, <i>world</i>',
                                  x=10, y=10)

Either label can then be drawn at any time with::

    label.draw()

For details on the subset of HTML supported, see `pyglet.text.formats.html`.

Refer to the Programming Guide for advanced usage of the document and layout
classes, including interactive editing, embedding objects within documents and
creating scrollable layouts.
"""
from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from os.path import dirname as _dirname
from os.path import splitext as _splitext
from typing import TYPE_CHECKING, Any, BinaryIO, Literal

import pyglet

from pyglet.text import caret, document, layout  # noqa: F401


if TYPE_CHECKING:
    from pyglet.customtypes import AnchorX, AnchorY, HorizontalAlign
    from pyglet.graphics import Batch, Group
    from pyglet.graphics.shader import ShaderProgram
    from pyglet.resource import Location
    from pyglet.text.document import AbstractDocument, FormattedDocument, UnformattedDocument


class DocumentDecodeException(Exception):  # noqa: N818
    """An error occurred decoding document text."""


class DocumentDecoder:
    """Abstract document decoder."""

    @abstractmethod
    def decode(self, text: str, location: Location | None = None) -> AbstractDocument:
        """Decode document text.

        Args:
            text:
                Text to decode
            location:
                Location to use as base path for additional resources referenced within the document (for example,
                HTML images).
        """


SupportedMimeTypes = Literal["text/plain", "text/html", "text/vnd.pyglet-attributed"]


class Weight(str, Enum):
    """An :py:class:`~enum.Enum` of known cross-platform font weight strings.

    Each value is both an :py:class:`~enum.Enum` and a :py:class:`str`.
    This is not a built-in Python :py:class:`~enum.StrEnum` to ensure
    compatibility with Python < 3.11.

    .. important:: Fonts will use the closest match if they lack a weight!

    The values of this enum imitate the string names for font weights
    as used in CSS and the OpenType specification. Numerical font weights
    are not supported because:

    * Integer font weight support and behavior varies by back-end
    * Some font renderers do not support or round :py:class:`float` values
    * Some font renderers lack support for variable-width fonts

    Additional weight strings may be supported by certain font-rendering
    back-ends. To learn more, please see your platform's API documentation
    and the following:

    #. `The MDN article on CSS font weights <https://developer.mozilla.org/en-US/docs/Web/CSS/font-weight>`_
    #. `The OpenType specification <https://learn.microsoft.com/en-us/typography/opentype/spec/os2#usweightclass>`_

    """

    THIN = 'thin'
    EXTRALIGHT = 'extralight'
    LIGHT = 'light'
    NORMAL = 'normal'
    """The default weight for a font."""
    MEDIUM = 'medium'
    SEMIBOLD = 'semibold'
    BOLD = 'bold'
    """The default **bold** style for a font."""
    EXTRABOLD = 'extrabold'
    ULTRABOLD = 'ultrabold'

    def __str__(self) -> str:
        return self.value


def get_decoder(filename: str | None, mimetype: SupportedMimeTypes | None = None) -> DocumentDecoder:
    """Get a document decoder for the given filename and MIME type.

    If ``mimetype`` is omitted it is guessed from the filename extension.

    The following MIME types are supported:

    ``text/plain``
        Plain text
    ``text/html``
        HTML 4 Transitional
    ``text/vnd.pyglet-attributed``
        Attributed text; see `pyglet.text.formats.attributed`

    Args:
        filename:
            Filename to guess the MIME type from.  If a MIME type is given, the filename is ignored.
        mimetype:
            MIME type to lookup, or ``None`` to guess the type from the filename.

    Raises:
        DocumentDecodeException: If MIME type is not from the supported types.
    """
    if mimetype is None:
        _, ext = _splitext(filename)
        if ext.lower() in (".htm", ".html", ".xhtml"):
            mimetype = "text/html"
        else:
            mimetype = "text/plain"

    if mimetype == "text/plain":
        from pyglet.text.formats import plaintext
        return plaintext.PlainTextDecoder()
    if mimetype == "text/html":
        from pyglet.text.formats import html
        return html.HTMLDecoder()
    if mimetype == "text/vnd.pyglet-attributed":
        from pyglet.text.formats import attributed
        return attributed.AttributedTextDecoder()

    msg = f'Unknown format "{mimetype}"'
    raise DocumentDecodeException(msg)


def load(filename: str,
         file: BinaryIO | None = None,
         mimetype: SupportedMimeTypes | None = None) -> AbstractDocument:
    """Load a document from a file.

    Args:
        filename:
            Filename of document to load.
        file:
            File object containing encoded data.  If omitted, ``filename`` is
            loaded from disk.
        mimetype:
            MIME type of the document.  If omitted, the filename extension is
            used to guess a MIME type.  See `get_decoder` for a list of
            supported MIME types.
    """
    decoder = get_decoder(filename, mimetype)
    if not file:
        with open(filename) as f:
            file_contents = f.read()
    else:
        file_contents = file.read()
        file.close()

    if hasattr(file_contents, "decode"):
        file_contents = file_contents.decode()

    location = pyglet.resource.FileLocation(_dirname(filename))
    return decoder.decode(file_contents, location)


def decode_html(text: str, location: str | None = None) -> FormattedDocument:
    """Create a document directly from some HTML formatted text.

    Args:
        text:
            HTML data to decode.
        location:
            Location giving the base path for additional resources referenced from the document (e.g., images).
    """
    decoder = get_decoder(None, "text/html")
    return decoder.decode(text, location)


def decode_attributed(text: str) -> FormattedDocument:
    """Create a document directly from some attributed text.

    See `pyglet.text.formats.attributed` for a description of attributed text.
    """
    decoder = get_decoder(None, "text/vnd.pyglet-attributed")
    return decoder.decode(text)


def decode_text(text: str) -> UnformattedDocument:
    """Create a document directly from some plain text."""
    decoder = get_decoder(None, "text/plain")
    return decoder.decode(text)


class DocumentLabel(layout.TextLayout):
    """Base label class.

    A label is a layout that exposes convenience methods for manipulating the
    associated document.
    """

    def __init__(
            self, document: AbstractDocument,
            x: float = 0.0, y: float = 0.0, z: float = 0.0,
            width: int | None = None, height: int | None = None,
            anchor_x: AnchorX = "left", anchor_y: AnchorY = "baseline", rotation: float = 0.0,
            multiline: bool = False, dpi: int | None = None,
            batch: Batch | None = None, group: Group | None = None,
            program: ShaderProgram | None = None,
            init_document: bool = True,
    ) -> None:
        """Create a label for a given document.

        Args:
            document: Document to attach to the layout.
            x: X coordinate of the label.
            y: Y coordinate of the label.
            z: Z coordinate of the label.
            width: Width of the label in pixels, or ``None``
            height:  Height of the label in pixels, or ``None``
            anchor_x:
                Anchor point of the X coordinate: one of
                ``"left"``, `"center"`` or ``"right"``.
            anchor_y:
                Anchor point of the Y coordinate: one of
                ``"bottom"``, ``"baseline"``, ``"center"`` or ``"top"``.
            rotation:
                The amount to rotate the label in degrees. A
                positive amount will be a clockwise rotation, negative
                values will result in counter-clockwise rotation.
            multiline:
                If ``True``, the label will be word-wrapped and
                accept newline characters. You must also set the width
                of the label.
            dpi: Resolution of the fonts in this layout. Defaults to 96.
            batch: Optional graphics batch to add the label to.
            group: Optional graphics group to use.
            program: Optional graphics shader to use. Will affect all glyphs.
            init_document:
                If ``True``, the document will be initialized. If you
                are passing an already-initialized document, then you can
                avoid duplicating work by setting this to ``False``.
        """
        super().__init__(document, x, y, z, width, height, anchor_x, anchor_y, rotation,
                         multiline, dpi, batch, group, program, init_document=init_document)

    @property
    def text(self) -> str:
        """The text of the label."""
        return self.document.text

    @text.setter
    def text(self, text: str) -> None:
        self.document.text = text

    @property
    def color(self) -> tuple[int, int, int, int]:
        """Text color.

        Color is a 4-tuple of RGBA components, each in range [0, 255].
        """
        return self.document.get_style("color")

    @color.setter
    def color(self, color: tuple[int, int, int, int]) -> None:
        r, g, b, *a = color
        color = r, g, b, a[0] if a else 255
        self.document.set_style(0, len(self.document.text), {"color": color})

    @property
    def opacity(self) -> int:
        """Blend opacity.

        This property sets the alpha component of the colour of the label's
        vertices.  With the default blend mode, this allows the layout to be
        drawn with fractional opacity, blending with the background.

        An opacity of 255 (the default) has no effect.  An opacity of 128 will
        make the label appear semi-translucent.
        """
        return self.color[3]

    @opacity.setter
    def opacity(self, alpha: int) -> None:
        if alpha != self.color[3]:
            self.color = list(map(int, (*self.color[:3], alpha)))

    @property
    def font_name(self) -> str | list[str]:
        """Font family name.

        The font name, as passed to :py:func:`pyglet.font.load`.  A list of names can
        optionally be given: the first matching font will be used.
        """
        return self.document.get_style("font_name")

    @font_name.setter
    def font_name(self, font_name: str | list[str]) -> None:
        self.document.set_style(0, len(self.document.text), {"font_name": font_name})

    @property
    def font_size(self) -> float:
        """Font size, in points."""
        return self.document.get_style("font_size")

    @font_size.setter
    def font_size(self, font_size: float) -> None:
        self.document.set_style(0, len(self.document.text), {"font_size": font_size})

    @property
    def weight(self) -> str:
        """The font weight (boldness or thickness), as a string.

        See the :py:class:`~Weight` enum for valid cross-platform
        string values.
        """
        return self.document.get_style("weight")

    @weight.setter
    def weight(self, weight: str) -> None:
        self.document.set_style(0, len(self.document.text), {"weight": str(weight)})

    @property
    def italic(self) -> bool | str:
        """Italic font style."""
        return self.document.get_style("italic")

    @italic.setter
    def italic(self, italic: bool | str) -> None:
        self.document.set_style(0, len(self.document.text), {"italic": italic})

    def get_style(self, name: str) -> Any:
        """Get a document style value by name.

        If the document has more than one value of the named style,
        `pyglet.text.document.STYLE_INDETERMINATE` is returned.

        Args:
            name:
                Style name to query.  See documentation from `pyglet.text.layout` for known style names.
        """
        return self.document.get_style_range(name, 0, len(self.document.text))

    def set_style(self, name: str, value: Any) -> None:
        """Set a document style value by name over the whole document.

        Args:
            name:
                Name of the style to set.  See documentation for
                `pyglet.text.layout` for known style names.
            value:
                Value of the style.
        """
        self.document.set_style(0, len(self.document.text), {name: value})

    def __del__(self) -> None:
        self.delete()


class Label(DocumentLabel):
    """Plain text label."""

    def __init__(
            self, text: str = "",
            x: float = 0.0, y: float = 0.0, z: float = 0.0,
            width: int | None = None, height: int | None = None,
            anchor_x: AnchorX = "left", anchor_y: AnchorY = "baseline", rotation: float = 0.0,
            multiline: bool = False, dpi: int | None = None,
            font_name: str | None = None, font_size: float | None = None,
            weight: str = "normal", italic: bool | str = False, stretch: bool | str = False,
            color: tuple[int, int, int, int] | tuple[int, int, int] = (255, 255, 255, 255),
            align: HorizontalAlign = "left",
            batch: Batch | None = None, group: Group | None = None,
            program: ShaderProgram | None = None,
    ) -> None:
        """Create a plain text label.

        Args:
            text:
                Text to display.
            x:
                X coordinate of the label.
            y:
                Y coordinate of the label.
            z:
                Z coordinate of the label.
            width:
                Width of the label in pixels, or None
            height:
                Height of the label in pixels, or None
            anchor_x:
                Anchor point of the X coordinate: one of ``"left"``,
                ``"center"`` or ``"right"``.
            anchor_y:
                Anchor point of the Y coordinate: one of ``"bottom"``,
                ``"baseline"``, ``"center"`` or ``"top"``.
            rotation:
                The amount to rotate the label in degrees. A positive amount
                will be a clockwise rotation, negative values will result in
                counter-clockwise rotation.
            multiline:
                If True, the label will be word-wrapped and accept newline
                characters.  You must also set the width of the label.
            dpi:
                Resolution of the fonts in this layout.  Defaults to 96.
            font_name:
                Font family name(s).  If more than one name is given, the
                first matching name is used.
            font_size:
                Font size, in points.
            weight:
                The 'weight' of the font (boldness). See the :py:class:`~Weight`
                enum for valid cross-platform weight names.
            italic:
                Italic font style.
            stretch:
                 Stretch font style.
            color:
                Font color as RGBA or RGB components, each within
                ``0 <= component <= 255``.
            align:
                Horizontal alignment of text on a line, only applies if
                a width is supplied. One of ``"left"``, ``"center"``
                or ``"right"``.
            batch:
                Optional graphics batch to add the label to.
            group:
                Optional graphics group to use.
            program:
                Optional graphics shader to use. Will affect all glyphs.
        """
        doc = decode_text(text)
        r, g, b, *a = color
        rgba = r, g, b, a[0] if a else 255

        super().__init__(doc, x, y, z, width, height, anchor_x, anchor_y, rotation,
                         multiline, dpi, batch, group, program, init_document=False)

        self.document.set_style(0, len(self.document.text), {
            "font_name": font_name,
            "font_size": font_size,
            "weight": weight,
            "italic": italic,
            "stretch": stretch,
            "color": rgba,
            "align": align,
        })


class HTMLLabel(DocumentLabel):
    """HTML formatted text label.

    A subset of HTML 4.01 is supported.  See `pyglet.text.formats.html` for
    details.
    """

    def __init__(self, text: str = "",
                 x: float = 0.0, y: float = 0.0, z: float = 0.0, width: int | None = None, height: int | None = None,
                 anchor_x: AnchorX = "left", anchor_y: AnchorY = "baseline", rotation: float = 0.0,
                 multiline: bool = False, dpi: float | None = None,
                 location: Location | None = None,
                 batch: Batch | None = None, group: Group | None = None,
                 program: ShaderProgram | None = None) -> None:
        """Create a label with an HTML string.

        Args:
            text:
                Text to display.
            x:
                X coordinate of the label.
            y:
                Y coordinate of the label.
            z:
                Z coordinate of the label.
            width:
                Width of the label in pixels, or None
            height:
                Height of the label in pixels, or None
            anchor_x:
                Anchor point of the X coordinate: one of ``"left"``,
                ``"center"`` or ``"right"``.
            anchor_y:
                Anchor point of the Y coordinate: one of ``"bottom"``,
                ``"baseline"``, ``"center"`` or ``"top"``.
            rotation:
                The amount to rotate the label in degrees. A positive amount
                will be a clockwise rotation, negative values will result in
                counter-clockwise rotation.
            multiline:
                If True, the label will be word-wrapped and accept newline
                characters.  You must also set the width of the label.
            dpi:
                Resolution of the fonts in this layout.  Defaults to 96.
            location:
                Location object for loading images referred to in the document.
                By default, the working directory is used.
            batch:
                Optional graphics batch to add the label to.
            group:
                Optional graphics group to use.
            program:
                Optional graphics shader to use. Will affect all glyphs.

        """
        self._text = text
        self._location = location
        doc = decode_html(text, location)
        super().__init__(doc, x, y, z, width, height, anchor_x, anchor_y, rotation,
                         multiline, dpi, batch, group, program, init_document=True)

    @property
    def text(self) -> str:
        """HTML formatted text of the label."""
        return self._text

    @text.setter
    def text(self, text: str) -> None:
        self._text = text
        self.document = decode_html(text, self._location)


__all__ = [
    "DocumentDecodeException",
    "DocumentDecoder",
    "SupportedMimeTypes",
    "get_decoder",
    "load",
    "decode_html",
    "decode_attributed",
    "decode_text",
    "DocumentLabel",
    "Label",
    "HTMLLabel",
    # imported from lower
    "document",
    "layout",
]
