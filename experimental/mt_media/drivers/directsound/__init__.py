#!/usr/bin/python
# $Id:$

import ctypes
import math
import sys
import threading
import time

import pyglet
_debug = pyglet.options['debug_media']

import mt_media

import lib_dsound as lib
from pyglet.window.win32 import _user32, _kernel32

class DirectSoundException(mt_media.MediaException):
    pass

def _db(gain):
    '''Convert linear gain in range [0.0, 1.0] to 100ths of dB.'''
    if gain <= 0:
        return -10000
    return max(-10000, min(int(1000 * math.log(min(gain, 1))), 0))

class DirectSoundWorker(mt_media.MediaThread):
    _min_write_size = 9600

    # Time to wait if there are players, but they're all full.
    _nap_time = 0.02

    # Time to wait if there are no players.
    _sleep_time = None

    def __init__(self, target=None):
        super(DirectSoundWorker, self).__init__(target)
        self.players = set()

    def run(self):
        while True:
            self.condition.acquire()
            players = list(self.players)
            self.condition.release()

            if players:
                player = None
                write_size = 0
                for p in players:
                    s = p.get_write_size()
                    if s > write_size:
                        player = p
                        write_size = s

                if write_size > self._min_write_size:
                    player.refill(write_size)
                else:
                    self.sleep(self._nap_time)
            else:
                self.sleep(self._sleep_time)

    def add(self, player):
        self.condition.acquire()
        self.players.add(player)
        self.condition.notify()
        self.condition.release()

    def remove(self, player):
        self.condition.acquire()
        self.players.remove(player)
        self.condition.notify()
        self.condition.release()

class DirectSoundAudioPlayer(mt_media.AbstractAudioPlayer):
    _buffer_size = 44800 * 1
    _update_buffer_size = _buffer_size // 4
    _buffer_size_secs = None

    _cone_inner_angle = 360
    _cone_outer_angle = 360

    UPDATE_PERIOD = 0.05

    def __init__(self, source_group, player):
        super(DirectSoundAudioPlayer, self).__init__(source_group, player)

        # Locking strategy:
        # All DirectSound calls should be locked.  All instance vars relating
        # to buffering/filling/time/events should be locked (used by both
        # application and worker thread).  Other instance vars (consts and
        # 3d vars) do not need to be locked.
        self._lock = threading.RLock()

        audio_format = source_group.audio_format

        self._playing = False
        self._timestamp = 0.

        self._buffer = None
        self._buffer_playing = False
        self._data_size = 0     # amount of buffer filled by this player
        self._play_cursor = 0
        self._buffer_time = 0.  # ts of buffer at buffer_time_pos
        self._buffer_time_pos = 0
        self._write_cursor = 0
        self._timestamps = []
        self._eos_count = 0

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
                           lib.DSBCAPS_CTRLFREQUENCY |
                           lib.DSBCAPS_CTRLVOLUME)
        if audio_format.channels == 1:
            dsbdesc.dwFlags |= lib.DSBCAPS_CTRL3D
        dsbdesc.dwBufferBytes = self._buffer_size
        dsbdesc.lpwfxFormat = ctypes.pointer(wfx)

        self._buffer = lib.IDirectSoundBuffer()
        driver._dsound.CreateSoundBuffer(dsbdesc, ctypes.byref(self._buffer), None)

        if audio_format.channels == 1:
            self._buffer3d = lib.IDirectSound3DBuffer()
            self._buffer.QueryInterface(lib.IID_IDirectSound3DBuffer, 
                                        ctypes.byref(self._buffer3d))
        else:
            self._buffer3d = None
        
        self._buffer_size_secs = \
            self._buffer_size / float(audio_format.bytes_per_second)
        self._buffer.SetCurrentPosition(0)

        self.refill(self._buffer_size)
            
    def __del__(self):
        try:
            self.delete()
        except:
            pass

    def delete(self):
        self.lock()

        if driver and driver.worker:
            driver.worker.remove(self)

        self._buffer.Stop()
        self._buffer.Release()
        self._buffer = None
        if self._buffer3d:
            self._buffer3d.Release()
            self._buffer3d = None

        self.unlock()

    def lock(self):
        self._lock.acquire()

    def unlock(self):
        self._lock.release()
        
    def play(self):
        self.lock()
        if not self._playing:
            self._playing = True

            self._buffer.Play(0, 0, lib.DSBPLAY_LOOPING)
            self._buffer_playing = True 
            driver.worker.add(self)
        self.unlock()

    def stop(self):
        self.lock()
        if self._playing:
            self._playing = False

            self._buffer.Stop()
            self._buffer_playing = False
            driver.worker.remove(self)
        self.unlock()

    def clear(self):
        self.lock()
        self._write_cursor = 0
        self._buffer.SetCurrentPosition(0)
        self._data_size = 0
        self.unlock()

    def refill(self, write_size):
        self.lock()
        while write_size > 0:
            audio_data = self.source_group.get_audio_data(write_size)
            # TODO if audio_data is longer than write_size, buffer remaining
            # audio_data.
            if audio_data:
                length = audio_data.length
                self.write(audio_data, length)
                if audio_data.length:
                    print 'ERROR: losing audio data.'
                # XXX write_size -= length - audio_data.length
                write_size -= length
            else:
                self.write(None, write_size)
                write_size = 0
            

        self.unlock()

    def get_write_size(self):
        # Also incidentaly updates play cursor.

        self.lock()

        # Update play cursor, check for wraparound and EOS markers XXX
        play_cursor = lib.DWORD()
        self._buffer.GetCurrentPosition(play_cursor, None)
        if play_cursor.value < self._play_cursor:
            # Wrapped around
            self._buffer_time_pos -= self._buffer_size
            self._timestamps = \
                [(a - self._buffer_size, t) for a, t in self._timestamps]

        play_cursor = self._play_cursor = play_cursor.value
        write_cursor = self._write_cursor
        data_size = self._data_size
        playing = self._playing
        buffer_playing = self._buffer_playing # XXX

        self.unlock()

        if self._data_size < self._buffer_size:
            return self._buffer_size - self._data_size

        if write_cursor == play_cursor and buffer_playing:
            # Polling too fast, no play cursor movement
            return 0
        elif write_cursor == play_cursor and not playing:
            # Paused and up-to-date
            return 0
        elif write_cursor < play_cursor:
            # Play cursor ahead of write cursor
            write_size = play_cursor - write_cursor
        else:
            # Play cursor behind write cursor, wraps around
            write_size = self._buffer_size - write_cursor + play_cursor

        return write_size

    def write(self, audio_data, length):
        # Pass audio_data=None to write silence
        if length == 0:
            return 0

        self.lock()
        #assert length <= self.get_write_size()

        if self._data_size < self._buffer_size:
            self._data_size = min(self._data_size + length, self._buffer_size)

        p1 = ctypes.c_void_p()
        l1 = lib.DWORD()
        p2 = ctypes.c_void_p()
        l2 = lib.DWORD()
        self._buffer.Lock(self._write_cursor, length, 
            ctypes.byref(p1), l1, ctypes.byref(p2), l2, 0)
        assert length == l1.value + l2.value

        if audio_data:
            if self._write_cursor >= self._play_cursor:
                wc = self._write_cursor
            else:
                wc = self._write_cursor + self._buffer_size
            self._timestamps.append((wc, audio_data.timestamp))
            
            ctypes.memmove(p1, audio_data.data, l1.value)
            audio_data.consume(l1.value, self.source_group.audio_format)
            if l2.value:
                ctypes.memmove(p2, audio_data.data, l2.value)
                audio_data.consume(l2.value, self.source_group.audio_format)
        else:
            ctypes.memset(p1, 0, l1.value)
            if l2.value:
                ctypes.memset(p2, 0, l2.value)
                pass
        self._buffer.Unlock(p1, l1, p2, l2)

        self._write_cursor += length
        self._write_cursor %= self._buffer_size
        self.unlock()

    def get_time(self):
        # Will be accurate to within driver.worker._nap_time secs (0.02).
        # XXX Could provide another method that gets a more accurate time, at
        # more expense.
        self.lock()
        t = self._timestamp
        self.unlock()
        return t
        
    def set_volume(self, volume):
        volume = _db(volume)
        self.lock()
        self._buffer.SetVolume(volume)
        self.unlock()

    def set_position(self, position):
        if self._buffer3d:
            x, y, z = position
            self.lock()
            self._buffer3d.SetPosition(x, y, -z, lib.DS3D_IMMEDIATE)
            self.unlock()

    def set_min_distance(self, min_distance):
        if self._buffer3d:
            self.lock()
            self._buffer3d.SetMinDistance(min_distance, lib.DS3D_IMMEDIATE)
            self.unlock()

    def set_max_distance(self, max_distance):
        if self._buffer3d:
            self.lock()
            self._buffer3d.SetMaxDistance(max_distance, lib.DS3D_IMMEDIATE)
            self.unlock()

    def set_pitch(self, pitch):
        frequency = int(pitch * self.audio_format.sample_rate)
        self.lock()
        self._buffer.SetFrequency(frequency)
        self.unlock()

    def set_cone_orientation(self, cone_orientation):
        if self._buffer3d:
            x, y, z = cone_orientation
            self.lock()
            self._buffer3d.SetConeOrientation(x, y, -z, lib.DS3D_IMMEDIATE)
            self.unlock()

    def set_cone_inner_angle(self, cone_inner_angle):
        if self._buffer3d:
            self._cone_inner_angle = int(cone_inner_angle)
            self._set_cone_angles()

    def set_cone_outer_angle(self, cone_outer_angle):
        if self._buffer3d:
            self._cone_outer_angle = int(cone_outer_angle)
            self._set_cone_angles()

    def _set_cone_angles(self):
        inner = min(self._cone_inner_angle, self._cone_outer_angle)
        outer = max(self._cone_inner_angle, self._cone_outer_angle)
        self.lock()
        self._buffer3d.SetConeAngles(inner, outer, lib.DS3D_IMMEDIATE)
        self.unlock()

    def set_cone_outer_gain(self, cone_outer_gain):
        if self._buffer3d:
            volume = _db(cone_outer_gain)
            self.lock()
            self._buffer3d.SetConeOutsideVolume(volume, lib.DS3D_IMMEDIATE)
            self.unlock()

class DirectSoundDriver(mt_media.AbstractAudioDriver):
    def __init__(self):
        self._dsound = lib.IDirectSound()
        lib.DirectSoundCreate(None, ctypes.byref(self._dsound), None)

        # A trick used by mplayer.. use desktop as window handle since it
        # would be complex to use pyglet window handles (and what to do when
        # application is audio only?).
        hwnd = _user32.GetDesktopWindow()
        self._dsound.SetCooperativeLevel(hwnd, lib.DSSCL_NORMAL)

        # Create primary buffer with 3D and volume capabilities
        self._buffer = lib.IDirectSoundBuffer()
        dsbd = lib.DSBUFFERDESC()
        dsbd.dwSize = ctypes.sizeof(dsbd)
        dsbd.dwFlags = (lib.DSBCAPS_CTRL3D |
                        lib.DSBCAPS_CTRLVOLUME |
                        lib.DSBCAPS_PRIMARYBUFFER)
        self._dsound.CreateSoundBuffer(dsbd, ctypes.byref(self._buffer), None)

        # Create listener
        self._listener = lib.IDirectSound3DListener()
        self._buffer.QueryInterface(lib.IID_IDirectSound3DListener, 
                                    ctypes.byref(self._listener)) 

        # Create worker thread
        self.worker = DirectSoundWorker()
        self.worker.start()

    def __del__(self):
        try:
            if self._buffer:
                self.delete()
        except:
            pass

    def create_audio_player(self, source_group, player):
        return DirectSoundAudioPlayer(source_group, player)

    def delete(self):
        self.worker.stop()
        self._buffer.Release()
        self._buffer = None
        self._listener.Release()
        self._listener = None
        
    # Listener API
      
    def _set_volume(self, volume):
        self._volume = volume
        self._buffer.SetVolume(_db(volume))

    def _set_position(self, position):
        self._position = position
        x, y, z = position
        self._listener.SetPosition(x, y, -z, lib.DS3D_IMMEDIATE)

    def _set_forward_orientation(self, orientation):
        self._forward_orientation = orientation
        self._set_orientation()

    def _set_up_orientation(self, orientation):
        self._up_orientation = orientation
        self._set_orientation()

    def _set_orientation(self):
        x, y, z = self._forward_orientation
        ux, uy, uz = self._up_orientation
        self._listener.SetOrientation(x, y, -z, ux, uy, -uz, lib.DS3D_IMMEDIATE)

def create_audio_driver():
    global driver
    driver = DirectSoundDriver()
    return driver

# Global driver needed for access to worker thread and _dsound
driver = None
