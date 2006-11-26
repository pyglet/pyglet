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

from pyglet.GL.VERSION_1_1 import *

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
        self.max_lines = self.height / self.font.glyph_height #- 1

        self.write('pyglet command console\n')
        self.write('Version %s\n' % __version__)

        sys.stdout = self
        sys.stderr = self

    def on_key_press(self, symbol, modifiers):
        if symbol == key.K_ESCAPE:
            return EVENT_UNHANDLED

        if modifiers & key.MOD_CTRL and symbol == key.K_C:
            self.buffer = ''
            self.pre_buffer = ''
        else:
            if symbol == key.K_ENTER:
                self.write('%s%s\n' % (self.get_prompt(), self.buffer))
                self.execute(self.pre_buffer + self.buffer)
                self.buffer = ''
            elif symbol == key.K_BACKSPACE:
                self.buffer = self.buffer[:-1]
            elif key.K_SPACE <= symbol <= K_ASCIITILDE:
                self.buffer += character
            elif key.K_NOBREAKSPACE <= symbol <= K_YDIAERESIS:
                self.buffer += character

    def write(self, text):
        if self.write_pending:
            text = self.write_pending + text
            self.write_pending = ''

        if type(text) in (str, unicode):
            text = text.split('\n')

        if text[-1] != '':
            self.write_pending = text[-1]
        del text[-1]

        self.lines = [pyglet.text.layout_text(line, font)
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

    def draw(self):
        pyglet.text.begin()
        glPushMatrix()
        glTranslate(10, self.height + self.font.descent - 10, 0)
        self.font.draw(self.get_prompt() + self.buffer)
        for line in self.lines:
            glTranslate(0, -self.font.line_height, 0)
            line.draw()
        glPopMatrix()

        pyglet.text.end()

if __name__ == '__main__':
    from pyglet.window import *
    from pyglet.window.event import *
    from pyglet import clock
    w1 = Window(width=400, height=200)
    console = Console(w1.width, w1.height)

    exit_handler = ExitHandler()
    w1.push_handlers(exit_handler)

    c = clock.Clock()

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, w1.width, 0, w1.height, -1, 1)
    glEnable(GL_COLOR_MATERIAL)

    glMatrixMode(GL_MODELVIEW)
    glClearColor(1, 1, 1, 1)
    while not exit_handler.exit:
        c.set_fps(10)
        w1.dispatch_events()
        glClear(GL_COLOR_BUFFER_BIT)
        console.draw()
        w1.flip()

