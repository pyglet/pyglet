#!/usr/bin/python
# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2007 Alex Holkner
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
#  * Neither the name of the pyglet nor the names of its
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

'''Windows DirectSound audio implementation.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes
import time

from pyglet.media import AudioPlayer, Listener, MediaException

from pyglet.media.drivers.directsound import lib_dsound as lib
from pyglet.window.win32 import _user32

class DirectSoundException(MediaException):
    pass

class DirectSoundAudioPlayer(AudioPlayer):
    _buffer_size = 44800 * 1
    _update_buffer_size = _buffer_size // 4
    _buffer_size_secs = None
    
    def __init__(self, audio_format):
        super(DirectSoundAudioPlayer, self).__init__(audio_format)

        self._playing = False
        self._timestamp = 0.

        self._buffer = None
        self._buffer_playing = False
        self._play_cursor = 0
        self._buffer_time = 0.  # ts of buffer at buffer_time_pos
        self._buffer_time_pos = 0
        self._write_cursor = 0
        self._timestamps = []
        self._eos_count = 0
        self._dirty_size = 0

        wfx = lib.WAVEFORMATEX()
        wfx.wFormatTag = lib.WAVE_FORMAT_PCM
        wfx.nChannels = audio_format.channels
        wfx.nSamplesPerSec = audio_format.sample_rate
        wfx.wBitsPerSample = audio_format.sample_size
        wfx.nBlockAlign = wfx.wBitsPerSample * wfx.nChannels // 8
        wfx.nAvgBytesPerSec = wfx.nSamplesPerSec * wfx.nBlockAlign

        dsbdesc = lib.DSBUFFERDESC()
        dsbdesc.dwSize = ctypes.sizeof(dsbdesc)
        dsbdesc.dwFlags = (lib.DSBCAPS_GLOBALFOCUS | 
                           lib.DSBCAPS_GETCURRENTPOSITION2 |
                           lib.DSBCAPS_CTRLVOLUME)
        if audio_format.channels == 1:
            dsbdesc.dwFlags |= lib.DSBCAPS_CTRL3D
        dsbdesc.dwBufferBytes = self._buffer_size
        dsbdesc.lpwfxFormat = ctypes.pointer(wfx)

        dsb = lib.IDirectSoundBuffer()
        dsound.CreateSoundBuffer(dsbdesc, ctypes.byref(dsb), None)
        self._buffer = dsb
        self._buffer_size_secs = \
            self._buffer_size / float(audio_format.bytes_per_second)
            
    def __del__(self):
        try:
            self._buffer.Release()
        except (NameError, AttributeError):
            pass

    def get_write_size(self):
        if not self._playing:
            return 0

        play_cursor = lib.DWORD()
        self._buffer.GetCurrentPosition(play_cursor, None)
        play_cursor = play_cursor.value
        if self._write_cursor == play_cursor and self._buffer_playing:
            return 0
        elif self._write_cursor < play_cursor:
            write_size = play_cursor - self._write_cursor
        else:
            write_size = self._buffer_size - self._write_cursor + play_cursor

        if write_size < self._update_buffer_size:
            return 0

        return write_size
 
    def write(self, audio_data, length=None):
        # Pass audio_data=None, length>0 to write silence

        if length is None:
            write_size = self.get_write_size()
            length = min(audio_data.length, write_size)
        if length == 0:
            return 0
        
        p1 = ctypes.c_void_p()
        l1 = lib.DWORD()
        p2 = ctypes.c_void_p()
        l2 = lib.DWORD()
        self._buffer.Lock(self._write_cursor, length, 
            ctypes.byref(p1), l1, ctypes.byref(p2), l2, 0)
        assert length == l1.value + l2.value

        if audio_data:
            if self._write_cursor > self._play_cursor:
                wc = self._write_cursor
            else:
                wc = self._write_cursor + self._buffer_size
            self._timestamps.append((wc, audio_data.timestamp))
            
            ctypes.memmove(p1, audio_data.data, l1.value)
            audio_data.consume(l1.value, self.audio_format)
            if l2.value:
                ctypes.memmove(p2, audio_data.data, l2.value)
                audio_data.consume(l2.value, self.audio_format)
        else:
            ctypes.memset(p1, 0, l1.value)
            if l2.value:
                ctypes.memset(p2, 0, l2.value)
                pass
        self._buffer.Unlock(p1, l1, p2, l2)

        self._write_cursor += length
        self._write_cursor %= self._buffer_size

    def write_eos(self):
        if self._write_cursor > self._play_cursor:
            wc = self._write_cursor
        else:
            wc = self._write_cursor + self._buffer_size
        self._timestamps.append((wc, 'eos'))

    def write_end(self):
        if not self._dirty_size:
            self._dirty_size = self._buffer_size

    def pump(self):
        # Update play cursor, check for wraparound and EOS markers
        play_cursor = lib.DWORD()
        self._buffer.GetCurrentPosition(play_cursor, None)
        if play_cursor.value < self._play_cursor:
            # Wrapped around
            self._buffer_time_pos -= self._buffer_size
            self._timestamps = \
                [(a - self._buffer_size, t) for a, t in self._timestamps]
        self._play_cursor = play_cursor.value

        try:
            while self._timestamps[0][0] < self._play_cursor:
                pos, timestamp = self._timestamps.pop(0)
                if timestamp == 'eos':
                    self._eos_count += 1
                else:
                    self._buffer_time = timestamp
                    self._buffer_time_pos = pos
        except IndexError:
            pass

        self._timestamp = self._buffer_time + \
            (self._play_cursor - self._buffer_time_pos) \
                / float(self.audio_format.bytes_per_second)

        # Write silence
        if self._dirty_size:
            write_size = self.get_write_size()
            length = min(write_size, self._dirty_size)
            self.write(None, length)
            self._dirty_size -= length
            if self._dirty_size < 0:
                self._dirty_size = 0

        if self._playing and not self._buffer_playing:
            self._buffer.Play(0, 0, lib.DSBPLAY_LOOPING)
            self._buffer_playing = True

    def get_time(self):
        return self._timestamp

    def play(self):
        if self._playing:
            return

        self._playing = True

        self._buffer.Play(0, 0, lib.DSBPLAY_LOOPING)
        self._buffer_playing = True

    def stop(self):
        if not self._playing:
            return
            
        self._playing = False

        self._buffer.Stop()
        self._buffer_playing = False

    def clear(self):
        self._eos_count = 0
        self._timestamps = []
        self._write_cursor = 0
        self._buffer.SetCurrentPosition(0)
        self._buffer_time = 0.
        self._buffer_time_pos = 0

    def clear_eos(self):
        if self._eos_count > 0:
            self._eos_count -= 1
            return True
        return False

    def _get_source(self):
        if self._sources:
            return self._sources[0]
        return None

class DirectSoundListener(Listener):
    def _set_volume(self, volume):
        self._volume = volume

    def _set_position(self, position):
        self._position = position

    def _set_velocity(self, velocity):
        self._velocity = velocity

    def _set_forward_orientation(self, orientation):
        self._forward_orientation = orientation

    def _set_up_orientation(self, orientation):
        self._up_orientation = orientation

    def _set_doppler_factor(self, factor):
        self._doppler_factor = factor

    def _set_speed_of_sound(self, speed_of_sound):
        self._speed_of_sound = speed_of_sound

dsound = None
def driver_init():
    global dsound
    dsound = lib.IDirectSound()
    lib.DirectSoundCreate(None, ctypes.byref(dsound), None)

    # A trick used by mplayer.. use desktop as window handle since it would
    # be complex to use pyglet window handles (and what to do when application
    # is audio only?).
    hwnd = _user32.GetDesktopWindow()
    dsound.SetCooperativeLevel(hwnd, lib.DSSCL_NORMAL)

driver_listener = DirectSoundListener()
driver_audio_player_class = DirectSoundAudioPlayer
