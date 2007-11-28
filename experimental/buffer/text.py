#!/usr/bin/python
# $Id:$

import graphics

from pyglet.gl import *

TextState = graphics.TextureState

class StyleRun(object):
    def __init__(self, start, style):
        self.start = start
        self.style = style

    def __repr__(self):
        return 'StyleRun(%d, %r)' % (self.start, self.style)

class StyleRuns(object):
    def __init__(self, size, initial):
        self.size = size
        self.runs = [StyleRun(0, initial)]

    def insert(self, pos, length):
        # TODO
        pass

    def remove(self, start, end):
        # TODO
        pass

    def set_style(self, start, end, style):
        assert 0 <= start < end <= self.size, 'Slice not in range'

        # Find indices of style runs before and after new style range
        start_index = None
        end_index = None
        end_style = None
        for i, run in enumerate(self.runs):
            if run.start >= start and start_index is None:
                start_index = i
            if run.start >= end:
                end_index = i
                break
            end_style = run.style
        if end_index is None:
            end_index = len(self.runs)
        if start_index is None:
            start_index = end_index
            
        # Remove old styles (may be nothing)
        del self.runs[start_index:end_index]
        
        # Insert new style unless unnecessary
        if len(self.runs) <= start_index or \
           self.runs[start_index].style != style:
            self.runs.insert(start_index, StyleRun(start, style))

        if end == self.size:
            return

        # Insert following style unless unnecessary
        if len(self.runs) <= start_index + 1 or \
           self.runs[start_index + 1].style != end_style:
            self.runs.insert(start_index + 1, StyleRun(end, end_style))

    
    def __iter__(self):
        last_run = None
        for run in self.runs:
            if last_run:
                yield last_run.start, run.start, last_run.style
            last_run = run
        yield last_run.start, self.size, last_run.style

    def iter_range(self, start, end):
        assert 0 <= start <= end <= self.size, 'Slice not in range'
        if start == end:
            raise StopIteration()

        last_run = None
        for run in self.runs:
            if run.start >= end:
                break
            if run.start > start:
                yield max(start, last_run.start), run.start, last_run.style
            last_run = run
        yield last_run.start, end, last_run.style

    def get_style_at(self, index):
        assert 0 <= index < self.size, 'Index not in range'
        last_run = None
        for run in self.runs:
            if run.start > index:
                return last_run.style
            last_run = run
        return last_run.style

class Line(object):
    def __init__(self):
        self.glyph_runs = []
        self.ascent = 0
        self.descent = 0
        self.width = 0

        self.x = None
        self.y = None

        self.vertex_lists = []

    def __repr__(self):
        return 'Line(%r)' % self.glyph_runs

    def add_word(self, word):
        self.glyph_runs.extend(word.glyph_runs)
        self.ascent = max(self.ascent, word.ascent)
        self.descent = min(self.descent, word.descent)

    def add_glyph_run(self, glyph_run):
        self.glyph_runs.append(glyph_run)
        self.ascent = max(self.ascent, glyph_run.font.ascent)
        self.descent = min(self.descent, glyph_run.font.descent)

class GlyphRun(object):
    def __init__(self, owner, font, glyphs):
        self.owner = owner
        self.font = font
        self.glyphs = glyphs

    def add_glyphs(self, glyphs):
        self.glyphs.extend(glyphs)

    def __repr__(self):
        return 'GlyphRun(%r)' % self.glyphs

class Word(object):
    def __init__(self):
        self.glyph_runs = [] 
        self.ascent = 0
        self.descent = 0
        self.width = 0

    def add_glyph_run(self, glyph_run):
        self.glyph_runs.append(glyph_run)
        self.ascent = max(self.ascent, glyph_run.font.ascent)
        self.descent = min(self.descent, glyph_run.font.descent)
        self.width += sum(g.advance for g in glyph_run.glyphs)

class Text2(object):
    def __init__(self, font, text, color=(255, 255, 255, 255), width=400,
                 batch=None):
        self.text = text
        self.width = width
        self.y = 480
        self.x = 0

        self.font_runs = StyleRuns(len(text), font)
        self.color_runs = StyleRuns(len(text), color)

        if batch is None:
            batch = graphics.Batch()
        self.batch = batch

        self.lines = []
        self.states = {}

    def _flow(self):
        self.lines = []
        self._build_line = None
        self._build_word = None

        for start, end, font in self.font_runs:
            self._flow_text(start, end, font)
        if self._build_word:
            self._build_line.add_word(self._build_word)
        if self._build_line.glyph_runs:
            self.lines.append(self._build_line)

        self._flow_lines()
        self._create_vertex_lists()

    def _flow_text(self, start, end, font):
        text = self.text[start:end]
        glyphs = font.get_glyphs(text)

        owner = glyphs[0].owner
        glyph_chars = []
        for c, glyph in zip(text, glyphs):
            if glyph.owner is not owner:
                self._flow_glyphs(glyph_chars, owner, font)
                owner = glyph.owner
                glyph_chars = []
            glyph_chars.append((glyph, c))
        self._flow_glyphs(glyph_chars, owner, font)

    def _flow_glyphs(self, glyph_chars, owner, font):
        if not self._build_line:
            self._build_line = Line()

        width = self.width
        line = self._build_line
        word = self._build_word
        run = GlyphRun(owner, font, [])
        accum = []
        x = line.width
        if word:
            x += word.width
        
        for glyph, c in glyph_chars:
            if c in u'\u0020\u200b':
                if word:
                    line.add_word(word)
                    word = self._build_word = None
                x += glyph.advance
                line.width = x
                accum.append(glyph)
                run.add_glyphs(accum)
                accum = []
            elif glyph.advance + x >= width:
                if run.glyphs:
                    line.add_glyph_run(run)
                self.lines.append(line)
                self._build_line = line = Line()
                run = GlyphRun(owner, font, [])
                x = sum(g.advance for g in accum)
                accum.append(glyph)
                x += glyph.advance
            else:
                accum.append(glyph)
                x += glyph.advance

        if run.glyphs:
            line.add_glyph_run(run)

        if x > width:
            self.lines.append(line)
            self.build_line = Line()

        if accum:
            if not word:
                self._build_word = word = Word()
            word.add_glyph_run(GlyphRun(owner, font, accum))

    def _flow_lines(self):
        y = self.y
        for line in self.lines:
            y -= line.ascent
            line.x = self.x
            line.y = y
            y += line.descent

    def _create_vertex_lists(self):
        batch = self.batch

        colors_iter = iter(self.color_runs)
        _, color_end, color = colors_iter.next()
        n_colors = color_end
        
        for line in self.lines:
            x = line.x
            y = line.y
            for glyph_run in line.glyph_runs:
                assert glyph_run.glyphs
                try:
                    state = self.states[glyph_run.owner]
                except KeyError:
                    owner = glyph_run.owner
                    self.states[owner] = state = TextState(owner)

                n_glyphs = len(glyph_run.glyphs)
                vertices = []
                tex_coords = []
                for glyph in glyph_run.glyphs:
                    v0, v1, v2, v3 = glyph.vertices
                    v0 += x
                    v2 += x
                    v1 += y
                    v3 += y
                    vertices.extend([v0, v1, v2, v1, v2, v3, v0, v3])
                    t = glyph.tex_coords
                    tex_coords.extend(t[0] + t[1] + t[2] + t[3])
                    x += glyph.advance
                
                colors = []
                ng = n_glyphs
                #import pdb; pdb.set_trace()
                while ng:
                    if n_colors == 0:
                        color_start, color_end, color = colors_iter.next()
                        n_colors = color_end - color_start
                    nc = min(ng, n_colors)
                    colors.extend(color * (nc * 4))
                    n_colors -= nc
                    ng -= nc

                list = batch.add(n_glyphs * 4, GL_QUADS, state, 
                    ('v2f/dynamic', vertices),
                    ('t3f/dynamic', tex_coords),
                    ('c4B/dynamic', colors))
                line.vertex_lists.append(list)

def test_text1(batch, width):
    from pyglet import font
    ft = font.load('Times New Roman', 36)
    ft2 = font.load('Times New Roman', 48, italic=True)
    ft3 = font.load('Times New Roman', 72, italic=True)
    text = Text2(ft, 'Hello, world!', batch=batch, width=width) 
    text.color_runs.set_style(7, 12, (100, 255, 255, 255))
    text.color_runs.set_style(0, 5, (255, 100, 100, 255))
    text.font_runs.set_style(8, 11, ft2)
    text.font_runs.set_style(9, 10, ft3)
    text._flow()
    return text

def test_text2(batch, width):
    from pyglet import font
    ft = font.load('Georgia', 72)
    text = Text2(ft, frog_prince.replace('\n', ' '), batch=batch, width=width)
    text._flow()
    return text

def main():
    from pyglet import window
    w = window.Window()

    batch = graphics.Batch()
    text = test_text1(batch, w.width)
    
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    while not w.has_exit:
        w.dispatch_events()
        w.clear()
        batch.draw()
        w.flip()

frog_prince = '''In olden times when wishing still
helped one, there lived a king whose daughters were all beautiful, but the
youngest was so beautiful that the sun itself, which has seen so much, was
astonished whenever it shone in her face.  Close by
the king's castle lay a great dark forest, and under an old lime-tree in the
forest was a well, and when the day was very warm, the king's child went out
into the forest and sat down by the side of the cool fountain, and when she
was bored she took a golden ball, and threw it up on high and caught it, and
this ball was her favorite plaything.'''

if __name__ == '__main__':
    main()
