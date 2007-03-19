#!/usr/bin/python
# $Id:$

import ctypes

from pyglet.media import lib_openal as al
from pyglet.media import lib_alc as alc

def init():
    device = alc.alcOpenDevice(None)
    if not device:
        raise Exception('No OpenAL device.')

    alcontext = alc.alcCreateContext(device, None)
    alc.alcMakeContextCurrent(alcontext)

class BufferPool(list):
    def get(self):
        if not self:
            buffer = al.ALuint()
            al.alGenBuffers(1, buffer)
        else:
            buffer = self.pop(0)
        return buffer

    def replace(self, buffer):
        self.insert(0, buffer)

buffer_pool = BufferPool()

class Sound(object):

    def get_source(self):
        return Source(self)

class Source(object):
    def __init__(self):
        self.source = al.ALuint()
        al.alGenSources(1, self.source)
        self.play_when_buffered = False

    def play(self):
        buffers = al.ALint()
        al.alGetSourcei(self.source, al.AL_BUFFERS_QUEUED, buffers)
        print 'play, %d' % buffers.value
        if buffers.value == 0:
            self.play_when_buffered = True
        else:
            al.alSourcePlay(self.source)
            self.play_when_buffered = False

