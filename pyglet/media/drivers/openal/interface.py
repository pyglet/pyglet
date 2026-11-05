from __future__ import annotations

import ctypes
import weakref
from collections import namedtuple
from typing import TYPE_CHECKING, NoReturn

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from ctypes import _Pointer

    from pyglet.media.codecs.base import AudioData, AudioFormat

from . import lib_openal as al
from . import lib_alc as alc

from pyglet.util import debug_print
from pyglet.media.exceptions import MediaException

_debug = debug_print('debug_media')


SAMPLE_FORMATS: dict[str, tuple[bytes | None, dict[int, int]]] = {
	"U8":  (None, {1: al.AL_FORMAT_MONO8, 2: al.AL_FORMAT_STEREO8}),
	"S16": (None, {1: al.AL_FORMAT_MONO16, 2: al.AL_FORMAT_STEREO16}),
	"S32": (b"AL_EXT_32bit_formats",
            {1: al.alGetEnumValue(b"AL_FORMAT_MONO_I32"),
             2: al.alGetEnumValue(b"AL_FORMAT_STEREO_I32")}),
	"F32": (b"AL_EXT_float32",
            {1: al.alGetEnumValue(b"AL_FORMAT_MONO_FLOAT32"),
             2: al.alGetEnumValue(b"AL_FORMAT_STEREO_FLOAT32")}),
}

al.alGetError()  # Clear error from possibly unknown enum values


class OpenALException(MediaException):
    message: str | None
    error_code: int | None
    error_string: str | None

    def __init__(self, message: str | None = None, error_code: int | None = None,
                 error_string: str | None = None) -> None:
        self.message = message
        self.error_code = error_code
        self.error_string = error_string

    def __str__(self) -> str:
        if self.error_code is None:
            return f'OpenAL Exception: {self.message}'
        else:
            return f'OpenAL Exception [{self.error_code}: {self.error_string}]: {self.message}'


class OpenALObject:
    """Base class for OpenAL objects."""
    @classmethod
    def _check_error(cls, message: str | None = None) -> None:
        """Check whether there is an OpenAL error and raise exception if present."""
        error_code = al.alGetError()
        if error_code != 0:
            error_string = al.alGetString(error_code)
            # TODO: Fix return type in generated code?
            error_string = ctypes.cast(error_string, ctypes.c_char_p)
            raise OpenALException(message=message,
                                  error_code=error_code,
                                  error_string=str(error_string.value))


class OpenALDevice(OpenALObject):
    """OpenAL audio device."""
    _al_device: _Pointer[alc.ALCdevice] | None
    buffer_pool: OpenALBufferPool

    def __init__(self, device_name: bytes | None = None) -> None:
        self._al_device = alc.alcOpenDevice(device_name)
        self.check_context_error('Failed to open device.')
        if self._al_device is None:
            raise OpenALException('No OpenAL devices.')

        self.buffer_pool = OpenALBufferPool()

    def close(self) -> None:
        """Close this ALDevice. No more buffers or contexts may exist on it."""
        assert _debug("Closing interface.OpenALDevice")
        if alc.alcCloseDevice(self._al_device) == alc.ALC_FALSE:
            self._raise_context_error('Failed to close device.')
        self._al_device = None

    @property
    def is_ready(self) -> bool:
        return self._al_device is not None

    def create_context(self) -> OpenALContext:
        al_context = alc.alcCreateContext(self._al_device, None)
        self.check_context_error('Failed to create context')
        return OpenALContext(self, al_context)

    def get_version(self) -> tuple[int, int]:
        major = alc.ALCint()
        minor = alc.ALCint()
        alc.alcGetIntegerv(self._al_device, alc.ALC_MAJOR_VERSION,
                           ctypes.sizeof(major), major)
        self.check_context_error('Failed to get version.')
        alc.alcGetIntegerv(self._al_device, alc.ALC_MINOR_VERSION,
                           ctypes.sizeof(minor), minor)
        self.check_context_error('Failed to get version.')
        return major.value, minor.value

    def get_extensions(self) -> list[str]:
        extensions = alc.alcGetString(self._al_device, alc.ALC_EXTENSIONS)
        self.check_context_error('Failed to get extensions.')
        return ctypes.cast(extensions, ctypes.c_char_p).value.decode('ascii').split()

    def check_context_error(self, message: str | None = None) -> None:
        """Check whether there is an OpenAL error and raise exception if present."""
        error_code = alc.alcGetError(self._al_device)
        if error_code != 0:
            error_string = alc.alcGetString(self._al_device, error_code)
            # TODO: Fix return type in generated code?
            error_string = ctypes.cast(error_string, ctypes.c_char_p)
            raise OpenALException(message=message,
                                  error_code=error_code,
                                  error_string=str(error_string.value))

    def _raise_context_error(self, message: str) -> NoReturn:
        """Try to check for OpenAL error and raise that, and then
        definitely raise an error with the given message.
        """
        self.check_context_error(message)
        raise OpenALException(message)


class OpenALContext(OpenALObject):
    device: OpenALDevice
    _al_context: _Pointer[alc.ALCcontext] | None
    _sources: set[OpenALSource]
    _supported_formats: list[str]

    def __init__(self, device: OpenALDevice, al_context: _Pointer[alc.ALCcontext]) -> None:
        self.device = device
        self._al_context = al_context
        self._sources = set()
        self.make_current()

        self._supported_formats = []
        for fmt, (required_extension, _) in SAMPLE_FORMATS.items():
            if (required_extension is None
                    or al.alIsExtensionPresent(required_extension)):
                self._supported_formats.append(fmt)

    def delete_sources(self) -> None:
        for s in tuple(self._sources):
            s.delete()

    def delete(self) -> None:
        assert _debug("Delete interface.OpenALContext")

        if (
            ctypes.cast(alc.alcGetCurrentContext(), ctypes.c_void_p).value ==
            ctypes.cast(self._al_context, ctypes.c_void_p).value  # type: ignore[arg-type]
        ):
            alc.alcMakeContextCurrent(None)
            self.device.check_context_error('Failed to make context no longer current.')

        alc.alcDestroyContext(self._al_context)
        self.device.check_context_error('Failed to destroy context.')
        self._al_context = None

    def make_current(self) -> None:
        alc.alcMakeContextCurrent(self._al_context)
        self.device.check_context_error('Failed to make context current.')

    def create_source(self) -> OpenALSource:
        self.make_current()
        new_source = OpenALSource(self)
        self._sources.add(new_source)
        return new_source

    def source_deleted(self, source: OpenALSource) -> None:
        self._sources.remove(source)


class OpenALSource(OpenALObject):
    context: OpenALContext | None
    _al_source: ctypes.c_uint | None
    buffer_pool: OpenALBufferPool | None
    _state: int | None
    _owned_buffers: dict[int, OpenALBuffer]

    def __init__(self, context: OpenALContext) -> None:
        self.context = context

        self._al_source = al.ALuint()
        al.alGenSources(1, self._al_source)
        self._check_error('Failed to create source.')

        self.buffer_pool = context.device.buffer_pool

        self._state = None
        self._get_state()

        self._owned_buffers = {}

    def delete(self) -> None:
        if self.context is None:
            assert _debug("Delete interface.OpenAlSource on deleted source, ignoring")
            return

        assert _debug("Delete interface.OpenALSource")
        al.alDeleteSources(1, self._al_source)
        self._check_error('Failed to delete source.')
        self.context.source_deleted(self)

        self.buffer_pool = None  # Reference breakup
        self.context = None
        self._al_source = None

    @property
    def is_initial(self) -> bool:
        self._get_state()
        return self._state == al.AL_INITIAL

    @property
    def is_playing(self) -> bool:
        self._get_state()
        return self._state == al.AL_PLAYING

    @property
    def is_paused(self) -> bool:
        self._get_state()
        return self._state == al.AL_PAUSED

    @property
    def is_stopped(self) -> bool:
        self._get_state()
        return self._state == al.AL_STOPPED

    @staticmethod
    def _int_source_property(attribute: int) -> property:
        return property(lambda self: self._get_int(attribute),
                        lambda self, value: self._set_int(attribute, value))

    @staticmethod
    def _float_source_property(attribute: int) -> property:
        return property(lambda self: self._get_float(attribute),
                        lambda self, value: self._set_float(attribute, value))

    @staticmethod
    def _3floats_source_property(attribute: int) -> property:
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
    cone_inner_angle = _float_source_property(al.AL_CONE_INNER_ANGLE)
    cone_outer_angle = _float_source_property(al.AL_CONE_OUTER_ANGLE)
    cone_outer_gain = _float_source_property(al.AL_CONE_OUTER_GAIN)
    sec_offset = _float_source_property(al.AL_SEC_OFFSET)
    sample_offset = _int_source_property(al.AL_SAMPLE_OFFSET)
    byte_offset = _int_source_property(al.AL_BYTE_OFFSET)

    del _int_source_property
    del _float_source_property
    del _3floats_source_property

    def play(self) -> None:
        al.alSourcePlay(self._al_source)
        self._check_error('Failed to play source.')

    def pause(self) -> None:
        al.alSourcePause(self._al_source)
        self._check_error('Failed to pause source.')

    def stop(self) -> None:
        al.alSourceStop(self._al_source)
        self._check_error('Failed to stop source.')

    def clear(self) -> None:
        self._set_int(al.AL_BUFFER, al.AL_NONE)
        self.buffer_pool.return_buffers(self._owned_buffers.values())
        self._owned_buffers.clear()

    def get_buffer(self) -> OpenALBuffer:
        return self.buffer_pool.get_buffer()

    def queue_buffer(self, buf: OpenALBuffer) -> None:
        assert buf.is_valid
        al.alSourceQueueBuffers(self._al_source, 1, ctypes.byref(buf.al_name))  # type: ignore[arg-type]
        self._check_error('Failed to queue buffer.')
        self._owned_buffers[buf.name] = buf

    def unqueue_buffers(self) -> int:
        processed = self.buffers_processed
        assert _debug("Processed buffer count: {}".format(processed))
        if processed > 0:
            buffers = (al.ALuint * processed)()
            al.alSourceUnqueueBuffers(self._al_source, len(buffers), buffers)
            self._check_error('Failed to unqueue buffers from source.')
            self.buffer_pool.return_buffers([self._owned_buffers.pop(bn) for bn in buffers])
        return processed

    def _get_state(self) -> None:
        if self._al_source is not None:
            self._state = self._get_int(al.AL_SOURCE_STATE)

    def _get_int(self, key: int) -> int:
        assert self._al_source is not None
        al_int = al.ALint()
        al.alGetSourcei(self._al_source, key, al_int)
        self._check_error('Failed to get value')
        return al_int.value

    def _set_int(self, key: int, value: int) -> None:
        assert self._al_source is not None
        al.alSourcei(self._al_source, key, int(value))
        self._check_error('Failed to set value.')

    def _get_float(self, key: int) -> float:
        assert self._al_source is not None
        al_float = al.ALfloat()
        al.alGetSourcef(self._al_source, key, al_float)
        self._check_error('Failed to get value')
        return al_float.value

    def _set_float(self, key: int, value: float) -> None:
        assert self._al_source is not None
        al.alSourcef(self._al_source, key, float(value))
        self._check_error('Failed to set value.')

    def _get_3floats(self, key: int) -> tuple[float, float, float]:
        assert self._al_source is not None
        x = al.ALfloat()
        y = al.ALfloat()
        z = al.ALfloat()
        al.alGetSource3f(self._al_source, key, x, y, z)
        self._check_error('Failed to get value')
        return x.value, y.value, z.value

    def _set_3floats(self, key: int, values: Iterable[float]) -> None:
        assert self._al_source is not None
        x, y, z = map(float, values)
        al.alSource3f(self._al_source, key, x, y, z)
        self._check_error('Failed to set value.')


OpenALOrientation = namedtuple("OpenALOrientation", ['at', 'up'])


class OpenALListener(OpenALObject):
    @property
    def position(self) -> tuple[float, float, float]:
        return self._get_3floats(al.AL_POSITION)

    @position.setter
    def position(self, values: Iterable[float]) -> None:
        self._set_3floats(al.AL_POSITION, values)

    @property
    def velocity(self) -> tuple[float, float, float]:
        return self._get_3floats(al.AL_VELOCITY)

    @velocity.setter
    def velocity(self, values: Iterable[float]) -> None:
        self._set_3floats(al.AL_VELOCITY, values)

    @property
    def gain(self) -> float:
        return self._get_float(al.AL_GAIN)

    @gain.setter
    def gain(self, value: float) -> None:
        self._set_float(al.AL_GAIN, value)

    @property
    def orientation(self) -> OpenALOrientation:
        values = self._get_float_vector(al.AL_ORIENTATION, 6)
        return OpenALOrientation(values[0:3], values[3:6])

    @orientation.setter
    def orientation(self, values: Sequence[float] | Sequence[Sequence[float]]) -> None:
        actual_values: Sequence[float]
        if len(values) == 2:
            actual_values = values[0] + values[1]  # type: ignore[operator, assignment]
        elif len(values) == 6:
            actual_values = values  # type: ignore[assignment]
        else:
            actual_values = []
        if len(actual_values) != 6:
            raise ValueError("Need 2 tuples of 3 or 1 tuple of 6.")
        self._set_float_vector(al.AL_ORIENTATION, actual_values)

    def _get_float(self, key: int) -> float:
        al_float = al.ALfloat()
        al.alGetListenerf(key, al_float)
        self._check_error('Failed to get value')
        return al_float.value

    def _set_float(self, key: int, value: float) -> None:
        al.alListenerf(key, float(value))
        self._check_error('Failed to set value.')

    def _get_3floats(self, key: int) -> tuple[float, float, float]:
        x = al.ALfloat()
        y = al.ALfloat()
        z = al.ALfloat()
        al.alGetListener3f(key, x, y, z)
        self._check_error('Failed to get value')
        return x.value, y.value, z.value

    def _set_3floats(self, key: int, values: Iterable[float]) -> None:
        x, y, z = map(float, values)
        al.alListener3f(key, x, y, z)
        self._check_error('Failed to set value.')

    def _get_float_vector(self, key: int, count: int) -> list[float]:
        al_float_vector = (al.ALfloat * count)()
        al.alGetListenerfv(key, al_float_vector)
        self._check_error('Failed to get value')
        return [x for x in al_float_vector]

    def _set_float_vector(self, key: int, values: Sequence[float]) -> None:
        al_float_vector = (al.ALfloat * len(values))(*values)
        al.alListenerfv(key, al_float_vector)
        self._check_error('Failed to set value.')


class OpenALBuffer(OpenALObject):
    al_name: ctypes.c_uint | None
    name: int

    def __init__(self, al_name: ctypes.c_uint) -> None:
        self.al_name = al_name
        self.name = al_name.value

        assert self.is_valid

    @property
    def is_valid(self) -> bool:
        self._check_error('Before validate buffer.')
        if self.al_name is None:
            return False
        valid = bool(al.alIsBuffer(self.al_name))
        if not valid:
            # Clear possible error due to invalid buffer
            al.alGetError()
        return valid

    def delete(self) -> None:
        if self.al_name is not None and self.is_valid:
            al.alDeleteBuffers(1, ctypes.byref(self.al_name))
            self._check_error('Error deleting buffer.')
            self.al_name = None

    def data(self, audio_data: AudioData, audio_format: AudioFormat,
             supported_formats: Sequence[str]) -> None:
        assert self.is_valid

        try:
            sample_format = audio_format.sample_format
            channels = audio_format.channels
            assert sample_format in SAMPLE_FORMATS
            assert sample_format in supported_formats
            al_format = SAMPLE_FORMATS[sample_format][1][channels]
        except AssertionError:
            raise MediaException(
                f"OpenAL does not support '{audio_format.channels}-channel, "
                f"{audio_format.sample_size}-bit "
                f"{audio_format.sample_type}' audio.")

        al.alBufferData(self.al_name,
                        al_format,
                        audio_data.pointer,
                        audio_data.length,
                        audio_format.sample_rate)
        self._check_error('Failed to add data to buffer.')


class OpenALBufferPool(OpenALObject):
    """At least Mac OS X doesn't free buffers when a source is deleted; it just
    detaches them from the source.  So keep our own recycled queue.
    """
    _buffers: list[OpenALBuffer]

    def __init__(self) -> None:
        self._buffers = []
        """List of free buffer names"""

    def __len__(self) -> int:
        return len(self._buffers)

    def delete(self) -> None:
        assert _debug("Delete interface.OpenALBufferPool")
        while self._buffers:
            self._buffers.pop().delete()

    def get_buffer(self) -> OpenALBuffer:
        """Convenience for returning one buffer name"""
        return self.get_buffers(1)[0]

    def get_buffers(self, number: int) -> list[OpenALBuffer]:
        """Returns an array containing `number` buffer names.  The returned list must
        not be modified in any way, and may get changed by subsequent calls to
        get_buffers.
        """
        ret_buffers: list[OpenALBuffer] = []
        while self._buffers and len(ret_buffers) < number:
            b = self._buffers.pop()
            if b.is_valid:
                ret_buffers.append(b)
            # Otherwise the buffer doesn't exist on the OpenAL side
            # anymore, forget about it

        # If we didn't get enough, create more buffers
        if (missing := number - len(ret_buffers)) > 0:
            names = (al.ALuint * missing)()
            al.alGenBuffers(missing, names)
            self._check_error('Error generating buffers.')
            ret_buffers.extend(OpenALBuffer(al.ALuint(name)) for name in names)

        return ret_buffers

    def return_buffers(self, buffers: Iterable[OpenALBuffer]) -> None:
        """Throw buffers not used anymore back into the pool."""
        for buf in buffers:
            if buf.is_valid:
                self._buffers.append(buf)
