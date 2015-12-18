# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------
# $Id$
from __future__ import print_function
from __future__ import absolute_import
from builtins import str

import ctypes
from collections import defaultdict

from . import lib_openal as al
from . import lib_alc as alc
from pyglet.media.exceptions import MediaException

import pyglet
_debug = pyglet.options['debug_media']
_debug_buffers = pyglet.options.get('debug_media_buffers', False)


class OpenALException(MediaException):
    def __init__(self, message=None, error_code=None, error_string=None):
        self.message = message
        self.error_code = error_code
        self.error_string = error_string

    def __str__(self):
        if self.error_code is None:
            return 'OpenAL Exception: {}'.format(self.message)
        else:
            return 'OpenAL Exception [{}: {}]: {}'.format(self.error_code,
                                                          self.error_string,
                                                          self.message)

# TODO move functions into context/driver?

def _split_nul_strings(s):
    # NUL-separated list of strings, double-NUL-terminated.
    nul = False
    i = 0
    while True:
        if s[i] == '\0':
            if nul:
                break
            else:
                nul = True
        else:
            nul = False
        i += 1
    s = s[:i - 1]
    return filter(None, [str(ss.strip()) for ss in s.split('\0')])

format_map = {
    (1,  8): al.AL_FORMAT_MONO8,
    (1, 16): al.AL_FORMAT_MONO16,
    (2,  8): al.AL_FORMAT_STEREO8,
    (2, 16): al.AL_FORMAT_STEREO16,
}

class OpenALObject(object):
    """Base class for OpenAL objects."""
    @classmethod
    def _check_error(cls, message=None):
        """Check whether there is an OpenAL error and raise exception if present."""
        error_code = al.alGetError()
        if error_code != 0:
            error_string = al.alGetString(error_code)
            #TODO: Fix return type in generated code?
            error_string = ctypes.cast(error_string, ctypes.c_char_p)
            raise OpenALException(message=message,
                                  error_code=error_code,
                                  error_string=str(error_string.value))

    @classmethod
    def _raise_error(cls, message):
        """Raise an exception. Try to check for OpenAL error code too."""
        cls._check_error(message)
        raise OpenALException(message)


class OpenALDevice(OpenALObject):
    """OpenAL audio device."""
    def __init__(self, device_name=None):
        self._al_device = alc.alcOpenDevice(device_name)
        if self._al_device is None:
            raise OpenALException('No OpenAL devices.')

    def __del__(self):
        self.delete()

    def delete(self):
        if self._al_device is not None:
            alc.alcCloseDevice(self._al_device)
            self._al_device = None

    @property
    def is_ready(self):
        return self._al_device is not None

    def create_context(self):
        al_context = alc.alcCreateContext(self._al_device, None)
        return OpenALContext(self, al_context)

    def get_version(self):
        major = alc.ALCint()
        minor = alc.ALCint()
        alc.alcGetIntegerv(self._al_device, alc.ALC_MAJOR_VERSION,
                           ctypes.sizeof(major), major)
        alc.alcGetIntegerv(self._al_device, alc.ALC_MINOR_VERSION,
                           ctypes.sizeof(minor), minor)
        return major.value, minor.value

    def get_extensions(self):
        extensions = alc.alcGetString(self._al_device, alc.ALC_EXTENSIONS)
        if pyglet.compat_platform == 'darwin' or pyglet.compat_platform.startswith('linux'):
            return [str(x) for x in ctypes.cast(extensions, ctypes.c_char_p).value.split(b' ')]
        else:
            return _split_nul_strings(extensions)


class OpenALContext(OpenALObject):
    def __init__(self, device, al_context):
        self.device = device
        self._al_context = al_context
        self.make_current()
        self.buffer_pool = OpenALBufferPool()

    def __del__(self):
        self.delete()

    def delete(self):
        if self._al_context is not None:
            # TODO: Check if this context is current
            alc.alcMakeContextCurrent(None)
            alc.alcDestroyContext(self._al_context)
            self._al_context = None

    def make_current(self):
        alc.alcMakeContextCurrent(self._al_context)

    def create_source(self):
        self.make_current()
        return OpenALSource(self)


class OpenALSource(OpenALObject):
    def __init__(self, context):
        self.context = context

        self._al_source = al.ALuint()
        al.alGenSources(1, self._al_source)
        self._check_error('Failed to create source.')

        self._state = None
        self._get_state()

        self._owned_buffers = {}

    def __del__(self):
        self.delete()

    def delete(self):
        if self._al_source is not None:
            al.alDeleteSources(1, self._al_source)
            self._check_error('Failed to delete source.')
            # TODO: delete buffers in use
            self._al_source = None

    @property
    def is_initial(self):
        self._get_state()
        return self._state == al.AL_INITIAL

    @property
    def is_playing(self):
        self._get_state()
        return self._state == al.AL_PLAYING

    @property
    def is_paused(self):
        self._get_state()
        return self._state == al.AL_PAUSED

    @property
    def is_stopped(self):
        self._get_state()
        return self._state == al.AL_STOPPED

    def _int_source_property(attribute):
        return property(lambda self: self._get_int(attribute),
                        lambda self, value: self._set_int(attribute, value))

    def _float_source_property(attribute):
        return property(lambda self: self._get_float(attribute),
                        lambda self, value: self._set_float(attribute, value))

    def _3floats_source_property(attribute):
        return property(lambda self: self._get_3floats(attribute),
                        lambda self, value: self._set_3floats(attribute, value))

    position = _3floats_source_property(al.AL_POSITION)
    velocity = _3floats_source_property(al.AL_VELOCITY)
    gain = _float_source_property(al.AL_GAIN)
    buffers_queued = _int_source_property(al.AL_BUFFERS_QUEUED)
    buffers_processed = _int_source_property(al.AL_BUFFERS_PROCESSED)
    min_gain = _float_source_property(al.AL_MIN_GAIN)
    max_gain = _float_source_property(al.AL_MAX_GAIN)
    reference_distance = _float_source_property(al.AL_REFERENCE_DISTANCE)
    rolloff_factor = _float_source_property(al.AL_ROLLOFF_FACTOR)
    pitch = _float_source_property(al.AL_PITCH)
    max_distance = _float_source_property(al.AL_MAX_DISTANCE)
    direction = _3floats_source_property(al.AL_DIRECTION)
    cone_inner_angle =_float_source_property(al.AL_CONE_INNER_ANGLE)
    cone_outer_angle = _float_source_property(al.AL_CONE_OUTER_ANGLE)
    cone_outer_gain = _float_source_property(al.AL_CONE_OUTER_GAIN)
    sec_offset = _float_source_property(al.AL_SEC_OFFSET)
    sample_offset = _float_source_property(al.AL_SAMPLE_OFFSET)
    byte_offset = _float_source_property(al.AL_BYTE_OFFSET)

    del _int_source_property
    del _float_source_property
    del _3floats_source_property

    def play(self):
        al.alSourcePlay(self._al_source)
        self._check_error('Failed to play source.')

    def pause(self):
        al.alSourcePause(self._al_source)
        self._check_error('Failed to pause source.')

    def stop(self):
        al.alSourceStop(self._al_source)
        self._check_error('Failed to stop source.')

    def queue_buffer(self, buf):
        assert buf.is_valid
        al.alSourceQueueBuffers(self._al_source, 1, ctypes.byref(buf.al_buffer))
        self._check_error('Failed to queue buffer.')
        self._add_buffer(buf)

    def unqueue_buffers(self):
        processed = self.buffers_processed
        buffers = (al.ALuint * processed)()
        al.alSourceUnqueueBuffers(self._al_source, len(buffers), buffers)
        self._check_error('Failed to unqueue buffers from source.')
        for buf in buffers:
            self.context.buffer_pool.unqueue_buffer(self._pop_buffer(buf))

    def _get_state(self):
        if self._al_source is not None:
            self._state = self._get_int(al.AL_SOURCE_STATE)

    def _get_int(self, key):
        assert self._al_source is not None
        al_int = al.ALint()
        al.alGetSourcei(self._al_source, key, al_int)
        self._check_error('Failed to get value')
        return al_int.value

    def _set_int(self, key, value):
        assert self._al_source is not None
        al.alSourcei(self._al_source, key, int(value))
        self._check_error('Failed to set value.')

    def _get_float(self, key):
        assert self._al_source is not None
        al_float = al.ALfloat()
        al.alGetSourcef(self._al_source, key, al_float)
        self._check_error('Failed to get value')
        return al_float.value

    def _set_float(self, key, value):
        assert self._al_source is not None
        al.alSourcef(self._al_source, key, float(value))
        self._check_error('Failed to set value.')

    def _get_3floats(self, key):
        assert self._al_source is not None
        x = al.ALfloat()
        y = al.ALfloat()
        z = al.ALfloat()
        al.alGetSource3f(self._al_source, key, x, y, z)
        self._check_error('Failed to get value')
        return x.value, y.value, z.value

    def _set_3floats(self, key, values):
        assert self._al_source is not None
        x, y, z = map(float, values)
        al.alSource3f(self._al_source, key, x, y, z)
        self._check_error('Failed to set value.')

    def _add_buffer(self, buf):
        self._owned_buffers[buf.name] = buf

    def _pop_buffer(self, al_buffer):
        buf = self._owned_buffers.pop(al_buffer, None)
        assert buf is not None
        return buf


class OpenALBuffer(OpenALObject):
    @classmethod
    def create(cls):
        cls._check_error('Before allocating buffer.')
        al_buffer = al.ALuint()
        al.alGenBuffers(1, al_buffer)
        cls._check_error('Error allocating buffer.')
        return cls(al_buffer)

    def __init__(self, al_buffer):
        self._al_buffer = al_buffer
        assert self.is_valid

    def __del__(self):
        self.delete()

    @property
    def is_valid(self):
        self._check_error('Before validate buffer.')
        if self._al_buffer is None:
            return False
        valid = bool(al.alIsBuffer(self._al_buffer))
        if not valid:
            # Clear possible error due to invalid buffer
            al.alGetError()
        return valid

    @property
    def al_buffer(self):
        assert self.is_valid
        return self._al_buffer

    @property
    def name(self):
        assert self.is_valid
        return self._al_buffer.value

    def delete(self):
        if self.is_valid:
            al.alDeleteBuffers(1, ctypes.byref(self._al_buffer))
            self._check_error('Error deleting buffer.')
            self._al_buffer = None

    def data(self, audio_data, audio_format):
        assert self.is_valid
        al_format = format_map[(audio_format.channels, audio_format.sample_size)]
        al.alBufferData(self._al_buffer,
                        al_format,
                        audio_data.data,
                        audio_data.length,
                        audio_format.sample_rate)
        self._check_error('Failed to add data to buffer.')


class OpenALBufferPool(object):
    """At least Mac OS X doesn't free buffers when a source is deleted; it just
    detaches them from the source.  So keep our own recycled queue.
    """
    def __init__(self):
        self._buffers = [] # list of free buffer names

    def __del__(self):
        self.clear()

    def __len__(self):
        return len(self._buffers)

    def clear(self):
        while self._buffers:
            self._buffers.pop().delete()

    def get_buffer(self):
        """Convenience for returning one buffer name"""
        return self.get_buffers(1)[0]

    def get_buffers(self, number):
        """Returns an array containing `number` buffer names.  The returned list must
        not be modified in any way, and may get changed by subsequent calls to
        get_buffers.
        """
        buffers = []
        while number > 0:
            if self._buffers:
                b = self._buffers.pop()
            else:
                b = OpenALBuffer.create()
            if b.is_valid:
                # Protect against implementations that DO free buffers
                # when they delete a source - carry on.
                buffers.append(b)
                number -= 1

        return buffers

    def unqueue_buffer(self, buf):
        """A buffer has finished playing, free it."""
        if buf.is_valid:
            self._buffers.append(buf)

