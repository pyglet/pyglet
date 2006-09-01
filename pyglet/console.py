#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import code
import sys
import traceback

from OpenGL.GL import *
from SDL import *

import pyglet.event
import pyglet.font
import pyglet.window

class Console:
    def __init__(self, globals=None, locals=None):
        self.activate_key = SDLK_ESCAPE
        self.activate_modifiers = 0
        self.deactivate_key = SDLK_ESCAPE
        self.deactivate_modifiers = 0
        self.visible = False
        self.font = pyglet.font.Font('VeraMono.ttf', 12)
        self.lines = []
        self.buffer = ''
        self.pre_buffer = ''
        self.prompt = '>>> '
        self.prompt2 = '... '
        self.globals = globals
        self.locals = locals
        self.write_pending = ''

        self.width, self.height = pyglet.window.get_size()
        self.max_lines = \
            (self.height + self.font.descent) / self.font.line_height - 1

        self.write('pyglet command console\n')
        self.write('Version %s\n' % __version__)

        pyglet.event.on_keydown(self.hidden_keydown)
        sys.stdout = self
        sys.stderr = self

    def hidden_keydown(self, character, symbol, modifiers):
        if symbol == self.activate_key and \
           self.activate_modifiers & modifiers == self.activate_modifiers:
            self.show()
        else:
            return True

    def keydown(self, character, symbol, modifiers):
        if symbol == self.deactivate_key and \
           self.deactivate_modifiers & modifiers == self.deactivate_modifiers:
            self.hide()
        elif modifiers & KMOD_CTRL:
            if symbol == SDLK_c:
                self.buffer = ''
                self.pre_buffer = ''
        else:
            if symbol == SDLK_RETURN:
                self.write('%s%s\n' % (self.get_prompt(), self.buffer))
                self.execute(self.pre_buffer + self.buffer)
                self.buffer = ''
            elif symbol == SDLK_BACKSPACE:
                self.buffer = self.buffer[:-1]
            elif character != '\0':
                self.buffer += character

    def show(self):
        if not self.visible:
            pyglet.event.push()
            pyglet.event.on_keydown(self.keydown)
            self.visible = True

    def hide(self):
        if self.visible:
            pyglet.event.pop()
            self.visible = False

    def write(self, text):
        if self.write_pending:
            text = self.write_pending + text
            self.write_pending = ''

        if type(text) in (str, unicode):
            text = text.split('\n')

        if text[-1] != '':
            self.write_pending = text[-1]
        del text[-1]

        self.lines = [pyglet.font.TextSprite(self.font, line) \
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
        if not self.visible:
            return

        glPushMatrix()
        glTranslate(10, self.height + self.font.descent - 10, 0)
        self.font.draw(self.get_prompt() + self.buffer)
        for line in self.lines:
            glTranslate(0, -self.font.line_height, 0)
            line.draw()
        glPopMatrix()
