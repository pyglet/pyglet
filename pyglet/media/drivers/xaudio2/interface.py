# ruff: noqa: SLF001

from __future__ import annotations

import threading
import weakref
from collections import defaultdict, deque
from collections.abc import Callable
from contextlib import suppress
from ctypes import POINTER, byref, c_char, c_float, cast, pointer
from ctypes.wintypes import DWORD, FLOAT
from typing import TYPE_CHECKING, NamedTuple, TypeAlias, ClassVar

import pyglet
from pyglet.libs.win32 import com
from pyglet.media.devices import get_audio_device_manager
from pyglet.media.devices.base import DeviceFlow, DeviceState
from pyglet.media.exceptions import MediaException
from pyglet.util import debug_print

from . import lib_xaudio2 as lib

if TYPE_CHECKING:
    from pyglet.media.codecs import AudioData, AudioFormat
    from pyglet.media.devices.base import AbstractAudioDeviceManager, AudioDevice
    from pyglet.media.drivers.xaudio2.adaptation import XAudio2AudioPlayer

Vector3: TypeAlias = tuple[float, float, float]
Orientation: TypeAlias = tuple[float, float, float, float, float, float]
VoiceKey: TypeAlias = tuple[int, int]
BufferEndCallback: TypeAlias = Callable[[int], None]


class _MasteringVoiceCreationError(OSError):
    """Raised when XAudio2 cannot attach a mastering voice to an endpoint."""


class ConeAngles(NamedTuple):  # noqa: D101
    inside: float
    outside: float


_debug = debug_print('debug_media')

SAMPLE_FORMATS = {
    "U8": lib.WAVE_FORMAT_PCM,
    "S16": lib.WAVE_FORMAT_PCM,
    "S24": lib.WAVE_FORMAT_PCM,
    "S32": lib.WAVE_FORMAT_PCM,
    "F32": 3,
}


def create_xa2_buffer(audio_data: AudioData) -> lib.XAUDIO2_BUFFER:
    """Creates a XAUDIO2_BUFFER to be used with a source voice.

    Audio data cannot be purged until the source voice has played it; doing so will cause glitches.
    """
    buff = lib.XAUDIO2_BUFFER()
    buff.AudioBytes = audio_data.length
    buff.pAudioData = cast(audio_data.pointer, POINTER(c_char))
    return buff


def create_xa2_waveformat(audio_format: AudioFormat) -> lib.WAVEFORMATEX:
    if audio_format.channels > 2 or audio_format.sample_format not in SAMPLE_FORMATS:
        message = (
            f"XAudio2 does not support '{audio_format.channels}-channel, "
            f"{audio_format.sample_size}-bit {audio_format.sample_type.value}' audio."
        )
        raise MediaException(message)

    wfx = lib.WAVEFORMATEX()
    wfx.wFormatTag = SAMPLE_FORMATS[audio_format.sample_format]
    wfx.nChannels = audio_format.channels
    wfx.nSamplesPerSec = audio_format.sample_rate
    wfx.wBitsPerSample = audio_format.sample_size
    wfx.nBlockAlign = wfx.wBitsPerSample * wfx.nChannels // 8
    wfx.nAvgBytesPerSec = wfx.nSamplesPerSec * wfx.nBlockAlign
    return wfx


class _VoiceResetter:
    """Manage a voice during its reset period."""

    def __init__(
        self,
        driver: XAudio2Driver,
        voice: XA2SourceVoice,
        voice_key: VoiceKey,
        remaining_data: deque[AudioData],
    ) -> None:
        self.driver = driver
        self.voice = voice
        self.voice_key = voice_key
        self.remaining_data = remaining_data

    def run(self) -> None:
        if self.voice.buffers_queued != 0:
            self.voice._callback.on_buffer_end = self.flush_on_buffer_end
            self.voice.flush()
        else:
            pyglet.clock.schedule_once(self._finish, 0)

    def flush_on_buffer_end(self, *_: float) -> None:
        if self.voice.buffers_queued == 0:
            self.remaining_data.clear()
            pyglet.clock.schedule_once(self._finish, 0)

    # Always schedule finish to make sure we're not returning the voice in an
    # XAudio callback. Should give the correct result for samples played.
    def _finish(self, *_: float) -> None:
        self.voice._callback.on_buffer_end = None
        self.voice.samples_played_at_last_recycle = self.voice.samples_played
        self.driver._return_reset_voice(self.voice, self.voice_key)

    def destroy(self) -> None:
        pyglet.clock.unschedule(self._finish)
        self.driver = None
        self.voice = None
        self.remaining_data.clear()


class XA2EngineCallback(com.COMObject):
    _interfaces_ = [lib.IXAudio2EngineCallback]  # noqa: RUF012

    def __init__(self, restart_requested: threading.Event):  # noqa: ANN204
        super().__init__()
        self._restart_requested = restart_requested

    def OnProcessingPassStart(self):  # noqa: ANN201, N802
        pass

    def OnProcessingPassEnd(self):  # noqa: ANN201, N802
        pass

    def OnCriticalError(self, hresult):  # noqa: ANN001, ANN201, N802
        # XAudio2 callbacks must not block or perform engine operations. The pyglet
        # clock observes this flag and recreates the engine on the application thread.
        assert _debug(f"XAudio2EngineCallback.OnCriticalError: {hresult}")
        self._restart_requested.set()


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

    _interfaces_ = [lib.IXAudio2VoiceCallback]  # noqa: RUF012

    def __init__(self):  # noqa: ANN204
        super().__init__()
        self.on_buffer_end: BufferEndCallback | None = None

    def OnBufferEnd(self, pBufferContext):  # noqa: ANN001, ANN201, N802, N803
        callback = self.on_buffer_end
        if callback is not None:
            callback(pBufferContext)

    def OnVoiceError(self, _pBufferContext, hresult):  # noqa: ANN001, ANN201, N802, N803
        assert _debug(f"Error occurred during audio playback: {hresult}")


class XAudio2Driver:
    _listener: XAudio2Listener | None
    _xaudio2: lib.IXAudio2 | None

    _players: set[XAudio2AudioPlayer]
    _resetting_voices: dict[XA2SourceVoice, _VoiceResetter]
    _in_use: dict[XA2SourceVoice, XAudio2AudioPlayer]
    _voice_pool: defaultdict[tuple[int, int], list[XA2SourceVoice]]
    _engine_callback: XA2EngineCallback
    lock: threading.RLock
    _emitting_voices: list[XA2SourceVoice]

    # Specifies if positional audio should be used. Can be enabled later, but not disabled.
    allow_3d: ClassVar[bool] = True

    # Which processor to use. (#1 by default)
    processor: ClassVar[int] = lib.XAUDIO2_DEFAULT_PROCESSOR

    # Which stream classification Windows uses on this driver.
    category: ClassVar[int] = lib.AudioCategory_GameEffects

    # If the driver errors or disappears, it will attempt to restart the engine.
    restart_on_error: ClassVar[bool] = True

    # Max Frequency a voice can have. Setting this higher/lower will increase/decrease memory allocation.
    max_frequency_ratio: ClassVar[float] = 2.0

    def __init__(self) -> None:
        """Creates an XAudio2 master voice and sets up 3D audio if specified.

        This attaches to the default audio device and will create a virtual audio endpoint
        that changes with the system.

        It will not recover if a critical error is encountered such as no more audio devices are present.
        """
        assert _debug('Constructing XAudio2Driver')
        self._listener = None
        self._xaudio2 = None
        self._deleted = False
        # Protects ownership transitions between the active, resetting, and pooled
        # voice collections. This is deliberately not acquired from an XAudio2
        # callback; callbacks must remain non-blocking.
        self.lock = threading.RLock()
        self._restart_lock = threading.Lock()
        self._restart_requested = threading.Event()
        self._engine_callback = XA2EngineCallback(self._restart_requested)
        self._device_id: str | None = None
        self._volume = 1.0
        self._waiting_for_output_device = False
        self._device_manager: AbstractAudioDeviceManager | None = None

        self._emitting_voices: list[XA2SourceVoice] = []
        self._voice_pool: defaultdict[VoiceKey, list[XA2SourceVoice]] = defaultdict(list)
        self._in_use: dict[XA2SourceVoice, XAudio2AudioPlayer] = {}

        self._resetting_voices: dict[XA2SourceVoice, _VoiceResetter] = {}

        self._players: set[XAudio2AudioPlayer] = set()

        try:
            self._create_xa2()
        except _MasteringVoiceCreationError:
            # Catch master voice creation failure. Mostly due to invalid output devices.
            # Catch this to keep this driver selected rather than falling through to a different
            # audio driver.
            # The device manager will request a retry when an output device returns.
            self._wait_for_output_device()

        if self.restart_on_error:
            pyglet.clock.schedule_interval_soft(self._check_state, 0.5)

    def _check_state(self, _dt: float) -> None:
        """Recreate XAudio2 outside of its callback thread after a critical error."""
        if self._deleted or not self._restart_requested.is_set():
            return

        with self._restart_lock:
            if self._deleted or not self._restart_requested.is_set():
                return

            if self._xaudio2 is not None:
                self._shutdown_xaudio2()

            # Clear before creation so a critical error from the new engine is
            # not accidentally erased after it has been reported.
            self._restart_requested.clear()
            try:
                self._create_xa2(self._device_id)
            except _MasteringVoiceCreationError as err:
                # Will occur due to no audio endpoint (if all go missing)
                # No audio endpoint is an expected, stable state. Wait for a
                # Windows device notification instead of retrying every clock
                # tick and spamming the debug log.
                was_waiting = self._waiting_for_output_device
                self._wait_for_output_device()
                if not was_waiting:
                    _debug(f"XAudio2 restart waiting for an output device: {err}")
                return

            self._stop_waiting_for_output_device()
            with self.lock:
                players = tuple(self._players)
                self._players.clear()

        for player in players:
            # The high-level player may have been deleted while the device was absent.
            with suppress(ReferenceError):
                player.player.dispatch_event('on_driver_reset')

    @staticmethod
    def _is_output_device(device: AudioDevice) -> bool:
        return device.platform_flow[device.flow] in (DeviceFlow.OUTPUT, DeviceFlow.INPUT_OUTPUT)

    def _wait_for_output_device(self) -> None:
        """Suspend restart retries until Windows reports an output-device change."""
        self._waiting_for_output_device = True
        if self._device_manager is None:
            self._device_manager = get_audio_device_manager()
            if self._device_manager is not None:
                self._device_manager.push_handlers(self)

        # Avoid missing a device which appeared between CreateMasteringVoice
        # failing and installing the notification handler.
        if self._device_manager is not None and self._device_manager.get_default_output() is not None:
            self._resume_after_output_device_change()

    def _stop_waiting_for_output_device(self) -> None:
        self._waiting_for_output_device = False
        if self._device_manager is not None:
            self._device_manager.remove_handlers(self)
            self._device_manager = None

    def _resume_after_output_device_change(self) -> None:
        if self._waiting_for_output_device and not self._deleted:
            self._waiting_for_output_device = False
            self._restart_requested.set()

    # Audio manager event.
    def on_device_added(self, device: AudioDevice) -> None:
        if self._is_output_device(device):
            self._resume_after_output_device_change()

    # Audio manager event.
    def on_device_state_changed(self, device: AudioDevice, _old_state: DeviceState, new_state: DeviceState) -> None:
        if new_state == DeviceState.ACTIVE and self._is_output_device(device):
            self._resume_after_output_device_change()

    # Audio manager event.
    def on_default_changed(self, device: AudioDevice | None, flow: DeviceFlow) -> None:
        if device is not None and flow in (DeviceFlow.OUTPUT, DeviceFlow.INPUT_OUTPUT):
            self._resume_after_output_device_change()

    def _create_xa2(self, device_id: str | None = None) -> None:
        self._xaudio2 = lib.IXAudio2()

        try:
            lib.XAudio2Create(byref(self._xaudio2), 0, self.processor)
        except OSError as err:
            self._xaudio2 = None
            raise ImportError("XAudio2 driver could not be initialized.") from err

        try:
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
        except OSError:
            self._xaudio2.Release()
            self._xaudio2 = None
            raise

        self._mvoice_details = lib.XAUDIO2_VOICE_DETAILS()
        self._master_voice = lib.IXAudio2MasteringVoice()
        try:
            self._xaudio2.CreateMasteringVoice(
                byref(self._master_voice),
                lib.XAUDIO2_DEFAULT_CHANNELS,
                lib.XAUDIO2_DEFAULT_SAMPLERATE,
                0,
                device_id,
                None,
                self.category,
            )
        except OSError as err:
            self._xaudio2.UnregisterForCallbacks(self._engine_callback)
            self._xaudio2.Release()
            self._xaudio2 = None
            raise _MasteringVoiceCreationError(*err.args) from err

        try:
            self._master_voice.GetVoiceDetails(byref(self._mvoice_details))
            self._master_voice.SetVolume(self._volume, 0)
        except OSError:
            self._xaudio2.UnregisterForCallbacks(self._engine_callback)
            self._xaudio2.Release()
            self._xaudio2 = None
            raise

        self._x3d_handle = None
        self._dsp_settings = None
        if self.allow_3d:
            self.enable_3d()

    @property
    def active_voices(self) -> tuple[XA2SourceVoice, ...]:
        with self.lock:
            return tuple(self._in_use)

    def _destroy_voices(self) -> None:
        """Destroy and clear all voice pools."""
        with self.lock:
            for list_ in self._voice_pool.values():
                for voice in list_:
                    voice.destroy()
                list_.clear()

            for voice, resetter in tuple(self._resetting_voices.items()):
                voice.destroy()
                resetter.destroy()
            self._resetting_voices.clear()

            self._emitting_voices.clear()
            for voice in tuple(self._in_use):
                voice.destroy()
            self._in_use.clear()

    def set_device(self, device: AudioDevice) -> None:
        """Attach XA2 with a specific device rather than the virtual device."""
        self._device_id = device.id
        self._restart_requested.set()
        self._check_state(0)

    def _shutdown_xaudio2(self) -> None:
        """Stops and destroys all active voices, then destroys XA2 instance."""
        with self.lock:
            players = tuple(self._in_use.values())
        for player in players:
            player.on_driver_destroy()
        with self.lock:
            self._players.update(players)

        self._delete_driver()

    def _delete_driver(self) -> None:
        with self.lock:
            if self._xaudio2:
                assert _debug("XAudio2Driver: Deleting")
                # Stop 3d
                if self.allow_3d:
                    pyglet.clock.unschedule(self._calculate_3d_sources)

                # DestroyVoice and Release synchronously wait for XAudio2's
                # processing thread, so callbacks cannot outlive this method.
                self._destroy_voices()

                self._xaudio2.UnregisterForCallbacks(self._engine_callback)
                self._xaudio2.StopEngine()
                self._xaudio2.Release()
                self._xaudio2 = None

    def enable_3d(self) -> None:
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
    def volume(self) -> float:
        if self._xaudio2 is not None:
            try:
                vol = c_float()
                self._master_voice.GetVolume(byref(vol))
                return vol.value
            except OSError:
                # A critical error can invalidate the mastering voice before
                # the clock has observed the restart request.
                pass
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        """Sets global volume of the master voice."""
        self._volume = value
        if self._xaudio2 is not None:
            self._master_voice.SetVolume(value, 0)

    def _calculate_3d_sources(self, _dt: float) -> None:
        """We calculate the 3d emitters and sources every 15 fps, committing everything after deferring all changes."""
        with self.lock:
            if self._xaudio2 is None:
                return
            for source_voice in tuple(self._emitting_voices):
                self._apply3d(source_voice, 1)

            self._xaudio2.CommitChanges(1)

    def apply3d(self, source_voice: XA2SourceVoice) -> None:
        """Apply and immediately commit positional audio effects for the given voice."""
        if self._x3d_handle is not None:
            self._apply3d(source_voice, 2)
            self._xaudio2.CommitChanges(2)

    def _apply3d(self, source_voice: XA2SourceVoice, commit: int) -> None:
        """Calculates and sets output matrix and frequency ratio.

        Calculation is based on the voice based on the listener and the voice's
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
        source_voice._voice.SetOutputMatrix(
            self._master_voice,
            1,
            self._mvoice_details.InputChannels,
            self._dsp_settings.pMatrixCoefficients,
            commit,
        )

        source_voice._voice.SetFrequencyRatio(self._dsp_settings.DopplerFactor, commit)

    def delete(self) -> None:
        pyglet.clock.unschedule(self._check_state)
        with self._restart_lock:
            self._deleted = True
            self._restart_requested.clear()
            self._stop_waiting_for_output_device()
            with self.lock:
                self._players.clear()
            self._delete_driver()

    def get_performance(self) -> lib.XAUDIO2_PERFORMANCE_DATA:
        """Retrieve some basic XAudio2 performance data such as memory usage and source counts."""
        pf = lib.XAUDIO2_PERFORMANCE_DATA()
        self._xaudio2.GetPerformanceData(byref(pf))
        return pf

    def create_listener(self) -> XAudio2Listener:
        assert self._listener is None, "You can only create one listener."
        self._listener = XAudio2Listener(self)
        return self._listener

    def return_voice(self, voice: XA2SourceVoice, remaining_data: deque[AudioData]) -> None:
        """Reset a voice and eventually return it to the pool.

        The voice must be stopped.
        `remaining_data` should contain the data this voice's remaining buffers point to.

        It will be `.clear()`ed shortly after as soon as the flush initiated
        by the driver completes in order to not have theoretical dangling
        pointers.
        """
        with self.lock:
            if voice.is_emitter:
                self._emitting_voices.remove(voice)
            self._in_use.pop(voice)

            assert _debug(f"XA2AudioDriver: Resetting {voice}...")
            voice_key = (voice.channel_count, voice.sample_size)
            resetter = _VoiceResetter(self, voice, voice_key, remaining_data)
            self._resetting_voices[voice] = resetter
            resetter.run()

    def _return_reset_voice(self, voice: XA2SourceVoice, voice_key: VoiceKey) -> None:
        with self.lock:
            resetter = self._resetting_voices.pop(voice, None)
            if resetter is None:
                return
            resetter.destroy()
            if self._xaudio2 is not None:
                self._voice_pool[voice_key].append(voice)
                assert _debug(f"XA2AudioDriver: {voice} back in pool")

    def get_source_voice(self, audio_format: AudioFormat, player: XAudio2AudioPlayer) -> XA2SourceVoice | None:
        """Get a source voice from the pool.

        Source voice creation can be slow to create/destroy.
        So pooling is recommended. We pool based on audio channels.
        A source voice handles all of the audio playing and state for a single source.
        """
        with self.lock:
            if self._xaudio2 is None:
                # A player can be created while there is no default output
                # device.  Remember it so the next successful engine creation
                # can notify its high-level Player to rebuild the voice.
                self._players.add(player)
                return None

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

    def _create_new_voice(self, audio_format: AudioFormat) -> XA2SourceVoice:
        """Has the driver create a new source voice for the given audio format."""
        voice = lib.IXAudio2SourceVoice()

        wfx_format = create_xa2_waveformat(audio_format)

        callback = XAudio2VoiceCallback()
        self._xaudio2.CreateSourceVoice(
            byref(voice),
            byref(wfx_format),
            0,
            self.max_frequency_ratio,
            callback,
            None,
            None,
        )
        return XA2SourceVoice(voice, callback, audio_format.channels, audio_format.sample_size)


class XA2SourceVoice:
    def __init__(
        self,
        voice: lib.IXAudio2SourceVoice,
        callback: XAudio2VoiceCallback,
        channel_count: int,
        sample_size: int,
    ) -> None:
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

    def destroy(self) -> None:
        """Completely destroy the voice."""
        self._emitter = None

        if self._voice is not None:
            self._voice.DestroyVoice()
            self._voice = None

        self._callback = None

    def acquired(self, on_buffer_end_cb: BufferEndCallback, sample_rate: int) -> None:
        """A voice has been acquired.

        Set the callback as well as its new sample rate.
        """
        self._callback.on_buffer_end = on_buffer_end_cb
        self._voice.SetSourceSampleRate(sample_rate)

    @property
    def buffers_queued(self) -> int:
        """Get the amount of buffers in the current voice. Adding flag for no samples played is 3x faster."""
        self._voice.GetState(byref(self._voice_state), lib.XAUDIO2_VOICE_NOSAMPLESPLAYED)
        return self._voice_state.BuffersQueued

    @property
    def samples_played(self) -> int:
        """Get the amount of samples played by the voice."""
        self._voice.GetState(byref(self._voice_state), 0)
        return self._voice_state.SamplesPlayed

    @property
    def volume(self) -> float:
        vol = c_float()
        self._voice.GetVolume(byref(vol))
        return vol.value

    @volume.setter
    def volume(self, value: float) -> None:
        self._voice.SetVolume(value, 0)

    @property
    def is_emitter(self) -> bool:
        return self._emitter is not None

    @property
    def position(self) -> Vector3:
        if self.is_emitter:
            return self._emitter.Position.x, self._emitter.Position.y, self._emitter.Position.z
        return 0, 0, 0

    @position.setter
    def position(self, position: Vector3) -> None:
        if self.is_emitter:
            x, y, z = position
            self._emitter.Position.x = x
            self._emitter.Position.y = y
            self._emitter.Position.z = z

    @property
    def min_distance(self) -> float:
        if self.is_emitter:
            return self._emitter.CurveDistanceScaler
        return 0

    @min_distance.setter
    def min_distance(self, value: float) -> None:
        if self.is_emitter and self._emitter.CurveDistanceScaler != value:
            self._emitter.CurveDistanceScaler = min(value, lib.FLT_MAX)

    @property
    def frequency(self) -> float:
        """The actual frequency ratio. If voice is 3d enabled, will be overwritten next apply3d cycle."""
        value = c_float()
        self._voice.GetFrequencyRatio(byref(value))
        return value.value

    @frequency.setter
    def frequency(self, value: float) -> None:
        if self.frequency == value:
            return

        self._voice.SetFrequencyRatio(value, 0)

    @property
    def cone_orientation(self) -> Vector3:
        """The orientation of the sound emitter."""
        if self.is_emitter:
            return self._emitter.OrientFront.x, self._emitter.OrientFront.y, self._emitter.OrientFront.z
        return 0, 0, 0

    @cone_orientation.setter
    def cone_orientation(self, value: Vector3) -> None:
        if self.is_emitter:
            x, y, z = value
            self._emitter.OrientFront.x = x
            self._emitter.OrientFront.y = y
            self._emitter.OrientFront.z = z

    @property
    def cone_angles(self) -> ConeAngles:
        """The inside and outside angles of the sound projection cone."""
        if self.is_emitter:
            return ConeAngles(self._emitter.pCone.contents.InnerAngle, self._emitter.pCone.contents.OuterAngle)
        return ConeAngles(0, 0)

    def set_cone_angles(self, inside: float, outside: float) -> None:
        """The inside and outside angles of the sound projection cone."""
        if self.is_emitter:
            self._emitter.pCone.contents.InnerAngle = inside
            self._emitter.pCone.contents.OuterAngle = outside

    @property
    def cone_outside_volume(self) -> float:
        """The volume scaler of the sound beyond the outer cone."""
        if self.is_emitter:
            return self._emitter.pCone.contents.OuterVolume
        return 0

    @cone_outside_volume.setter
    def cone_outside_volume(self, value: float) -> None:
        if self.is_emitter:
            self._emitter.pCone.contents.OuterVolume = value

    @property
    def cone_inside_volume(self) -> float:
        """The volume scaler of the sound within the inner cone."""
        if self.is_emitter:
            return self._emitter.pCone.contents.InnerVolume
        return 0

    @cone_inside_volume.setter
    def cone_inside_volume(self, value: float) -> None:
        if self.is_emitter:
            self._emitter.pCone.contents.InnerVolume = value

    def flush(self) -> None:
        """Stop and removes all buffers already queued. OnBufferEnd is called for each."""
        self._voice.Stop(0, 0)
        self._voice.FlushSourceBuffers()

    def play(self) -> None:
        self._voice.Start(0, 0)

    def stop(self) -> None:
        self._voice.Stop(0, 0)

    def submit_buffer(self, x2_buffer: lib.XAUDIO2_BUFFER) -> None:
        self._voice.SubmitSourceBuffer(byref(x2_buffer), None)


class XAudio2Listener:
    def __init__(self, driver: XAudio2Driver) -> None:
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

    def delete(self) -> None:
        self.listener = None

    @property
    def position(self) -> Vector3:
        return self.listener.Position.x, self.listener.Position.y, self.listener.Position.z

    @position.setter
    def position(self, value: Vector3) -> None:
        x, y, z = value
        self.listener.Position.x = x
        self.listener.Position.y = y
        self.listener.Position.z = z

    @property
    def orientation(self) -> Orientation:
        return (
            self.listener.OrientFront.x,
            self.listener.OrientFront.y,
            self.listener.OrientFront.z,
            self.listener.OrientTop.x,
            self.listener.OrientTop.y,
            self.listener.OrientTop.z,
        )

    @orientation.setter
    def orientation(self, orientation: Orientation) -> None:
        front_x, front_y, front_z, top_x, top_y, top_z = orientation

        self.listener.OrientFront.x = front_x
        self.listener.OrientFront.y = front_y
        self.listener.OrientFront.z = front_z

        self.listener.OrientTop.x = top_x
        self.listener.OrientTop.y = top_y
        self.listener.OrientTop.z = top_z
