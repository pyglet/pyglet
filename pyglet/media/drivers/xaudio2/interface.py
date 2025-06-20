import threading
import weakref
from collections import defaultdict, namedtuple
from ctypes import POINTER, byref, c_char, c_float, cast, pointer
from ctypes.wintypes import DWORD, FLOAT

import pyglet
from pyglet.libs.win32 import com
from pyglet.media.devices import get_audio_device_manager
from pyglet.media.devices.base import DeviceFlow
from pyglet.media.exceptions import MediaException
from pyglet.util import debug_print

from . import lib_xaudio2 as lib

_debug = debug_print('debug_media')


def create_xa2_buffer(audio_data):
    """Creates a XAUDIO2_BUFFER to be used with a source voice.

    Audio data cannot be purged until the source voice has played it; doing so will cause glitches.
    """
    buff = lib.XAUDIO2_BUFFER()
    buff.AudioBytes = audio_data.length
    buff.pAudioData = cast(audio_data.pointer, POINTER(c_char))
    return buff


def create_xa2_waveformat(audio_format):
    if audio_format.channels > 2 or audio_format.sample_size not in (8, 16):
        raise MediaException(f'Unsupported audio format: {audio_format}')

    wfx = lib.WAVEFORMATEX()
    wfx.wFormatTag = lib.WAVE_FORMAT_PCM
    wfx.nChannels = audio_format.channels
    wfx.nSamplesPerSec = audio_format.sample_rate
    wfx.wBitsPerSample = audio_format.sample_size
    wfx.nBlockAlign = wfx.wBitsPerSample * wfx.nChannels // 8
    wfx.nAvgBytesPerSec = wfx.nSamplesPerSec * wfx.nBlockAlign
    return wfx


class _VoiceResetter:
    """Manage a voice during its reset period."""

    def __init__(self, driver, voice, voice_key, remaining_data) -> None:
        self.driver = driver
        self.voice = voice
        self.voice_key = voice_key
        self.remaining_data = remaining_data

    def run(self):
        if self.voice.buffers_queued != 0:
            self.voice._callback.on_buffer_end = self.flush_on_buffer_end
            self.voice.flush()
        else:
            pyglet.clock.schedule_once(self._finish, 0)

    def flush_on_buffer_end(self, *_):
        if self.voice.buffers_queued == 0:
            self.remaining_data.clear()
            pyglet.clock.schedule_once(self._finish, 0)

    # Always schedule finish to make sure we're not returning the voice in an
    # XAudio callback. Should give the correct result for samples played.
    def _finish(self, *_):
        self.voice._callback.on_buffer_end = None
        self.voice.samples_played_at_last_recycle = self.voice.samples_played
        self.driver._return_reset_voice(self.voice, self.voice_key)

    def destroy(self):
        pyglet.clock.unschedule(self._finish)
        self.driver = None
        self.voice = None
        self.remaining_data.clear()


class XA2EngineCallback(com.COMObject):
    _interfaces_ = [lib.IXAudio2EngineCallback]

    def __init__(self, lock):
        super().__init__()
        self._lock = lock

    def OnProcessingPassStart(self):
        self._lock.acquire()

    def OnProcessingPassEnd(self):
        self._lock.release()

    def OnCriticalError(self, hresult):
        # This is a textbook bad example, yes.
        # It's probably safe though: assuming that XA2 has ceased to operate if we ever end up
        # here, nothing can release the lock in between.
        if self._lock.locked():
            self._lock.release()
        raise Exception("Critical Error:", hresult)


class XAudio2VoiceCallback(com.COMObject):
    """Callback class used to trigger when buffers or streams end.
           WARNING: Whenever a callback is running, XAudio2 cannot generate audio.
           Make sure these functions run as fast as possible and do not block/delay more than a few milliseconds.
           MS Recommendation:
           At a minimum, callback functions must not do the following:
                - Access the hard disk or other permanent storage
                - Make expensive or blocking API calls
                - Synchronize with other parts of client code
                - Require significant CPU usage
    """
    _interfaces_ = [lib.IXAudio2VoiceCallback]

    def __init__(self):
        super().__init__()
        self.on_buffer_end = None

    def OnBufferEnd(self, pBufferContext):
        self.on_buffer_end(pBufferContext)

    def OnVoiceError(self, pBufferContext, hresult):
        raise Exception(f"Error occurred during audio playback: {hresult}")


class XAudio2Driver:
    # Specifies if positional audio should be used. Can be enabled later, but not disabled.
    allow_3d = True

    # Which processor to use. (#1 by default)
    processor = lib.XAUDIO2_DEFAULT_PROCESSOR

    # Which stream classification Windows uses on this driver.
    category = lib.AudioCategory_GameEffects

    # If the driver errors or disappears, it will attempt to restart the engine.
    restart_on_error = True

    # Max Frequency a voice can have. Setting this higher/lower will increase/decrease memory allocation.
    max_frequency_ratio = 2.0

    def __init__(self):
        """Creates an XAudio2 master voice and sets up 3D audio if specified. This attaches to the default audio
        device and will create a virtual audio endpoint that changes with the system. It will not recover if a
        critical error is encountered such as no more audio devices are present.
        """
        assert _debug('Constructing XAudio2Driver')
        self._listener = None
        self._xaudio2 = None
        self._dead = False

        # A lock that will prevent XAudio2 from running any callbacks (processing audio at all)
        # while it is held. Must be acquired by audio players in certain situations in order to
        # ensure that the following, very unlikely, sequence of events does not happen:
        # - an on_buffer_end callback is made
        # - python creates a dummy thread to run its code
        # - very early on, before it could acquire any protective locks, the thread is suspended
        #   and the main thread runs
        # - the main thread runs a critical operation on the player such as `delete` to completion
        # - the callback is resumed and breaks as the audio player is deleted.
        self.lock = threading.Lock()
        self._engine_callback = XA2EngineCallback(self.lock)

        self._emitting_voices = []  # Contains all playing source voices with an emitter.
        self._voice_pool = defaultdict(list)
        self._in_use = {}  # All voices currently in use, mapped to their audio player.

        self._resetting_voices = {}  # All resetting voices, mapped to their resetter.

        self._players = []  # Used for resetting/restoring xaudio2. Stores high-level players to callback.

        self._create_xa2()

        if self.restart_on_error:
            audio_devices = get_audio_device_manager()
            if audio_devices:
                assert _debug('Audio device instance found.')
                audio_devices.push_handlers(self)

                if audio_devices.get_default_output() is None:
                    raise ImportError("No default audio device found, can not create driver.")

                pyglet.clock.schedule_interval_soft(self._check_state, 0.5)

    def _check_state(self, dt):
        """Hack/workaround, you cannot shutdown/create XA2 within a COM callback, set a schedule to check state."""
        if self._dead is True:
            if self._xaudio2:
                self._shutdown_xaudio2()
        else:
            if not self._xaudio2:
                self._create_xa2()
                # Notify all active it's reset.
                for player in self._players:
                    player.dispatch_event('on_driver_reset')

                self._players.clear()

    def on_default_changed(self, device, flow: DeviceFlow):
        if flow == DeviceFlow.OUTPUT:
            """Callback derived from the Audio Devices to help us determine when the system no longer has output."""
            if device is None:
                assert _debug('Error: Default audio device was removed or went missing.')
                self._dead = True
            else:
                if self._dead:
                    assert _debug('Warning: Default audio device added after going missing.')
                    self._dead = False

    def _create_xa2(self, device_id=None):
        self._xaudio2 = lib.IXAudio2()

        try:
            lib.XAudio2Create(byref(self._xaudio2), 0, self.processor)
        except OSError:
            raise ImportError("XAudio2 driver could not be initialized.")

        if _debug:
            # Debug messages are found in Windows Event Viewer, you must enable event logging:
            # Applications and Services -> Microsoft -> Windows -> Xaudio2 -> Debug Logging.
            # Right click -> Enable Logs
            debug = lib.XAUDIO2_DEBUG_CONFIGURATION()
            debug.LogThreadID = True
            debug.TraceMask = lib.XAUDIO2_LOG_ERRORS | lib.XAUDIO2_LOG_WARNINGS
            debug.BreakMask = lib.XAUDIO2_LOG_WARNINGS

            self._xaudio2.SetDebugConfiguration(byref(debug), None)

        self._xaudio2.RegisterForCallbacks(self._engine_callback)

        self._mvoice_details = lib.XAUDIO2_VOICE_DETAILS()
        self._master_voice = lib.IXAudio2MasteringVoice()
        self._xaudio2.CreateMasteringVoice(byref(self._master_voice),
                                           lib.XAUDIO2_DEFAULT_CHANNELS,
                                           lib.XAUDIO2_DEFAULT_SAMPLERATE,
                                           0, device_id, None, self.category)
        self._master_voice.GetVoiceDetails(byref(self._mvoice_details))

        self._x3d_handle = None
        self._dsp_settings = None
        if self.allow_3d:
            self.enable_3d()

    @property
    def active_voices(self):
        return self._in_use.keys()

    def _destroy_voices(self):
        """Destroy and clear all voice pools."""
        for list_ in self._voice_pool.values():
            for voice in list_:
                voice.destroy()
            list_.clear()

        for voice, resetter in self._resetting_voices.items():
            voice.destroy()
            resetter.destroy()
        self._resetting_voices.clear()

        for voice in self.active_voices:
            voice.destroy()
        self._in_use.clear()

    def set_device(self, device):
        """Attach XA2 with a specific device rather than the virtual device."""
        self._shutdown_xaudio2()
        self._create_xa2(device.id)

        # Notify all active players it's reset.
        for player in self._players:
            player.dispatch_event('on_driver_reset')

        self._players.clear()

    def _shutdown_xaudio2(self):
        """Stops and destroys all active voices, then destroys XA2 instance."""
        for player in self._in_use.values():
            player.on_driver_destroy()
            self._players.append(player.player)

        self._delete_driver()

    def _delete_driver(self):
        if self._xaudio2:
            assert _debug("XAudio2Driver: Deleting")
            # Stop 3d
            if self.allow_3d:
                pyglet.clock.unschedule(self._calculate_3d_sources)

            # Destroy all pooled voices as master will change.
            self._destroy_voices()

            self._xaudio2.UnregisterForCallbacks(self._engine_callback)
            self._xaudio2.StopEngine()
            self._xaudio2.Release()
            self._xaudio2 = None

    def enable_3d(self):
        """Initializes the prerequisites for 3D positional audio and initializes with default DSP settings."""
        channel_mask = DWORD()
        self._master_voice.GetChannelMask(byref(channel_mask))

        self._x3d_handle = lib.X3DAUDIO_HANDLE()
        lib.X3DAudioInitialize(channel_mask.value, lib.X3DAUDIO_SPEED_OF_SOUND, self._x3d_handle)

        matrix = (FLOAT * self._mvoice_details.InputChannels)()
        self._dsp_settings = lib.X3DAUDIO_DSP_SETTINGS()
        self._dsp_settings.SrcChannelCount = 1
        self._dsp_settings.DstChannelCount = self._mvoice_details.InputChannels
        self._dsp_settings.pMatrixCoefficients = matrix

        pyglet.clock.schedule_interval_soft(self._calculate_3d_sources, 1 / 15.0)

    @property
    def volume(self):
        vol = c_float()
        self._master_voice.GetVolume(byref(vol))
        return vol.value

    @volume.setter
    def volume(self, value):
        """Sets global volume of the master voice."""
        self._master_voice.SetVolume(value, 0)

    def _calculate_3d_sources(self, dt):
        """We calculate the 3d emitters and sources every 15 fps, committing everything after deferring all changes."""
        for source_voice in self._emitting_voices:
            self._apply3d(source_voice, 1)

        self._xaudio2.CommitChanges(1)

    def apply3d(self, source_voice):
        """Apply and immediately commit positional audio effects for the given voice."""
        if self._x3d_handle is not None:
            self._apply3d(source_voice, 2)
            self._xaudio2.CommitChanges(2)

    def _apply3d(self, source_voice, commit):
        """Calculates and sets output matrix and frequency ratio on the voice based on the listener and the voice's
           emitter. Commit determines the operation set, whether the settings are applied immediately (0) or to
           be committed together at a later time.
        """
        lib.X3DAudioCalculate(
            self._x3d_handle,
            self._listener.listener,
            source_voice._emitter,
            lib.default_dsp_calculation,
            self._dsp_settings,
        )
        source_voice._voice.SetOutputMatrix(self._master_voice,
                                            1,
                                            self._mvoice_details.InputChannels,
                                            self._dsp_settings.pMatrixCoefficients,
                                            commit)

        source_voice._voice.SetFrequencyRatio(self._dsp_settings.DopplerFactor, commit)

    def delete(self):
        self._delete_driver()
        pyglet.clock.unschedule(self._check_state)

    def get_performance(self):
        """Retrieve some basic XAudio2 performance data such as memory usage and source counts."""
        pf = lib.XAUDIO2_PERFORMANCE_DATA()
        self._xaudio2.GetPerformanceData(byref(pf))
        return pf

    def create_listener(self):
        assert self._listener is None, "You can only create one listener."
        self._listener = XAudio2Listener(self)
        return self._listener

    def return_voice(self, voice, remaining_data):
        """Reset a voice and eventually return it to the pool. The voice must be stopped.
        `remaining_data` should contain the data this voice's remaining
        buffers point to.
        It will be `.clear()`ed shortly after as soon as the flush initiated
        by the driver completes in order to not have theoretical dangling
        pointers.
        """
        if voice.is_emitter:
            self._emitting_voices.remove(voice)
        self._in_use.pop(voice)

        assert _debug(f"XA2AudioDriver: Resetting {voice}...")
        voice_key = (voice.channel_count, voice.sample_size)
        resetter = _VoiceResetter(self, voice, voice_key, remaining_data)
        self._resetting_voices[voice] = resetter
        resetter.run()

    def _return_reset_voice(self, voice, voice_key):
        self._resetting_voices.pop(voice).destroy()
        self._voice_pool[voice_key].append(voice)
        assert _debug(f"XA2AudioDriver: {voice} back in pool")

    def get_source_voice(self, audio_format, player):
        """Get a source voice from the pool. Source voice creation can be slow to create/destroy.
        So pooling is recommended. We pool based on audio channels.
        A source voice handles all of the audio playing and state for a single source."""

        voice_key = (audio_format.channels, audio_format.sample_size)
        if not self._voice_pool[voice_key]:
            voice = self._create_new_voice(audio_format)
            # Create a 2nd one for good measure, multiple players might be needing it soon,
            # and a clear command will probably complete more quickly when swapping out for a
            # pooled voice
            self._voice_pool[voice_key].append(self._create_new_voice(audio_format))
        else:
            voice = self._voice_pool[voice_key].pop()

        assert voice.buffers_queued == 0

        voice.acquired(player.on_buffer_end, audio_format.sample_rate)
        if voice.is_emitter:
            self._emitting_voices.append(voice)
        self._in_use[voice] = player

        return voice

    def _create_new_voice(self, audio_format):
        """Has the driver create a new source voice for the given audio format."""
        voice = lib.IXAudio2SourceVoice()

        wfx_format = create_xa2_waveformat(audio_format)

        callback = XAudio2VoiceCallback()
        self._xaudio2.CreateSourceVoice(byref(voice),
                                        byref(wfx_format),
                                        0,
                                        self.max_frequency_ratio,
                                        callback,
                                        None,
                                        None)
        return XA2SourceVoice(voice, callback, audio_format.channels, audio_format.sample_size)


class XA2SourceVoice:
    def __init__(self, voice, callback, channel_count, sample_size):
        self._voice_state = lib.XAUDIO2_VOICE_STATE()  # Used for buffer state, will be reused constantly.
        self._voice = voice
        self._callback = callback

        self.channel_count = channel_count
        self.sample_size = sample_size

        # How many samples the voice had played when it was most recently re-added into the
        # pool of available voices.
        self.samples_played_at_last_recycle = 0

        # If it's a mono source, then we can make it an emitter.
        # In the future, non-mono source's can be supported as well.
        if channel_count == 1:
            self._emitter = lib.X3DAUDIO_EMITTER()
            self._emitter.ChannelCount = channel_count
            self._emitter.CurveDistanceScaler = 1.0

            # Commented are already set by the Player class.
            # Leaving for visibility on default values
            cone = lib.X3DAUDIO_CONE()
            # cone.InnerAngle = math.radians(360)
            # cone.OuterAngle = math.radians(360)
            cone.InnerVolume = 1.0
            # cone.OuterVolume = 1.0

            self._emitter.pCone = pointer(cone)
            self._emitter.pVolumeCurve = None
        else:
            self._emitter = None

    def destroy(self):
        """Completely destroy the voice."""
        self._emitter = None

        if self._voice is not None:
            self._voice.DestroyVoice()
            self._voice = None

        self._callback = None

    def acquired(self, on_buffer_end_cb, sample_rate):
        """A voice has been acquired. Set the callback as well as its new sample
        rate.
        """
        self._callback.on_buffer_end = on_buffer_end_cb
        self._voice.SetSourceSampleRate(sample_rate)

    @property
    def buffers_queued(self):
        """Get the amount of buffers in the current voice. Adding flag for no samples played is 3x faster."""
        self._voice.GetState(byref(self._voice_state), lib.XAUDIO2_VOICE_NOSAMPLESPLAYED)
        return self._voice_state.BuffersQueued

    @property
    def samples_played(self):
        """Get the amount of samples played by the voice."""
        self._voice.GetState(byref(self._voice_state), 0)
        return self._voice_state.SamplesPlayed

    @property
    def volume(self):
        vol = c_float()
        self._voice.GetVolume(byref(vol))
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
        """The actual frequency ratio. If voice is 3d enabled, will be overwritten next apply3d cycle."""
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

    def flush(self):
        """Stop and removes all buffers already queued. OnBufferEnd is called for each."""
        self._voice.Stop(0, 0)
        self._voice.FlushSourceBuffers()

    def play(self):
        self._voice.Start(0, 0)

    def stop(self):
        self._voice.Stop(0, 0)

    def submit_buffer(self, x2_buffer):
        self._voice.SubmitSourceBuffer(byref(x2_buffer), None)


class XAudio2Listener:
    def __init__(self, driver):
        self.xa2_driver = weakref.proxy(driver)
        self.listener = lib.X3DAUDIO_LISTENER()

        # Default listener orientations for DirectSound/XAudio2:
        # Front: (0, 0, 1), Up: (0, 1, 0)
        self.listener.OrientFront.x = 0
        self.listener.OrientFront.y = 0
        self.listener.OrientFront.z = 1

        self.listener.OrientTop.x = 0
        self.listener.OrientTop.y = 1
        self.listener.OrientTop.z = 0

    def delete(self):
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
