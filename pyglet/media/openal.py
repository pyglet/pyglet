#!/usr/bin/python
# $Id$

import ctypes

from pyglet.media import Sound
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
            buffer = al.ALuint(self.pop(0))
        return buffer

    def replace(self, buffers):
        self.extend(buffers)

    def __del__(self, al=al):
        if al and al.ALuint and al.alDeleteBuffers:
            buffers = (al.ALuint * len(self))(*self)
            al.alDeleteBuffers(len(self), buffers)

buffer_pool = BufferPool()

class OpenALSound(Sound):
    _processed_buffers = 0
    _queued_buffers = 0

    def __init__(self):
        self.source = al.ALuint()
        al.alGenSources(1, self.source)
        self.play_when_buffered = False

    def __del__(self, al=al):
        if al and al.alDeleteSources:
            al.alDeleteSources(1, self.source)

    def play(self):
        self._openal_play()

    def _openal_play(self):
        buffers = al.ALint()
        al.alGetSourcei(self.source, al.AL_BUFFERS_QUEUED, buffers)
        if buffers.value == 0:
            self.play_when_buffered = True
        else:
            al.alSourcePlay(self.source)
            self.play_when_buffered = False

    def dispatch_events(self):
        queued = al.ALint()
        processed = al.ALint()
        al.alGetSourcei(self.source, al.AL_BUFFERS_QUEUED, queued)
        al.alGetSourcei(self.source, al.AL_BUFFERS_PROCESSED, processed)
        if processed.value == queued.value:
            self.finished = True
        self._processed_buffers = processed.value
        self._queued_buffers = queued.value

        if self.play_when_buffered and queued.value:
            self._openal_play()

class OpenALStreamingSound(OpenALSound):
    def dispatch_events(self):
        super(OpenALStreamingSound, self).dispatch_events()

        # Release spent buffers
        if self._processed_buffers:
            discard_buffers = (al.ALuint * self._processed_buffers)()
            al.alSourceUnqueueBuffers(
                self.source, len(discard_buffers), discard_buffers)
            buffer_pool.replace(discard_buffers)

class OpenALStaticSound(OpenALSound):
    def __init__(self, medium):
        super(OpenALStaticSound, self).__init__()

        # Keep a reference to the medium to avoid premature release of
        # buffers.
        self.medium = medium

_format_map = {
    (1,  8): al.AL_FORMAT_MONO8,
    (1, 16): al.AL_FORMAT_MONO16,
    (2,  8): al.AL_FORMAT_STEREO8,
    (2, 16): al.AL_FORMAT_STEREO16,
}
def get_format(channels, depth):
    return _format_map[channels, depth]

