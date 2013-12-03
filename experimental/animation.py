#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '1.2'

import sys

from pyglet import clock
from pyglet import image
from pyglet import window

class AnimationPlayer(object):
    expected_delay = 0

    def __init__(self, animation):
        self.animation = animation
        self.index = -1
        self.next_frame(0)

    def next_frame(self, dt):
        self.index = (self.index + 1) % len(self.animation.frames)
        frame = self.animation.frames[self.index]
        if frame.duration is not None:
            delay = frame.duration - (self.expected_delay - dt)
            delay = min(max(0, delay), frame.duration)
            clock.schedule_once(self.next_frame, delay)
            self.expected_delay = delay

    def blit(self, x, y):
        self.animation.frames[self.index].image.blit(x, y)

try:
    animation = image.load_animation(sys.argv[1])
except image.codecs.ImageDecodeException:
    from pyglet import media
    source = media.load(sys.argv[1])
    source._seek(0)
    animation = source.get_animation()
except IndexError:
    sys.exit('usage: animation.py <image>')


w = window.Window()

clock.tick()
player = AnimationPlayer(animation)

while not w.has_exit:
    clock.tick()

    w.dispatch_events()
    w.clear()
    player.blit(w.width//2, w.height//2)
    w.flip()
