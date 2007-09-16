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
# $Id:$

'''Windows DirectSound audio implementation.
'''

import ctypes
import time

from pyglet.media import BasePlayer, ManagedSoundPlayerMixIn, Listener
from pyglet.media import MediaException

from pyglet.media.drivers.directsound import lib_dsound as lib

class DirectSoundPlayer(BasePlayer):
    _buffer_size = 44800 * 8 # 1 sec of 16 bit 44.8 kHz stereo 
    _update_buffer_size = _buffer_size // 4
    
    def __init__(self):
        super(DirectSoundPlayer, self).__init__()

        self._sources = []
        self._playing = False
        self._timestamp = 0.
        self._timestamp_time = None

        self._buffer = None
        self._buffer_playing = False
        self._write_cursor = 0
        self._source_read_index = 0
        self._next_audio_data = None

    def _create_buffer(self, audio_format):
        if not audio_format:
            return

        wfx = lib.WAVEFORMATEX()
        wfx.wFormatTag = lib.WAVE_FORMAT_PCM
        wfx.nChannels = audio_format.channels
        wfx.nSamplesPerSec = audio_format.sample_rate
        wfx.wBitsPerSample = audio_format.sample_size
        wfx.nBlockAlign = wfx.wBitsPerSample * wfx.nChannels // 8
        wfx.nAvgBytesPerSec = wfx.nSamplesPerSec * wfx.nBlockAlign

        dsbdesc = lib.DSBUFFERDESC()
        dsbdesc.dwSize = ctypes.sizeof(dsbdesc)
        dsbdesc.dwFlags = lib.DSBCAPS_GLOBALFOCUS | lib.DSBCAPS_CTRLVOLUME
        if audio_format.channels == 1:
            dsbdesc.dwFlags |= lib.DSBCAPS_CTRL3D
        dsbdesc.dwBufferBytes = self._buffer_size
        dsbdesc.lpwfxFormat = ctypes.pointer(wfx)

        dsb = lib.IDirectSoundBuffer()
        dsound.CreateSoundBuffer(dsbdesc, ctypes.byref(dsb), None)
        self._buffer = dsb

    def _get_audio_data(self, bytes):
        if self._next_audio_data:
            audio_data = self._next_audio_data
            self._next_audio_data = None
            bytes -= audio_data.length
            yield audio_data

        try:
            source = self._sources[self._source_read_index]
        except IndexError:
            source = None

        while source:
            audio_data = source._get_audio_data(bytes)
            if audio_data:
                bytes -= audio_data.length
                yield audio_data
            else:
                if self._eos_action == self.EOS_NEXT:
                    self._source_read_index += 1
                    try:
                        source = self._sources[self._source_read_index]
                        source._play()
                    except IndexError:
                        source = None
                elif self._eos_action == self.EOS_LOOP:
                    source.seek(0)
                elif self._eos_action == self.EOS_PAUSE:
                    source = None
                elif self._eos_action == self.EOS_STOP:
                    source = None
                else:
                    assert False, 'Invalid eos_action'
                    source = None

    def _fill_buffer(self):
        if self._buffer:
            play_cursor = lib.DWORD()
            self._buffer.GetCurrentPosition(play_cursor, None)
            if self._write_cursor > play_cursor.value:
                write_size = self._write_cursor - play_cursor.value
            else:
                write_size = self._buffer_size - self._write_cursor + \
                    play_cursor.value
        else:
            write_size = self._buffer_size
            self._create_buffer(
                self.sources[self._source_read_index].audio_format)

        if write_size < self._update_buffer_size:
            return

        for audio_data in self._get_audio_data(write_size):
            length = min(write_size, audio_data.length)

            p1 = ctypes.c_void_p()
            l1 = lib.DWORD()
            p2 = ctypes.c_void_p()
            l2 = lib.DWORD()
            self._buffer.Lock(self._write_cursor, length, 
                ctypes.byref(p1), l1, ctypes.byref(p2), l2, 0)
            assert length == l1.value + l2.value
            ctypes.memmove(p1, audio_data.data, l1.value)
            if l2.value:
                audio_data.consume(l1)
                ctypes.memmove(p2, audio_data.data, l2.value)
            self._buffer.Unlock(p1, l1, p2, l2)

            self._write_cursor += length
            self._write_cursor %= self._buffer_size

            if length < audio_data.length:
                audio_data.consume(length,
                    self._sources[self._source_read_index].audio_format)
                self._next_audio_data = audio_data

            write_size -= length
            if write_size <= 0:
                break

    def queue(self, source):
        source = source._get_queue_source()

        if not self._sources:
            source._init_texture(self)
            self._create_buffer(source.audio_format)
            
        self._sources.append(source)

    def next(self):
        if self._sources:
            old_source = self._sources.pop(0)
            old_source._release_texture(self)
            old_source._stop()
            self._source_read_index -= 1

        if self._sources:
            self._sources[0]._init_texture(self)

    def dispatch_events(self):
        if not self._sources:
            return

        if self._playing:
            now = time.time()
            self._timestamp += now - self._timestamp_time
            self._timestamp_time = now

        self._fill_buffer()

        if self._texture:
            self._sources[0]._update_texture(self, self._timestamp)

        if self._timestamp > self._sources[0].duration:
            self.next()
            self._timestamp = 0.

    def _get_time(self):
        if not self._playing:
            return self._timestamp

        return self._timestamp + time.time() - self._timestamp_time

    def play(self):
        if self._playing:
            return

        self._playing = True

        if not self._sources:
            return

        if self._buffer:
            self._buffer.Play(0, 0, lib.DSBPLAY_LOOPING)
            self._buffer_playing = True

        self._timestamp_time = time.time()

    def pause(self):
        self._playing = False

        if not self._sources:
            return

    def seek(self, timestamp):
        if self._sources:
            self._sources[0]._seek(timestamp)
            self._timestamp = timestamp
            self._timestamp_time = time.time()

    def _get_source(self):
        if self._sources:
            return self._sources[0]
        return None

    def _set_volume(self, volume):
        self._volume = volume

    def _set_min_gain(self, min_gain):
        self._min_gain = min_gain

    def _set_max_gain(self, max_gain):
        self._max_gain = max_gain

    def _set_position(self, position):
        self._position = position

    def _set_velocity(self, velocity):
        self._velocity = velocity

    def _set_pitch(self, pitch):
        self._pitch = pitch

    def _set_cone_orientation(self, cone_orientation):
        self._cone_orientation = cone_orientation

    def _set_cone_inner_angle(self, cone_inner_angle):
        self._cone_inner_angle = cone_inner_angle

    def _set_cone_outer_gain(self, cone_outer_gain):
        self._cone_outer_gain = cone_outer_gain

class DirectSoundManagedSoundPlayer(DirectSoundPlayer, ManagedSoundPlayerMixIn):
    pass

class DirectSoundListener(Listener):
    def set_volume(self, volume):
        self._volume = volume

    def set_position(self, position):
        self._position = position

    def set_velocity(self, velocity):
        self._velocity = velocity

    def set_forward_orientation(self, orientation):
        self._forward_orientation = orientation

    def set_up_orientation(self, orientation):
        self._up_orientation = orientation

    def set_doppler_factor(self, factor):
        self._doppler_factor = factor

    def set_speed_of_sound(self, speed_of_sound):
        self._speed_of_sound = speed_of_sound

def driver_init():
    global dsound
    dsound = lib.IDirectSound()
    lib.DirectSoundCreate(None, ctypes.byref(dsound), None)

    # TODO
    from pyglet import window
    w = window.Window(visible=False)

    dsound.SetCooperativeLevel(w._hwnd, lib.DSSCL_NORMAL)

driver_listener = DirectSoundListener()
DriverPlayer = DirectSoundPlayer
DriverManagedSoundPlayer = DirectSoundManagedSoundPlayer
dsound = None
