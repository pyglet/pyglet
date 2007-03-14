#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import code
import sys
import traceback

import pyglet.event
import pyglet.text
from pyglet.window import key

from pyglet.gl import *

class Console(object):
    def __init__(self, width, height, globals=None, locals=None):
        self.font = pyglet.text.default_font_factory.get_font('bitstream vera sans mono', 12)
        self.lines = []
        self.buffer = ''
        self.pre_buffer = ''
        self.prompt = '>>> '
        self.prompt2 = '... '
        self.globals = globals
        self.locals = locals
        self.write_pending = ''

        self.width, self.height = (width, height)
        self.max_lines = self.height / self.font.glyph_height - 1

        self.write('pyglet command console\n')
        self.write('Version %s\n' % __version__)

    def on_key_press(self, symbol, modifiers):
        # TODO cursor control / line editing
        if modifiers & key.key.MOD_CTRL and symbol == key.key.C:
            self.buffer = ''
            self.pre_buffer = ''
            return
        if symbol == key.key.ENTER:
            self.write('%s%s\n' % (self.get_prompt(), self.buffer))
            self.execute(self.pre_buffer + self.buffer)
            self.buffer = ''
            return
        if symbol == key.key.BACKSPACE:
            self.buffer = self.buffer[:-1]
            return
        return EVENT_UNHANDLED

    def on_text(self, text):
        if ' ' <= text <= '~':
            self.buffer += text
        if 0xae <= ord(text) <= 0xff:
            self.buffer += text

    def write(self, text):
        if self.write_pending:
            text = self.write_pending + text
            self.write_pending = ''

        if type(text) in (str, unicode):
            text = text.split('\n')

        if text[-1] != '':
            self.write_pending = text[-1]
        del text[-1]

        self.lines = [pyglet.text.layout_text(line.strip(), font=self.font)
             for line in text] + self.lines

        if len(self.lines) > self.max_lines:
            del self.lines[-1]

    def execute(self, input):
        old_stderr, old_stdout = sys.stderr, sys.stdout
        sys.stderr = sys.stdout = self
        try:
            c = code.compile_command(input, '<pyglet console>')
            if c is None:
                self.pre_buffer = '%s\n' % input
            else:
                self.pre_buffer = ''
                result = eval(c, self.globals, self.locals)
                if result is not None:
                    self.write('%r\n' % result)
        except:
            traceback.print_exc()
            self.pre_buffer = ''
        sys.stderr = old_stderr
        sys.stdout = old_stdout

    def get_prompt(self):
        if self.pre_buffer:
            return self.prompt2
        return self.prompt

    __last = None
    def draw(self):
        pyglet.text.begin()
        glPushMatrix()
        glTranslatef(0, self.height, 0)
        for line in self.lines[::-1]:
            line.draw()
            glTranslatef(0, -self.font.glyph_height, 0)
        line = self.get_prompt() + self.buffer
        if self.__last is None or line != self.__last[0]:
            self.__last = (line, pyglet.text.layout_text(line.strip(),
                font=self.font))
        self.__last[1].draw()
        glPopMatrix()

        pyglet.text.end()

if __name__ == '__main__':
    from pyglet.window import *
    from pyglet.window.event import *
    from pyglet import clock
    w1 = Window(width=600, height=400)
    console = Console(w1.width, w1.height)

    w1.push_handlers(console)

    c = clock.Clock()

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, w1.width, 0, w1.height, -1, 1)
    glEnable(GL_COLOR_MATERIAL)

    glMatrixMode(GL_MODELVIEW)
    glClearColor(1, 1, 1, 1)
    while not w1.has_exit:
        c.set_fps(60)
        w1.dispatch_events()
        glClear(GL_COLOR_BUFFER_BIT)
        console.draw()
        w1.flip()

