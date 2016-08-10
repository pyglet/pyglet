"""
Pythonic interface to DirectSound.
"""
from collections import namedtuple
import ctypes
import math

from pyglet.window.win32 import _user32

from . import lib_dsound as lib


def _db(gain):
    """
    Convert linear gain in range [0.0, 1.0] to 100ths of dB.

    Power gain = P1/P2
    dB = 10 log(P1/P2)
    dB * 100 = 1000 * log(power gain)
    """
    if gain <= 0:
        return -10000
    return max(-10000, min(int(1000 * math.log10(min(gain, 1))), 0))


def _gain(db):
    """Convert 100ths of dB to linear gain."""
    return math.pow(10.0, float(db)/1000.0)


class DirectSoundNativeError(Exception):
    def __init__(self, hresult):
        self.hresult = hresult

    def __repr__(self):
        return "{}: Error {}".format(self.__class__.__name__, self.hresult)


def _check(hresult):
    if hresult != lib.DS_OK:
        raise DirectSoundNativeError(hresult)


class DirectSoundDriver(object):
    def __init__(self):
        self._native_dsound = lib.IDirectSound()
        _check(
            lib.DirectSoundCreate(None, ctypes.byref(self._native_dsound), None)
        )

        # A trick used by mplayer.. use desktop as window handle since it
        # would be complex to use pyglet window handles (and what to do when
        # application is audio only?).
        hwnd = _user32.GetDesktopWindow()
        _check(
            self._native_dsound.SetCooperativeLevel(hwnd, lib.DSSCL_NORMAL)
        )

        self._buffer_factory = DirectSoundBufferFactory(self, self._native_dsound)
        self._primary_buffer = self._buffer_factory.create_primary_buffer()

    def __del__(self):
        del self._primary_buffer
        self._native_dsound.Release()

    def create_buffer(self, audio_format):
        return self._buffer_factory.create_buffer(audio_format)

    def create_listener(self):
        return self._primary_buffer.create_listener()


class DirectSoundBufferFactory(object):
    default_buffer_size = 44100 * 1

    def __init__(self, driver, native_dsound):
        self.driver = driver
        self._native_dsound = native_dsound

    def create_buffer(self, audio_format):
        return DirectSoundBuffer(
                self.driver,
                self._create_buffer(self._create_buffer_desc(audio_format)),
                audio_format,
                self.default_buffer_size)

    def create_primary_buffer(self):
        return DirectSoundBuffer(
                self,
                self._create_buffer(self._create_primary_buffer_desc()),
                None,
                0)

    def _create_buffer(self, buffer_desc):
        buf = lib.IDirectSoundBuffer()
        _check(
            self._native_dsound.CreateSoundBuffer(buffer_desc, ctypes.byref(buf), None)
        )
        return buf

    @staticmethod
    def _create_wave_format(audio_format):
        wfx = lib.WAVEFORMATEX()
        wfx.wFormatTag = lib.WAVE_FORMAT_PCM
        wfx.nChannels = audio_format.channels
        wfx.nSamplesPerSec = audio_format.sample_rate
        wfx.wBitsPerSample = audio_format.sample_size
        wfx.nBlockAlign = wfx.wBitsPerSample * wfx.nChannels // 8
        wfx.nAvgBytesPerSec = wfx.nSamplesPerSec * wfx.nBlockAlign
        return wfx

    @classmethod
    def _create_buffer_desc(cls, audio_format, buffer_size=None):
        buffer_size = buffer_size or cls.default_buffer_size

        wfx = cls._create_wave_format(audio_format)

        dsbdesc = lib.DSBUFFERDESC()
        dsbdesc.dwSize = ctypes.sizeof(dsbdesc)
        dsbdesc.dwFlags = (lib.DSBCAPS_GLOBALFOCUS |
                           lib.DSBCAPS_GETCURRENTPOSITION2 |
                           lib.DSBCAPS_CTRLFREQUENCY |
                           lib.DSBCAPS_CTRLVOLUME)
        if audio_format.channels == 1:
            dsbdesc.dwFlags |= lib.DSBCAPS_CTRL3D
        dsbdesc.dwBufferBytes = buffer_size
        dsbdesc.lpwfxFormat = ctypes.pointer(wfx)

        return dsbdesc

    @classmethod
    def _create_primary_buffer_desc(cls):
        """Primary buffer with 3D and volume capabilities"""
        buffer_desc = lib.DSBUFFERDESC()
        buffer_desc.dwSize = ctypes.sizeof(buffer_desc)
        buffer_desc.dwFlags = (lib.DSBCAPS_CTRL3D |
                               lib.DSBCAPS_CTRLVOLUME |
                               lib.DSBCAPS_PRIMARYBUFFER)

        return buffer_desc

class DirectSoundBuffer(object):
    def __init__(self, driver, native_buffer, audio_format, buffer_size):
        self.driver = driver
        self.audio_format = audio_format
        self.buffer_size = buffer_size

        self._native_buffer = native_buffer

        if audio_format is not None and audio_format.channels == 1:
            self._native_buffer3d = lib.IDirectSound3DBuffer()
            self._native_buffer.QueryInterface(lib.IID_IDirectSound3DBuffer,
                                               ctypes.byref(self._native_buffer3d))
        else:
            self._native_buffer3d = None

        # TODO Only for normal buffers: self._native_buffer.SetCurrentPosition(0)

    def __del__(self):
        if self._native_buffer is not None:
            self._native_buffer.Stop()
            self._native_buffer.Release()
            self._native_buffer = None
            if self._native_buffer3d is not None:
                self._native_buffer3d.Release()
                self._native_buffer3d = None

    @property
    def volume(self):
        vol = lib.LONG()
        _check(
            self._native_buffer.GetVolume(ctypes.byref(vol))
        )
        return _gain(vol.value)

    @volume.setter
    def volume(self, value):
        _check(
            self._native_buffer.SetVolume(_db(value))
        )

    @property
    def current_position(self):
        """Tuple of current play position and current write position."""
        # TODO NamedTuple
        play_cursor = lib.DWORD()
        write_cursor = lib.DWORD()
        _check(
            self._native_buffer.GetCurrentPosition(ctypes.byref(play_cursor),
                                                   ctypes.byref(write_cursor))
        )
        return play_cursor.value, write_cursor.value

    @current_position.setter
    def current_position(self, value):
        _check(
            self._native_buffer.SetCurrentPosition(value)
        )

    @property
    def is3d(self):
        return self._native_buffer3d is not None

    @property
    def position(self):
        if self.is3d:
            position = lib.D3DVECTOR()
            _check(
                self._native_buffer3d.GetPosition(ctypes.byref(position))
            )
            return position.x, position.y, position.z
        else:
            return 0, 0, 0

    @position.setter
    def position(self, position):
        if self.is3d:
            x, y, z = position
            # TODO Correct in adaptation: x, y, -z
            _check(
                self._native_buffer3d.SetPosition(x, y, z, lib.DS3D_IMMEDIATE)
            )

    @property
    def min_distance(self):
        """The minimum distance, which is the distance from the
        listener at which sounds in this buffer begin to be attenuated."""
        if self.is3d:
            value = lib.D3DVALUE()
            _check(
                self._native_buffer3d.GetMinDistance(ctypes.byref(value))
            )
            return value.value
        else:
            return 0

    @min_distance.setter
    def min_distance(self, value):
        if self.is3d:
            _check(
                self._native_buffer3d.SetMinDistance(value, lib.DS3D_IMMEDIATE)
            )

    @property
    def max_distance(self):
        """The maximum distance, which is the distance from the listener beyond which
        sounds in this buffer are no longer attenuated."""
        if self.is3d:
            value = lib.D3DVALUE()
            _check(
                self._native_buffer3d.GetMaxDistance(ctypes.byref(value))
            )
            return value.value
        else:
            return 0

    @max_distance.setter
    def max_distance(self, value):
        if self.is3d:
            _check(
                self._native_buffer3d.SetMaxDistance(value, lib.DS3D_IMMEDIATE)
            )

    @property
    def frequency(self):
        value = lib.DWORD()
        _check(
            self._native_buffer.GetFrequency(value)
        )
        return value.value

    @frequency.setter
    def frequency(self, value):
        """The frequency, in samples per second, at which the buffer is playing."""
        # TODO Translate from pitch (pitch * sample_rate = freq)
        _check(
            self._native_buffer.SetFrequency(value)
        )

    @property
    def cone_orientation(self):
        """The orientation of the sound projection cone."""
        if self.is3d:
            orientation = lib.D3DVECTOR()
            _check(
                self._native_buffer3d.GetConeOrientation(ctypes.byref(orientation))
            )
            return orientation.x, orientation.y, orientation.z
        else:
            return 0, 0, 0

    @cone_orientation.setter
    def cone_orientation(self, value):
        # TODO: Adaptation x, y, -z
        if self.is3d:
            x, y, z = value
            _check(
                self._native_buffer3d.SetConeOrientation(x, y, z, lib.DS3D_IMMEDIATE)
            )

    _ConeAngles = namedtuple('_ConeAngles', ['inside', 'outside'])
    @property
    def cone_angles(self):
        """The inside and outside angles of the sound projection cone."""
        if self.is3d:
            inside = lib.DWORD()
            outside = lib.DWORD()
            _check(
                self._native_buffer3d.GetConeAngles(ctypes.byref(inside), ctypes.byref(outside))
            )
            return self._ConeAngles(inside.value, outside.value)
        else:
            return self._ConeAngles(0, 0)

    def set_cone_angles(self, inside, outside):
        """The inside and outside angles of the sound projection cone."""
        if self.is3d:
            _check(
                self._native_buffer3d.SetConeAngles(inside, outside, lib.DS3D_IMMEDIATE)
            )

    @property
    def cone_outside_volume(self):
        """The volume of the sound outside the outside angle of the sound projection cone."""
        if self.is3d:
            volume = lib.LONG()
            _check(
                self._native_buffer3d.GetConeOutsideVolume(ctypes.byref(volume))
            )
            return volume.value
        else:
            return 0

    @cone_outside_volume.setter
    def cone_outside_volume(self, value):
        if self.is3d:
            _check(
                self._native_buffer3d.SetConeOutsideVolume(value, lib.DS3D_IMMEDIATE)
            )

    def create_listener(self):
        listener = lib.IDirectSound3DListener()
        self._native_buffer.QueryInterface(lib.IID_IDirectSound3DListener,
                                           ctypes.byref(listener))
        return DirectSoundListener(self, listener)

    def play(self):
        _check(
            self._native_buffer.Play(0, 0, lib.DSBPLAY_LOOPING)
        )

    def stop(self):
        _check(
            self._native_buffer.Stop()
        )

    class _WritePointer(object):
        def __init__(self):
            self.audio_ptr_1 = ctypes.c_void_p()
            self.audio_length_1 = lib.DWORD()
            self.audio_ptr_2 = ctypes.c_void_p()
            self.audio_length_2 = lib.DWORD()

    def lock(self, write_cursor, write_size):
        pointer = self._WritePointer()
        _check(
            self._native_buffer.Lock(write_cursor,
                                     write_size,
                                     ctypes.byref(pointer.audio_ptr_1),
                                     pointer.audio_length_1,
                                     ctypes.byref(pointer.audio_ptr_2),
                                     pointer.audio_length_2,
                                     0)
        )
        return pointer

    def unlock(self, pointer):
        _check(
            self._native_buffer.Unlock(pointer.audio_ptr_1,
                                       pointer.audio_length_1,
                                       pointer.audio_ptr_2,
                                       pointer.audio_length_2)
        )


class DirectSoundListener(object):
    def __init__(self, buf, listener):
        self.buffer = buf
        self._listener = listener

    def __del__(self):
        self._listener.Release()

    @property
    def position(self):
        vector = lib.D3DVECTOR()
        _check(
            self._listener.GetPosition(ctypes.byref(vector))
        )
        return (vector.x, vector.y, vector.z)

    @position.setter
    def position(self, value):
        # TODO do translation in adaptation (x, y, -z)
        _check(
            self._listener.SetPosition(*(list(value) + [lib.DS3D_IMMEDIATE]))
        )

    @property
    def orientation(self):
        front = lib.D3DVECTOR()
        top = lib.D3DVECTOR()
        _check(
            self._listener.GetOrientation(ctypes.byref(front), ctypes.byref(top))
        )
        return (front.x, front.y, front.z, top.x, top.y, top.z)

    @orientation.setter
    def orientation(self, orientation):
        # TODO do translation in adaptation (x, y, -z, ux, uy, -uz)
        _check(
            self._listener.SetOrientation(*(list(orientation) + [lib.DS3D_IMMEDIATE]))
        )


