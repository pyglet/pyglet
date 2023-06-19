#!/usr/bin/env python
"""A simple tool that may be used to explore font faces. (Windows only)

Only the fonts installed in the system are visible.

Use the left/right cursor keys to change font faces.

By default only the pyglet safe fonts are shown, toggle the safe flag
to see all.

Don't include tabs in the text sample (see
http://pyglet.org/doc-current/programming_guide/text.html#id9 )
"""
import warnings

import pyglet

pyglet.options["win32_gdi_font"] = True
warnings.warn("This example uses a deprecated font renderer.")
import pyglet.font.win32query as wq

if pyglet.compat_platform != 'win32':
    print("This example is only for Windows")
    exit()


# support to generate a sample text good to spot monospace compliance.
# Chosen to do a table of fields_per_line columns, each column with field_size
# characters. Fields are filled with a rolling subset of ASCII characters.
class SampleTable:
    field_size = 7
    gap_size = 3
    fields_per_line = 7
    spaces = ' ' * field_size
    max_chars_per_line = (field_size + gap_size) * fields_per_line - gap_size

    def __init__(self):
        self.lines = []
        self.current_line = ''

    def newline(self):
        self.lines.append(self.current_line)
        self.current_line = ''

    def add_field(self, s):
        assert len(s) <= self.field_size
        to_add = self.spaces[len(s):] + s
        if self.current_line:
            to_add = ' ' * self.gap_size + to_add
        if len(self.current_line) + len(to_add) > self.max_chars_per_line:
            self.newline()
            self.add_field(s)
        else:
            self.current_line = self.current_line + to_add

    def text(self):
        return '\n'.join(self.lines)


def sample_text_monospaced_table():
    printables = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ '
    table = SampleTable()
    for i in range(6):
        s = printables[i:] + printables[:i]
        for k in range(0, len(printables), table.field_size):
            table.add_field(s[k:k + table.field_size])
        table.newline()
    return table.text()


# this worked right with all fonts in a win xp installation
def pyglet_safe(fontentry):
    """ this is heuristic and conservative. YMMV. """
    return fontentry.vector and fontentry.family != wq.FF_DONTCARE


class Window(pyglet.window.Window):
    font_num = 0

    def on_text_motion(self, motion):
        if motion == pyglet.window.key.MOTION_RIGHT:
            self.font_num += 1
            if self.font_num == len(font_names):
                self.font_num = 0
        elif motion == pyglet.window.key.MOTION_LEFT:
            self.font_num -= 1
            if self.font_num < 0:
                self.font_num = len(font_names) - 1

        face = font_names[self.font_num]
        self.head = pyglet.text.Label(face, font_size=16, y=0, anchor_y='bottom')
        self.text = pyglet.text.Label(sample_text, font_name=face, font_size=12,
                                      y=self.height, anchor_y='top', width=self.width,
                                      multiline=True)

    def on_draw(self):
        self.clear()
        self.head.draw()
        self.text.draw()


lorem_ipsum = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec a diam lectus.
Sed sit amet ipsum mauris. Maecenas congue ligula ac quam viverra nec
consectetur ante hendrerit. Donec et mollis dolor. Praesent et diam eget
libero egestas mattis sit amet vitae augue.


"""

if __name__ == '__main__':
    print(__doc__)
    safe = True
    sample_text = lorem_ipsum + sample_text_monospaced_table()
    # all fonts known by the OS
    fontdb = wq.query()

    if safe:
        candidates = [f for f in fontdb if pyglet_safe(f)]
    else:
        canditates = fontdb

    # theres one fontentry for each charset supported, so reduce names
    font_names = list(set([f.name for f in candidates]))

    font_names.sort()
    window = Window(1024, 600)
    window.on_text_motion(None)
    pyglet.app.run()
