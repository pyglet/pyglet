# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2020 pyglet contributors
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
from collections import namedtuple
import weakref
import pyglet
from pyglet.libs.win32.constants import *
from pyglet.libs.win32.types import *
from . import lib_xaudio2 as lib
from pyglet.util import debug_print

_debug = debug_print('debug_media')

class XAudio2Driver:
    allow_3d = True  # Specifies if positional audio should be used. Can be enabled later, but not disabled.
    processor = lib.XAUDIO2_DEFAULT_PROCESSOR  # Which processor to use. (#1 by default)
    category = lib.AudioCategory_GameEffects  # Which stream classification Windows uses on this driver.

    def __init__(self):
        assert _debug('Constructing XAudio2Driver')
        self._listener = None

        self._emitting_voices = []  # Contains all of the emitting source voices not deleted.

        self._xaudio2 = lib.IXAudio2()
        lib.XAudio2Create(ctypes.byref(self._xaudio2), 0, self.processor)

        if _debug:
            # Debug messages are found in Windows Event Viewer, you must enable event logging:
            # Applications and Services -> Microsoft -> Windows -> Xaudio2 -> Debug Logging.
            # Right click -> Enable Logs
            debug = lib.XAUDIO2_DEBUG_CONFIGURATION()
            debug.LogThreadID = True
            debug.TraceMask = lib.XAUDIO2_LOG_ERRORS | lib.XAUDIO2_LOG_WARNINGS
            debug.BreakMask = lib.XAUDIO2_LOG_WARNINGS

            self._xaudio2.SetDebugConfiguration(ctypes.byref(debug), None)

        self._master_voice = lib.IXAudio2MasteringVoice()
        self._xaudio2.CreateMasteringVoice(byref(self._master_voice),
                                           lib.XAUDIO2_DEFAULT_CHANNELS,
                                           lib.XAUDIO2_DEFAULT_SAMPLERATE,
                                           0, None, None, self.category)

        if self.allow_3d:
            self.enable_3d()

    def enable_3d(self):
        """Initializes the prerequisites for 3D positional audio and initializes with default DSP settings."""
        channel_mask = DWORD()
        self._master_voice.GetChannelMask(byref(channel_mask))

        self._x3d_handle = lib.X3DAUDIO_HANDLE()
        lib.X3DAudioInitialize(channel_mask.value, lib.X3DAUDIO_SPEED_OF_SOUND, self._x3d_handle)

        self._mvoice_details = lib.XAUDIO2_VOICE_DETAILS()
        self._master_voice.GetVoiceDetails(byref(self._mvoice_details))

        matrix = (FLOAT * self._mvoice_details.InputChannels)()
        self._dsp_settings = lib.X3DAUDIO_DSP_SETTINGS()
        self._dsp_settings.SrcChannelCount = 1
        self._dsp_settings.DstChannelCount = self._mvoice_details.InputChannels
        self._dsp_settings.pMatrixCoefficients = matrix

        pyglet.clock.schedule_interval_soft(self._calculate_3d_sources, 1/15.0)

    @property
    def volume(self):
        vol = c_float()
        self._master_voice.GetVolume(ctypes.byref(vol))
        return vol.value

    @volume.setter
    def volume(self, value):
        """Sets global volume of the master voice."""
        self._master_voice.SetVolume(value, 0)

    def _calculate_3d_sources(self, dt):
        """We calculate the 3d emitters and sources every 15 fps, committing everything after deferring all changes."""
        for source_voice in self._emitting_voices:
            self.apply3d(source_voice)

        self._xaudio2.CommitChanges(0)

    def _calculate3d(self, listener, emitter):
        lib.X3DAudioCalculate(
            self._x3d_handle,
            listener,
            emitter,
            lib.default_dsp_calculation,
            self._dsp_settings
        )

    def _apply3d(self, voice, commit):
        """Calculates the output channels based on the listener and emitter and default DSP settings.
           Commit determines if the settings are applied immediately (0) or commited at once through the xaudio driver.
        """
        voice.SetOutputMatrix(self._master_voice,
                              1,
                              self._mvoice_details.InputChannels,
                              self._dsp_settings.pMatrixCoefficients,
                              commit)

        voice.SetFrequencyRatio(self._dsp_settings.DopplerFactor, commit)

    def apply3d(self, source_voice, commit=1):
        self._calculate3d(self._listener.listener, source_voice._emitter)
        self._apply3d(source_voice._voice, commit)

    def __del__(self):
        self._xaudio2.Release()
        self._xaudio2 = None
        pyglet.clock.unschedule(self._calculate_3d_sources)

    def get_performance(self):
        """Retrieve some basic XAudio2 performance data such as memory usage and source counts."""
        pf = lib.XAUDIO2_PERFORMANCE_DATA()
        self._xaudio2.GetPerformanceData(ctypes.byref(pf))
        return pf

    def create_listener(self):
        assert self._listener is None, "You can only create one listener."

        self._listener = XAudio2Listener(self)
        return self._listener

    def create_source_voice(self, source):
        """ Source voice handles all of the audio playing and state for a single source."""
        voice = lib.IXAudio2SourceVoice()

        wfx_format = self.create_wave_format(source.audio_format)


        self._xaudio2.CreateSourceVoice(ctypes.byref(voice),
                                      ctypes.byref(wfx_format),
                                      0,
                                      2.0,
                                      None, None, None)

        source_voice = XA2SourceVoice(voice, source.audio_format, self)
        return source_voice

    def create_buffer(self, audio_data):
        """Creates a XAUDIO2_BUFFER to be used with a source voice.
            Audio data cannot be purged until the source voice has played it; doing so will cause glitches.
            Furthermore, if the data is not in a string buffer, such as pure bytes, it must be converted."""
        if type(audio_data.data) == bytes:
            data = (ctypes.c_char * audio_data.length)()
            ctypes.memmove(data, audio_data.data, audio_data.length)
        else:
            data = audio_data.data

        buff = lib.XAUDIO2_BUFFER()
        buff.AudioBytes = audio_data.length
        buff.pAudioData = data
        return buff

    @staticmethod
    def create_wave_format(audio_format):
        wfx = lib.WAVEFORMATEX()
        wfx.wFormatTag = lib.WAVE_FORMAT_PCM
        wfx.nChannels = audio_format.channels
        wfx.nSamplesPerSec = audio_format.sample_rate
        wfx.wBitsPerSample = audio_format.sample_size
        wfx.nBlockAlign = wfx.wBitsPerSample * wfx.nChannels // 8
        wfx.nAvgBytesPerSec = wfx.nSamplesPerSec * wfx.nBlockAlign
        return wfx

class XA2SourceVoice:
    def __init__(self, voice, audio_format, driver):
        self._voice_state = lib.XAUDIO2_VOICE_STATE()  # Used for buffer state, will be reused constantly.
        self._voice = voice
        self._driver = driver

        # If it's a mono source, then we can make it an emitter.
        # In the future, non-mono source's can be supported as well.
        if audio_format is not None and audio_format.channels == 1:
            self._emitter = lib.X3DAUDIO_EMITTER()
            self._emitter.ChannelCount = 1
            self._emitter.CurveDistanceScaler = 1.0

            # Commented are already set by the Player class.
            # Leaving for visibility on default values
            cone = lib.X3DAUDIO_CONE()
            #cone.InnerAngle = math.radians(360)
            #cone.OuterAngle = math.radians(360)
            cone.InnerVolume = 1.0
            #cone.OuterVolume = 1.0

            self._emitter.pCone = pointer(cone)
            self._emitter.pVolumeCurve = None
            self._driver._emitting_voices.append(self)
        else:
            self._emitter = None

    def __del__(self):
        self.delete()

    def delete(self):
        if self._voice is not None:
            if self._emitter is not None:
                self._driver._emitting_voices.remove(self)
                self._emitter = None

            self._voice.Stop(0, 0)
            self._voice.FlushSourceBuffers()
            self._voice.DestroyVoice()
            self._voice = None

    @property
    def buffers_queued(self):
        self._voice.GetState(ctypes.byref(self._voice_state), 0)
        return self._voice_state.BuffersQueued

    @property
    def volume(self):
        vol = c_float()
        self._voice.GetVolume(ctypes.byref(vol))
        return vol.value

    @volume.setter
    def volume(self, value):
        self._voice.SetVolume(value, 0)

    @property
    def is_emitter(self):
        return self._emitter is not None

    @property
    def position(self):
        if self.is_emitter:
            return self._emitter.Position.x, self._emitter.Position.y, self._emitter.Position.z
        else:
            return 0, 0, 0

    @position.setter
    def position(self, position):
        if self.is_emitter:
            x, y, z = position
            self._emitter.Position.x = x
            self._emitter.Position.y = y
            self._emitter.Position.z = z

    @property
    def min_distance(self):
        """Curve distance scaler that is used to scale normalized distance curves to user-defined world units,
        and/or to exaggerate their effect."""
        if self.is_emitter:
            return self._emitter.CurveDistanceScaler
        else:
            return 0

    @min_distance.setter
    def min_distance(self, value):
        if self.is_emitter:
            if self._emitter.CurveDistanceScaler != value:
                self._emitter.CurveDistanceScaler = min(value, lib.FLT_MAX)


    @property
    def frequency(self):
        """The actual frequency ratio. May not be accurate if changes were not committed by the sound engine.
        If voice is 3d enabled, will be overwritten next apply3d cycle."""
        value = c_float()
        self._voice.GetFrequencyRatio(byref(value))
        return value.value

    @frequency.setter
    def frequency(self, value):
        if self.frequency == value:
            return

        self._voice.SetFrequencyRatio(value, 0)

    @property
    def cone_orientation(self):
        """The orientation of the sound emitter."""
        if self.is_emitter:
            return self._emitter.OrientFront.x, self._emitter.OrientFront.y, self._emitter.OrientFront.z
        else:
            return 0, 0, 0

    @cone_orientation.setter
    def cone_orientation(self, value):
        if self.is_emitter:
            x, y, z = value
            self._emitter.OrientFront.x = x
            self._emitter.OrientFront.y = y
            self._emitter.OrientFront.z = z

    _ConeAngles = namedtuple('_ConeAngles', ['inside', 'outside'])
    @property
    def cone_angles(self):
        """The inside and outside angles of the sound projection cone."""
        if self.is_emitter:
            return self._ConeAngles(self._emitter.pCone.contents.InnerAngle, self._emitter.pCone.contents.OuterAngle)
        else:
            return self._ConeAngles(0, 0)

    def set_cone_angles(self, inside, outside):
        """The inside and outside angles of the sound projection cone."""
        if self.is_emitter:
            self._emitter.pCone.contents.InnerAngle = inside
            self._emitter.pCone.contents.OuterAngle = outside

    @property
    def cone_outside_volume(self):
        """The volume scaler of the sound beyond the outer cone."""
        if self.is_emitter:
            return self._emitter.pCone.contents.OuterVolume
        else:
            return 0

    @cone_outside_volume.setter
    def cone_outside_volume(self, value):
        if self.is_emitter:
            self._emitter.pCone.contents.OuterVolume = value


    @property
    def cone_inside_volume(self):
        """The volume scaler of the sound within the inner cone."""
        if self.is_emitter:
            return self._emitter.pCone.contents.InnerVolume
        else:
            return 0

    @cone_inside_volume.setter
    def cone_inside_volume(self, value):
        if self.is_emitter:
            self._emitter.pCone.contents.InnerVolume = value

    def play(self):
        self._voice.Start(0, 0)

    def stop(self):
        self._voice.Stop(0, 0)

    def submit_buffer(self, x2_buffer):
        self._voice.SubmitSourceBuffer(ctypes.byref(x2_buffer), None)


class XAudio2Listener:
    def __init__(self, driver):
        self.xa2_driver = weakref.proxy(driver)
        self.listener = lib.X3DAUDIO_LISTENER()

    def __del__(self):
        self.delete()

    def delete(self):
        if self.listener:
            self.listener = None

    @property
    def position(self):
        return self.listener.Position.x, self.listener.Position.y, self.listener.Position.z

    @position.setter
    def position(self, value):
        x, y, z = value
        self.listener.Position.x = x
        self.listener.Position.y = y
        self.listener.Position.z = z

    @property
    def orientation(self):
        return self.listener.OrientFront.x, self.listener.OrientFront.y, self.listener.OrientFront.z, \
               self.listener.OrientTop.x, self.listener.OrientTop.y, self.listener.OrientTop.z

    @orientation.setter
    def orientation(self, orientation):
        front_x, front_y, front_z, top_x, top_y, top_z = orientation

        self.listener.OrientFront.x = front_x
        self.listener.OrientFront.y = front_y
        self.listener.OrientFront.z = front_z

        self.listener.OrientTop.x = top_x
        self.listener.OrientTop.y = top_y
        self.listener.OrientTop.z = top_z
