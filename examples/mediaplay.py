#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import sys
import time

from pyglet.gl import *
from pyglet import clock
from pyglet import font
from pyglet import media
from pyglet import window
from pyglet.window import key

class MediaPlayWindow(window.Window):
    def __init__(self, filename, *args, **kwargs):
        super(MediaPlayWindow, self).__init__(*args, **kwargs)

        self.y = self.height
        self.labels = []
        def add_label(text):
            l = font.Label(font.load('Arial', 12), text, color=(1, 1, 1, 1))
            l.x = 10
            l.y = self.y - l.height
            self.y -= l.height
            self.labels.append(l)
            return l

        add_label(filename)
        add_label('')
        self.playing_label = add_label('Playing; press space to pause')
        self.volume_label = add_label('Volume 1.0; adjust with +/-')
        self.position_label = add_label('Position 0,0,0: adjust with W,A,S,D')

        medium = media.load(filename, streaming=True)
        self.sound = medium.play()

    def draw(self):
        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        for label in self.labels:
            label.draw()
        self.flip()

    def add_volume(self, v):
        self.sound.volume += v
        self.volume_label.text = \
            'Volume %f; adjust with +/-' % self.sound.volume

    def add_position(self, dx, dy, dz):
        x, y, z = self.sound.position
        self.sound.position = x + dx, y + dy, z + dz
        self.position_label.text = \
            'Position %.2f, %.2f, %.2f; adjust with W,A,S,D' % \
                self.sound.position

    def on_key_press(self, symbol, modifiers):
        if symbol == key.SPACE:
            if self.sound.playing:
                self.sound.pause()
                self.playing_label.text = 'Paused; press space to resume'
            else:
                self.sound.play()
                self.playing_label.text = 'Playing; press space to pause'
        if symbol in (key.EQUAL, key.NUM_ADD):
            self.add_volume(.1)
        elif symbol in (key.MINUS, key.NUM_SUBTRACT):
            self.add_volume(-.1)
        elif symbol == key.A:
            self.add_position(-.1, 0, 0)
        elif symbol == key.S:
            self.add_position(0, 0, .1)
        elif symbol == key.D:
            self.add_position(.1, 0, 0)
        elif symbol == key.W:
            self.add_position(0, 0, -.1)

    def run(self):
        clock.set_fps_limit(30)
        while not self.sound.finished and not self.has_exit:
            clock.tick()
            self.dispatch_events()
            media.dispatch_events()

            self.draw()

if __name__ == '__main__':
    filename = sys.argv[1]

    win = MediaPlayWindow(filename, width=400, height=100)
    time.sleep(.1)
    win.run()

    media.cleanup()
