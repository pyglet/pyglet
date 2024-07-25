"""Formatted and unformatted document interfaces used by text layout.

Abstract representation
=======================

Styled text in pyglet is represented by one of the :py:class:`~pyglet.text.document.AbstractDocument` classes,
which manage the state representation of text and style independently of how
it is loaded or rendered.

A document consists of the document text (a Unicode string) and a set of
named style ranges.  For example, consider the following (artificial)
example::

    0    5   10   15   20
    The cat sat on the mat.
    +++++++        +++++++    "bold"
                ++++++      "italic"

If this example were to be rendered, "The cat" and "the mat" would be in bold,
and "on the" in italics.  Note that the second "the" is both bold and italic.

The document styles recorded for this example would be ``"bold"`` over ranges
(0-7, 15-22) and ``"italic"`` over range (12-18).  Overlapping styles are
permitted; unlike HTML and other structured markup, the ranges need not be
nested.

The document has no knowledge of the semantics of ``"bold"`` or ``"italic"``,
it stores only the style names.  The pyglet layout classes give meaning to
these style names in the way they are rendered; but you are also free to
invent your own style names (which will be ignored by the layout classes).
This can be useful to tag areas of interest in a document, or maintain
references back to the source material.

As well as text, the document can contain arbitrary elements represented by
:py:class:`~pyglet.text.document.InlineElement`.  An inline element behaves
like a single character in the document, but can be rendered by the application.

Paragraph breaks
================

Paragraph breaks are marked with a "newline" character (U+0010).  The Unicode
paragraph break (U+2029) can also be used.

Line breaks (U+2028) can be used to force a line break within a paragraph.

See Unicode recommendation UTR #13 for more information:
https://www.unicode.org/standard/reports/tr13/tr13-5.html.

Document classes
================

Any class implementing :py:class:`~pyglet.text.document.AbstractDocument` provides an interface to a
document model as described above.  In theory a structured document such as
HTML or XML could export this model, though the classes provided by pyglet
implement only unstructured documents.

The :py:class:`~pyglet.text.document.UnformattedDocument` class assumes any styles set are set over the entire
document.  So, regardless of the range specified when setting a ``"bold"``
style attribute, for example, the entire document will receive that style.

The :py:class:`~pyglet.text.document.FormattedDocument` class implements the document model directly, using
the `RunList` class to represent style runs efficiently.

Style attributes
================

The following character style attribute names are recognised by pyglet:

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
    Additional space to insert between glyphs, in points.  Defaults to 0.
``baseline``
    Offset of glyph baseline from line baseline, in points.  Positive values
    give a superscript, negative values give a subscript.  Defaults to 0.
``color``
    4-tuple of ints in range (0, 255) giving RGBA text color
``background_color``
    4-tuple of ints in range (0, 255) giving RGBA text background color; or
    ``None`` for no background fill.

The following paragraph style attribute names are recognised by pyglet.  Note
that paragraph styles are handled no differently from character styles by the
document: it is the application's responsibility to set the style over an
entire paragraph, otherwise results are undefined.

``align``
    ``left`` (default), ``center`` or ``right``.
``indent``
    Additional horizontal space to insert before the first
``leading``
    Additional space to insert between consecutive lines within a paragraph,
    in points.  Defaults to 0.
``line_spacing``
    Distance between consecutive baselines in a paragraph, in points.
    Defaults to ``None``, which automatically calculates the tightest line
    spacing for each line based on the font ascent and descent.
``margin_left``
    Left paragraph margin, in pixels.
``margin_right``
    Right paragraph margin, in pixels.
``margin_top``
    Margin above paragraph, in pixels.
``margin_bottom``
    Margin below paragraph, in pixels.  Adjacent margins do not collapse.
``tab_stops``
    List of horizontal tab stops, in pixels, measured from the left edge of
    the text layout.  Defaults to the empty list.  When the tab stops
    are exhausted, they implicitly continue at 50 pixel intervals.
``wrap``
    Boolean.  If True (the default), text wraps within the width of the layout.

Other attributes can be used to store additional style information within the
document; it will be ignored by the built-in text classes.

All style attributes (including those not present in a document) default to
``None`` (including the so-called "boolean" styles listed above).  The meaning
of a ``None`` style is style- and application-dependent.
"""
from __future__ import annotations

import re
import sys
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generator

from pyglet import event
from pyglet.text import runlist

if TYPE_CHECKING:
    from pyglet.font.base import Font
    from pyglet.text.layout import TextLayout

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run

#: The style attribute takes on multiple values in the document.
STYLE_INDETERMINATE = "indeterminate"


class InlineElement(ABC):
    """Arbitrary inline element positioned within a formatted document.

    Elements behave like a single glyph in the document.  They are
    measured by their horizontal advance, ascent above the baseline, and
    descent below the baseline.

    The pyglet layout classes reserve space in the layout for elements and
    call the element's methods to ensure they are rendered at the
    appropriate position.

    If the size of an element (any of the ``advance``, ``ascent``, or ``descent``
    variables) is modified it is the application's responsibility to
    trigger a reflow of the appropriate area in the affected layouts.  This
    can be done by forcing a style change over the element's position.
    """
    advance: int
    descent: int
    ascent: int
    _position: int | None

    def __init__(self, ascent: int, descent: int, advance: int) -> None:
        """Initialize the element.

        Args:
            ascent:
                Ascent of the element above the baseline, in pixels.
            descent:
                Descent of the element below the baseline, in pixels. Typically negative.
            advance:
                Width of the element, in pixels.
        """
        self.ascent = ascent
        self.descent = descent
        self.advance = advance
        self._position = None

    @property
    def position(self) -> int | None:
        """Character position within the document.

        Determined by the layout it is in. Will return ``None`` if it has not been placed.
        """
        return self._position

    @abstractmethod
    def place(self, layout: TextLayout, x: float, y: float, z: float, line_x: float, line_y: float, rotation: float,
              visible: bool, anchor_x: float, anchor_y: float) -> None:
        ...

    @abstractmethod
    def update_translation(self, x: float, y: float, z: float) -> None:
        ...

    @abstractmethod
    def update_color(self, color: list[int]) -> None:
        ...

    @abstractmethod
    def update_view_translation(self, translate_x: float, translate_y: float) -> None:
        ...

    @abstractmethod
    def update_rotation(self, rotation: float) -> None:
        ...

    @abstractmethod
    def update_visibility(self, visible: bool) -> None:
        ...

    @abstractmethod
    def update_anchor(self, anchor_x: float, anchor_y: float) -> None:
        ...

    @abstractmethod
    def remove(self, layout: TextLayout) -> None:
        ...


class AbstractDocument(event.EventDispatcher):
    """Abstract document interface used by all :py:mod:`pyglet.text` classes.

    This class can be overridden to interface pyglet with a third-party
    document format.  It may be easier to implement the document format in
    terms of one of the supplied concrete classes :py:class:`~pyglet.text.document.FormattedDocument` or
    :py:class:`~pyglet.text.document.UnformattedDocument`.
    """
    _previous_paragraph_re: re.Pattern[str] = re.compile("\n[^\n\u2029]*$")
    _next_paragraph_re: re.Pattern[str] = re.compile("[\n\u2029]")

    def __init__(self, text: str = "") -> None:
        """Initialize a document with text.

        Args:
            text: Initial text string.
        """
        super().__init__()

        self._text = ""
        self._elements: list[InlineElement] = []
        if text:
            self.append_text(text)

    @property
    def text(self) -> str:
        """Document text.

        For efficient incremental updates, use the :py:func:`~pyglet.text.document.AbstractDocument.insert_text` and
        :py:func:`~pyglet.text.document.AbstractDocument.delete_text` methods instead of replacing this property.

        """
        return self._text

    @text.setter
    def text(self, text: str) -> None:
        if text == self._text:
            return
        self.delete_text(0, len(self._text))
        self.insert_text(0, text)

    def get_paragraph_start(self, pos: int) -> int:
        """Get the starting position of a paragraph from the character position."""
        # Tricky special case where the $ in pattern matches before the
        # \n at the end of the string instead of the end of the string.
        if self._text[:pos + 1].endswith("\n") or self._text[:pos + 1].endswith("\u2029"):
            return pos

        m: re.Match[str] | None = self._previous_paragraph_re.search(self._text, 0, pos + 1)
        if not m:
            return 0
        return m.start() + 1

    def get_paragraph_end(self, pos: int) -> int:
        """Get the end position of a paragraph from the character position."""
        m: re.Match[str] | None = self._next_paragraph_re.search(self._text, pos)
        if not m:
            return len(self._text)
        return m.start() + 1

    @abstractmethod
    def get_style_runs(self, attribute: str) -> runlist.AbstractRunIterator:
        """Get a style iterator over the given style attribute.

        Args:
            attribute:
                Name of style attribute to query.
        """

    @abstractmethod
    def get_style(self, attribute: str, position: int = 0) -> Any:
        """Get an attribute style at the given position.

        Args:
            attribute:
                Name of style attribute to query.
            position:
                Character position of document to query.

        Returns:
            The style set for the attribute at the given position.
        """

    def get_style_range(self, attribute: str, start: int, end: int) -> Any:
        """Get an attribute style over the given range.

        If the style varies over the range, `STYLE_INDETERMINATE` is returned.

        Args:
            attribute:
                Name of style attribute to query.
            start:
                Starting character position.
            end:
                Ending character position (exclusive).

        Returns:
            The style set for the attribute over the given range, or `STYLE_INDETERMINATE` if more than one value is
            set.
        """
        iterable: runlist.AbstractRunIterator = self.get_style_runs(attribute)
        _, value_end, value = next(iterable.ranges(start, end))
        if value_end < end:
            return STYLE_INDETERMINATE

        return value

    @abstractmethod
    def get_font_runs(self, dpi: int | None = None) -> runlist.AbstractRunIterator:
        """Get a style iterator over the `pyglet.font.Font` instances used in the document.

        The font instances are created on-demand by inspection of the
        ``font_name``, ``font_size``, ``bold`` and ``italic`` style
        attributes.

        Args:
            dpi:
                Optional resolution to construct fonts at.
                :see: :py:func:`~pyglet.font.load`.
        """

    @abstractmethod
    def get_font(self, position: int, dpi: int | None = None) -> Font:
        """Get the font instance used at the given position.

        :see: `get_font_runs`

        Args:
            position:
                Character position of document to query.
            dpi:
                Optional resolution to construct fonts at.
                :see: :py:func:`~pyglet.font.load`.
        """

    def insert_text(self, start: int, text: str, attributes: dict[str, Any] | None = None) -> None:  # noqa: D417
        """Insert text into the document.

        Dispatches an :py:meth:`~pyglet.text.document.AbstractDocument.on_insert_text` event.

        Args:
            start:
                Character insertion point within document.
            text:
                Text to insert.
            attributes:
                Optional dictionary giving named style attributes of the inserted text.
        """  # noqa: D411, D405, D214, D410
        self._insert_text(start, text, attributes)
        self.dispatch_event("on_insert_text", start, text)

    def _insert_text(self, start: int, text: str, attributes: dict[str, Any] | None) -> None:  # noqa: ARG002
        self._text = "".join((self._text[:start], text, self._text[start:]))
        len_text = len(text)
        for element in self._elements:
            assert element._position is not None  # noqa: SLF001
            if element._position >= start:  # noqa: SLF001
                element._position += len_text  # noqa: SLF001

    def append_text(self, text: str, attributes: dict[str, Any] | None = None) -> None:
        """Append text into the end of document.

        Dispatches an :py:meth:`~pyglet.text.document.AbstractDocument.on_insert_text` event.

        Args:
            text:
                Text to append.
            attributes:
                Optional dictionary giving named style attributes of the appended text.
        """  # noqa: D411, D405, D214, D410
        start = len(self._text)
        self._append_text(text, attributes)
        self.dispatch_event("on_insert_text", start, text)

    def _append_text(self, text: str, attributes: dict[str, Any] | None) -> None:
        self._text += text

    def delete_text(self, start: int, end: int) -> None:
        """Delete text from the document.

        Dispatches an :py:meth:`on_delete_text` event.

        Args:
            start:
                Starting character position to delete from.
            end:
                Ending character position to delete to (exclusive).

        """
        self._delete_text(start, end)
        self.dispatch_event("on_delete_text", start, end)

    def _delete_text(self, start: int, end: int) -> None:
        for element in list(self._elements):
            assert element.position is not None
            if start <= element._position < end: # noqa: SLF001
                self._elements.remove(element)
            elif element._position >= end:  # fixes #538  # noqa: SLF001
                element._position -= (end - start)  # noqa: SLF001

        self._text = self._text[:start] + self._text[end:]

    def insert_element(self, position: int, element: InlineElement,
                       attributes: dict[str, Any] | None = None) -> None:
        """Insert a element into the document.

        See the :py:class:`~pyglet.text.document.InlineElement` class documentation for details of usage.

        Args:
            position:
                Character insertion point within document.
            element:
                Element to insert.
            attributes: dict
                Optional dictionary giving named style attributes of the inserted text.

        """
        assert element.position is None, "Element is already in a document."
        self.insert_text(position, "\0", attributes)
        element._position = position  # noqa: SLF001
        self._elements.append(element)

        # All _elements should have a valid position assigned.
        self._elements.sort(key=lambda d: d.position)  # type: ignore[arg-type, return-value]

    def get_element(self, position: int) -> InlineElement:
        """Get the element at a specified position.

        Args:
            position:
                Position in the document of the element.

        """
        for element in self._elements:
            if element._position == position:  # noqa: SLF001
                return element
        msg = f"No element at position {position}"
        raise RuntimeError(msg)

    def set_style(self, start: int, end: int, attributes: dict[str, Any]) -> None:  # noqa: D417
        """Set text style of a range between start and end of the document.

        Dispatches an :py:meth:`~pyglet.text.document.AbstractDocument.on_style_text` event.

        Args:
            start:
                Starting character position.
            end:
                Ending character position (exclusive).
            attributes:
                Dictionary giving named style attributes of the text.

        """  # noqa: D214, D405, D411, D410
        self._set_style(start, end, attributes)
        self.dispatch_event("on_style_text", start, end, attributes)

    @abstractmethod
    def _set_style(self, start: int, end: int, attributes: dict[str, Any]) -> None:
        ...

    def set_paragraph_style(self, start: int, end: int, attributes: dict[str, Any]) -> None:  # noqa: D417
        """Set the style for a range of paragraphs.

        This is a convenience method for `set_style` that aligns the character range to the enclosing paragraph(s).

        Dispatches an :py:meth:`~pyglet.text.document.AbstractDocument.on_style_text` event.

        Args:
            start:
                Starting character position.
            end:
                Ending character position (exclusive).
            attributes:
                Dictionary giving named style attributes of the paragraphs.

        """  # noqa: D214, D405, D411, D410
        start = self.get_paragraph_start(start)
        end = self.get_paragraph_end(end)
        self._set_style(start, end, attributes)
        self.dispatch_event("on_style_text", start, end, attributes)

    if _is_pyglet_doc_run:
        def on_insert_text(self, start: int, text: str) -> None:
            """Text was inserted into the document.

            Args:
                start:
                    Character insertion point within document.
                text:
                    The text that was inserted.

            :event:
            """

        def on_delete_text(self, start: int, end: int) -> None:
            """Text was deleted from the document.

            Args:
                start:
                    Starting character position of deleted text.
                end:
                    Ending character position of deleted text (exclusive).

            :event:
            """

        def on_style_text(self, start: int, end: int, attributes: dict[str, Any] | None) -> None:  # noqa: D417
            """Text character style was modified.

            Args:
                start:
                    Starting character position of modified text.
                end:
                    Ending character position of modified text (exclusive).
                attributes:
                    Dictionary giving updated named style attributes of the text.

            :event:
            """  # noqa: D214, D405, D411, D410


AbstractDocument.register_event_type("on_insert_text")
AbstractDocument.register_event_type("on_delete_text")
AbstractDocument.register_event_type("on_style_text")


class UnformattedDocument(AbstractDocument):
    """A document having uniform style over all text.

    Changes to the style of text within the document affects the entire
    document.  For convenience, the ``position`` parameters of the style
    methods may therefore be omitted.
    """

    def __init__(self, text: str = "") -> None:
        """Create unformatted document with a string."""
        super().__init__(text)
        self.styles: dict[str, Any] = {}

    def get_style_runs(self, attribute: str) -> runlist.ConstRunIterator:
        value = self.styles.get(attribute)
        return runlist.ConstRunIterator(len(self.text), value)

    def get_style(self, attribute: str, position: int | None = None) -> Any:  # noqa: ARG002
        return self.styles.get(attribute)

    def set_style(self, start: int, end: int, attributes: dict[str, Any]) -> None:  # noqa: ARG002
        return super().set_style(0, len(self.text), attributes)

    def _set_style(self, start: int, end: int, attributes: dict[str, Any]) -> None:  # noqa: ARG002
        self.styles.update(attributes)

    def set_paragraph_style(self, start: int, end: int, attributes: dict[str, Any]) -> None:  # noqa: ARG002
        return super().set_paragraph_style(0, len(self.text), attributes)

    def get_font_runs(self, dpi: int | None = None) -> runlist.ConstRunIterator:
        ft: Font = self.get_font(dpi=dpi)
        return runlist.ConstRunIterator(len(self.text), ft)

    def get_font(self, position: int | None = None, dpi: int | None = None) -> Font:  # noqa: ARG002
        from pyglet import font
        font_name = self.styles.get("font_name")
        font_size = self.styles.get("font_size")
        bold = self.styles.get("bold", False)
        italic = self.styles.get("italic", False)
        stretch = self.styles.get("stretch", False)
        return font.load(font_name, font_size, bold=bold, italic=italic, stretch=stretch, dpi=dpi)

    def get_element_runs(self) -> runlist.ConstRunIterator:
        return runlist.ConstRunIterator(len(self._text), None)


class FormattedDocument(AbstractDocument):
    """Simple implementation of a document that maintains text formatting.

    Changes to text style are applied according to the description in
    :py:class:`~pyglet.text.document.AbstractDocument`.  All styles default to ``None``.
    """

    def __init__(self, text: str = "") -> None:  # noqa: D107
        self._style_runs: dict[str, runlist.RunList] = {}
        super().__init__(text)

    def get_style_runs(self, attribute: str) -> runlist.RunIterator | _NoStyleRangeIterator:
        try:
            return self._style_runs[attribute].get_run_iterator()
        except KeyError:
            return _no_style_range_iterator

    def get_style(self, attribute: str, position: int = 0) -> Any | None:
        try:
            return self._style_runs[attribute][position]
        except KeyError:
            return None

    def _set_style(self, start: int, end: int, attributes: dict[str, Any]) -> None:
        for attribute, value in attributes.items():
            try:
                runs = self._style_runs[attribute]
            except KeyError:
                runs = self._style_runs[attribute] = runlist.RunList(0, None)
                runs.insert(0, len(self._text))
            runs.set_run(start, end, value)

    def get_font_runs(self, dpi: int | None = None) -> _FontStyleRunsRangeIterator:
        return _FontStyleRunsRangeIterator(
            self.get_style_runs("font_name"),
            self.get_style_runs("font_size"),
            self.get_style_runs("bold"),
            self.get_style_runs("italic"),
            self.get_style_runs("stretch"),
            dpi)

    def get_font(self, position: int, dpi: int | None = None) -> Font:
        runs_iter = self.get_font_runs(dpi)
        return runs_iter[position]

    def get_element_runs(self) -> _ElementIterator:
        return _ElementIterator(self._elements, len(self._text))

    def _insert_text(self, start: int, text: str, attributes: dict[str, Any] | None) -> None:
        super()._insert_text(start, text, attributes)

        len_text = len(text)
        if attributes is None:
            for runs in self._style_runs.values():
                runs.insert(start, len_text)

        else:
            for name, runs in self._style_runs.items():
                if name not in attributes:
                    runs.insert(start, len_text)

            for attribute, value in attributes.items():
                try:
                    runs = self._style_runs[attribute]
                except KeyError:
                    runs = self._style_runs[attribute] = runlist.RunList(0, None)
                    runs.append(len(self.text))
                    runs.set_run(start, start+len_text, value)
                else:
                    runs.insert_run(start, len_text, value)

    def _append_text(self, text: str, attributes: dict[str, Any] | None) -> None:
        super()._append_text(text, attributes)

        len_text = len(text)
        if attributes is None:
            for runs in self._style_runs.values():
                runs.append(len_text)

        else:
            for name, runs in self._style_runs.items():
                if name not in attributes:
                    runs.append(len_text)

            for attribute, value in attributes.items():
                try:
                    runs = self._style_runs[attribute]
                except KeyError:
                    runs = self._style_runs[attribute] = runlist.RunList(0, None)
                    runs.append(len(self.text) - len_text)
                runs.append_run(len_text, value)

    def _delete_text(self, start: int, end: int) -> None:
        super()._delete_text(start, end)
        for runs in self._style_runs.values():
            runs.delete(start, end)


def _iter_elements(elements: list[InlineElement], length: int) -> Generator[
    tuple[int, int, InlineElement | None], None, None]:
    last = 0
    for element in elements:
        p = element.position
        assert p is not None
        yield last, p, None
        yield p, p + 1, element
        last = p + 1
    yield last, length, None


class _ElementIterator(runlist.RunIterator):
    def __init__(self, elements: list[InlineElement], length: int) -> None:
        self._run_list_iter = _iter_elements(elements, length)
        self.start, self.end, self.value = next(self)


class _FontStyleRunsRangeIterator(runlist.RunIterator):
    # XXX subclass runlist
    def __init__(self, font_names: runlist.RunIterator, font_sizes: runlist.RunIterator, bolds: runlist.RunIterator,
                 italics: runlist.RunIterator, stretch: runlist.RunIterator, dpi: int | None) -> None:
        self.zip_iter = runlist.ZipRunIterator((font_names, font_sizes, bolds, italics, stretch))
        self.dpi = dpi

    def ranges(self, start: int, end: int) -> Generator[tuple[int, int, Font], None, None]:
        from pyglet import font
        for start_, end_, styles in self.zip_iter.ranges(start, end):
            font_name, font_size, bold, italic, stretch = styles
            ft = font.load(font_name, font_size, bold=bool(bold), italic=bool(italic), stretch=stretch, dpi=self.dpi)
            yield start_, end_, ft

    def __getitem__(self, index: int) -> Font:
        from pyglet import font
        font_name, font_size, bold, italic, stretch = self.zip_iter[index]
        return font.load(font_name, font_size, bold=bool(bold), italic=bool(italic), stretch=stretch, dpi=self.dpi)


class _NoStyleRangeIterator(runlist.RunIterator):
    def __init__(self) -> None:
        pass

    def ranges(self, start: int, end: int) -> Generator[tuple[int, int, None], None, None]:
        yield start, end, None

    def __getitem__(self, index: int) -> None:
        return None


_no_style_range_iterator = _NoStyleRangeIterator()
