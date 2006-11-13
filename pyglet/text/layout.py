#!/usr/bin/env python

'''
'''

from OpenGL.GL import *

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

class Align:
    """Enumeration of alignments."""
    left, right, top, bottom, center = range(5)

class Style:
    """A character style.

    Currently consists of just a font instance and a color, but could
    be marked up later to include things like underlining, super and
    subscript, etc."""
    def __init__(self, font, color):
        """Create a new character style.

        :Parameters:
            `font` : pyglet.text.Font
                Font instance for this style
            `color` : 3 or 4-tuple of float
                Color passed to glColor
        """
        self.font = font
        self.color = color
   
    def tuple(self):
        return (self.font, self.color)

    def __cmp__(self, other):
        return cmp(self.tuple(), other.tuple())

    def __hash__(self):
        return hash(self.tuple())

class StyledRun:
    """A sequence of characters with the same character style.
   
    The internal representation is the list of boxes returned by
    `pyglet.text.Font.get_boxes`.  The run can be translated
    in space (equivalent to ``glTranslate``) and sliced efficiently.
    """
    def __init__(self, text, style, boxes=None, advance=None):
        """Construct a styled run of text.

        :Parameters:
            `text` : str
                Text or unicode text to be displayed
            `style` : Style
                Style to format these characters with
            `boxes`
                List of boxes obtained from
                `pyglet.text.Font.get_boxes`.  If omitted, will
                be calculated.
            `advance` : number
                Horizontal advance for the run.  Will be calculated if
                omitted.
        """

        self.text = text
        self.style = style
        if not boxes or not advance:
            self.boxes, self.advance = style.font.get_boxes(text)
        else:
            self.boxes = boxes
            self.advance = advance

    def slice(self, start=0, end=None):
        """Return a new StyledRun which is a slice of this one.

        The parameter semantics are the same as a Python built-in slice.
        """
        r = StyledRun(self.text[start:end],
                      self.style,
                      self.boxes[start:end],
                      self.boxes[(end or 0)-1][0][2] - self.boxes[start][0][0])
        r.translate(-r.boxes[0][0][0], 0)
        return r

    def translate(self, x, y):
        """Translate this slice by the given deltas."""
        self.boxes = [((box[0][0] + x,
                        box[0][1] + y,
                        box[0][2] + x,
                        box[0][3] + y),
                       box[1]) for box in self.boxes]

    def __repr__(self):
        return 'StyledRun(%s, %s)' % (self.text, self.style)

class ParagraphMarker:
    """A paragraph style that can be inserted into a layout.
   
    Currently the only paragraph-level attribute is justification, but
    future expected attributes are margin, leading, hanging indent,
    and so on.
    """
    def __init__(self, style, justification=Align.left):
        """Construct a ParagraphMarker with the given style attributes.
       
        :Parameters:
            `style` : Style
                Style for this paragraph marker (not used).
            `justification` : int
                Valid justifications are
                  * `pyglet.text.layout.Align.left`
                  * `pyglet.text.layout.Align.right`
                  * `pyglet.text.layout.Align.center`
                defaults to `pyglet.text.layout.Align.left`.
        """
        self.style = style
        self.justification = justification

class StyledRunLine:
    """A completed line of laid-out text.

    The line consists of a list of `StyledRun`.  In the future the width
    and height attributes may be used to efficiently cull text not
    visible in a viewport.  Currently this class is a little redundant
    though."""
    def __init__(self, runs, width, height):
        """Construct a new StyledRunLine with the given runs."""
        self.runs = runs
        # TODO width height necessary?
        self.width = width
        self.height = height

    def __repr__(self):
        return 'StyledRunLine(%s, %d, %d)' % \
            (self.runs, self.width, self.height)

class TextLayout:
    """Automatic line-wrapping and justification of attributed text.

    To use this class directly, instantiate it with the width of the
    box the text will be flowed into.  Then call `layout` with a list
    of all `StyledRun` of text.  The resultant lines are then available
    in the ``lines`` attribute, which is a list of `StyledRunLine`.

    For rendering the text, see `OpenGLTextLayout`.
    """
    def __init__(self, width=-1):
        """Construct a TextLayout of the given width.

        :Parameters:
            `width` : int
                Width of the layout, in pixels.  Text will be wrapped into
                this width.  If -1, text will not be wrapped and width
                will expand to fit text.

        The layout can be reused by calling `layout` as many times as
        necessary; ``lines`` will be cleared each time.
        """

        self.width = width
        self.height = 0

    def words(self, runs):
        """Find potential breakpoints in a list of runs.

        This is a generator method that returns breakpoints continuously
        until all have been found.  Each return value is a list of
        `StyledRun`.
        """
        buffer = []
        for run in runs:
            if isinstance(run, ParagraphMarker):
                if buffer:
                    yield buffer
                    buffer = []
                yield run
            else:
                idx = run.text.find(' ')
                start = 0
                while idx != -1:
                    if start != idx:
                        buffer.append(run.slice(start, idx))
                    yield buffer
                    buffer = []
                    start = idx + 1
                    idx = run.text.find(' ', start)
                if start < len(run.text):
                    buffer.append(run.slice(start, None))
        if buffer:
            yield buffer

    def _commit_line(self):
        if self.current_line:
            self.y -= self.current_line_ascent - self.last_line_descent
            x = 0
            if self.justification == Align.right:
                x = self.width - self.current_line_width
            elif self.justification == Align.center:
                x = (self.width - self.current_line_width) / 2
            for run in self.current_line:
                run.translate(x, self.y)
            self.lines.append(StyledRunLine(self.current_line,
                                            self.current_line_width, -1))
            self.last_line_descent = self.current_line_descent
        else:
            self.y -= self.current_line_ascent - self.last_line_descent
        self.current_line = []
        self.current_line_width = 0
        self.current_line_ascent = 0
        self.current_line_descent = 0
        self.spacer_advance = 0
           
    def layout(self, runs):
        """Layout attributed text into the flow width.

        :Parameters:
            `runs` : list
                Each element of the list is either a `StyledRun` or
                `ParagraphMarker`.

        There is no return value, but the ``lines`` attribute is set to
        a list of `StyledRunLine`.
        """
        self.height = 0
        self.lines = []
        self.current_line = []
        self.current_line_width = 0
        self.current_line_ascent = 0
        self.current_line_descent = 0
        self.last_line_descent = 0
        self.spacer_advance = 0
        self.justification = Align.left
        self.y = 0
        for word in self.words(runs):
            if isinstance(word, ParagraphMarker):
                self.current_line_ascent = max(self.current_line_ascent,
                    word.style.font.ascent)
                self.current_line_descent = min(self.current_line_descent,
                    word.style.font.descent)
                self._commit_line()
                self.justification = word.justification
                continue

            if self.current_line:
                spacer = StyledRun(' ', self.current_line[-1].style)
                self.spacer_advance = spacer.advance

            self.word_advance = reduce(lambda a,b:a + b.advance, word, 0)
            if (self.word_advance + self.spacer_advance +
                    self.current_line_width > self.width and self.width != -1):
                self._commit_line()

            x = self.current_line_width + self.spacer_advance
            for run in word:
                run.translate(x, 0)
                x += run.advance

            self.current_line += word
            self.current_line_width += self.word_advance + self.spacer_advance
            self.current_line_ascent = max(self.current_line_ascent,
                reduce(lambda a,b:max(a,b.style.font.ascent), word, 0))
            self.current_line_descent = min(self.current_line_descent,
                reduce(lambda a,b:min(a,b.style.font.descent), word, 0))

        if self.current_line:
            self._commit_line()
        self.height = -self.y - self.last_line_descent
        if self.width == -1:
            self.width = x

    def draw(self):
        """Subclasses override this method for implementation-specific
        rendering."""
        raise NotImplementedError()

class OpenGLTextLayout(TextLayout):
    """Text layout for rendering in OpenGL.

    In addition to performing text layout, OpenGL state changes are grouped
    together and minimised in order to increase drawing efficiency.
    """

    def __init__(self, *args, **kwargs):
        """Construct a OpenGLTextLayout.

        See `TextLayout.__init__` for accepted parameters.
        """
        TextLayout.__init__(self, *args, **kwargs)
        self._contexts = {}

    def layout(self, runs):
        """Layout attributed text into the flow width.

        This method extends `TextLayout.layout` by finding OpenGL state
        changes and sorting on them for rendering efficiency.
        """
        TextLayout.layout(self, runs)
        self._contexts = {}
        runs = reduce(lambda a,b: a + b.runs, self.lines, [])
        for run in runs:
            if not run.style in self._contexts:
               self._contexts[run.style] = []
            self._contexts[run.style] += run.boxes

    def draw(self, pos=(0,0), anchor=(Align.left, Align.top)):
        """Draw the layout to the current GL context.

        :Parameters:
            `pos` : tuple of (int, int)
                Position (x, y) to draw the layout
            `anchor` : tuple of (int, int)
                Alignment of anchor position (x, y), where x is one of:
                    * pyglet.text.layout.Align.left
                    * pyglet.text.layout.Align.center
                    * pyglet.text.layout.Align.right
                and y is one of
                    * pyglet.text.layout.Align.top
                    * pyglet.text.layout.Align.center
                    * pyglet.text.layout.Align.bottom.
                Defaults to left, top.

        The `anchor` and `pos` parameters determine the position of the
        layout in x, y coordinates.  For example, specifying ``pos = (50,20)``
        and ``anchor = (Align.center, Align.center)`` will center the
        layout on those coordinates.

        XXX This method assumes the context has the necessary drawing
        XXX state; see `pyglyph.begin`.
        """
        x, y = pos
        if anchor[0] == Align.center:
            x -= self.width/2
        elif anchor[0] == Align.right:
            x -= self.width
        if anchor[1] == Align.center:
            y += self.height/2
        elif anchor[1] == Align.bottom:
            y += self.height

        glTranslatef(x, y, 0)
        last_color = None
        for style, boxes in self._contexts.items():
            if style.color != last_color:
                glColor4f(*style.color)
            style.font.draw_boxes(boxes)
        glTranslatef(-x, -y, 0)

