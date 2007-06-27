#!/usr/bin/env python

'''A very minimalist sound and video player.  We are using this for testing
pyglet.media for now.  You can use it to test if a particular file format is
supported on your system::

    mediaplay.py <media-file>

pyglet uses the installed codecs on your operating system (gstreamer on Linux)
to play media; so for example you will need to download and install the OGG
codec to play OGG files.

There are some keyboard commands to alter playback at runtime which are
documented within the window (unless the video you're playing is mostly white,
in which case they won't be readable).
'''

import sys
import time

from pyglet.gl import *
from pyglet import clock
from pyglet import font
from pyglet import media
from pyglet import window
from pyglet import event
from pyglet.window import key

class MediaPlayWindow(window.Window):
    instance = None
    sound = None
    video = None

    def __init__(self, filename, *args, **kwargs):
        super(MediaPlayWindow, self).__init__(*args, **kwargs)

        # Load the medium, determine if it's video and/or audio
        medium = media.load(filename, streaming=True)
        if medium.has_video:
            self.instance = self.video = medium.get_video()
            self.sound = self.instance.sound
            self.width = self.video.width
            self.height = self.video.height
        elif medium.has_audio:
            self.sound = self.instance = medium.get_sound()

        if not self.sound and not self.video:
            raise Exception("Media file doesn't contain sound or video")

        self.instance.play()

        # Decorative labels

        self.y = self.height
        self.labels = []
        def add_label(text):
            l = font.Text(font.load('Arial', 12), text, color=(1, 1, 1, 1))
            l.x = 10
            l.y = self.y - l.height
            self.y -= l.height
            self.labels.append(l)
            return l

        add_label(filename)
        self.time_label = add_label('')
        self.fps_label = add_label('')
        add_label('')
        self.playing_label = add_label('Playing; press space to pause')
        self.volume_label = add_label('Volume 1.0; adjust with +,-')
        self.pitch_label = add_label('Pitch 1.0: adjust with [,]')
        self.position_label = add_label('Position 0,0,0: adjust with W,A,S,D')
        self.velocity_label = add_label('Velocity 0,0,0: adjust with I,J,K,L')

    def draw(self):
        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        if self.video:
            self.video.texture.blit(0, 0, 0)
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

    def add_velocity(self, dx, dy, dz):
        x, y, z = self.sound.velocity
        self.sound.velocity = x + dx, y + dy, z + dz
        self.velocity_label.text = \
            'Velocity %.2f, %.2f, %.2f; adjust with W,A,S,D' % \
                self.sound.velocity

    def add_pitch(self, pitch):
        self.sound.pitch += pitch
        self.pitch_label.text = \
            'Pitch %.2f; adjust with [,]' % self.sound.pitch

    def on_key_press(self, symbol, modifiers):
        if symbol == key.SPACE:
            if self.instance.playing:
                self.instance.pause()
                self.playing_label.text = 'Paused; press space to resume'
            else:
                self.instance.play()
                self.playing_label.text = 'Playing; press space to pause'
        elif symbol in (key.EQUAL, key.NUM_ADD):
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
        elif symbol == key.J:
            self.add_velocity(-.1, 0, 0)
        elif symbol == key.K:
            self.add_velocity(0, 0, .1)
        elif symbol == key.L:
            self.add_velocity(.1, 0, 0)
        elif symbol == key.I:
            self.add_velocity(0, 0, -.1)
        elif symbol == key.BRACKETLEFT:
            self.add_pitch(-0.1)
        elif symbol == key.BRACKETRIGHT:
            self.add_pitch(0.1)
        else:
            return super(MediaPlayWindow, self).on_key_press(symbol, modifiers)
        return event.EVENT_HANDLED

    def run(self):
        #clock.set_fps_limit(30)
        while not self.instance.finished and not self.has_exit:
            clock.tick()
            self.dispatch_events()
            media.dispatch_events()

            t = self.instance.time
            self.time_label.text = '%d:%05.2f' % \
                (int(t / 60), t - 60 * int(t / 60))
            self.fps_label.text = 'FPS: %.2f'%clock.get_fps()

            self.draw()

if __name__ == '__main__':
    filename = sys.argv[1]

    try:
        win = MediaPlayWindow(filename, width=400, height=150, resizable=True)
        win.run()
    finally:
        media.cleanup()
