from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pyglet
from pyglet.media.drivers.base import AbstractAudioDriver, AbstractAudioPlayer
from pyglet.media.drivers.listener import AbstractListener

try:
    import js
    from pyodide.ffi import create_proxy
except ImportError:
    raise ImportError('Pyodide not available.')

if TYPE_CHECKING:
    from pyglet.media import Player
    from pyglet.media.codecs.webaudio_pyodide import JavascriptWebAudioSource


class JSAudioDriver(AbstractAudioDriver):
    def __init__(self) -> None:
        super().__init__()
        self._start_button = None
        self._start_button_proxy = None
        self.ctx = js.window.AudioContext.new()
        if self.ctx.state == 'suspended':
            # Audio requires user interaction for enablement in browsers due to abuses.
            self._create_approval()

    def resume_audio_context(self, event):
        if self.ctx.state == "suspended":
            # Resume the AudioContext, and then hide the button
            self.ctx.resume().then(lambda _: js.console.log("AudioContext resumed!"))
        # Optionally, remove or hide the button after the first click
        self._start_button.style.display = "none"

    def _remove_approval(self):
        self._start_button.removeEventListener("click", self._start_button_proxy)
        self._start_button_proxy.destroy()
        self._start_button_proxy = None
        self._start_button.remove()
        self._start_button = None

    def _create_approval(self):
        # Create a button element to resume audio
        assert self._start_button is None
        self._start_button = js.document.createElement("button")
        self._start_button.innerHTML = "Click to Enable Audio"
        # Optional: Style the button to be visible and centered
        #self._start_button.style.position = "absolute"
        self._start_button.style.top = "50%"
        self._start_button.style.left = "50%"
        #self._start_button.style.transform = "translate(-50%, -50%)"
        self._start_button.style.padding = "10px 20px"
        self._start_button.style.fontSize = "16px"
        self._start_button_proxy = create_proxy(self.resume_audio_context)
        self._start_button.addEventListener("click", self._start_button_proxy)
        js.document.body.appendChild(self._start_button)

    def decode_audio(self, array_buffer):
        return self.ctx.decodeAudioData(array_buffer)

    def create_audio_player(self, source, player):
        return PyodideJSAudioPlayer(self, source, player)

    def get_listener(self):
        return PyodideJSListener()

    def delete(self):
        pass


class PyodideJSListener(AbstractListener):
    """Not currently supported."""

    def _set_volume(self, volume):
        pass

    def _set_position(self, position):
        pass

    def _set_forward_orientation(self, orientation):
        pass

    def _set_up_orientation(self, orientation):
        pass

    def _set_orientation(self):
        pass


class PyodideJSAudioPlayer(AbstractAudioPlayer):
    def __init__(self, driver: JSAudioDriver, source: JavascriptWebAudioSource, player: Player):
        super().__init__(source, player)
        self.driver = driver

        self._source_player = driver.ctx.createBufferSource()
        self._source_player.buffer = source.audio_buffer

        self._source_player.connect(self.driver.ctx.destination)

        # Create gain node later.
        #gain_node = driver.ctx.createGain()
        #gain_node.gain.value = volume  # Set initial volume.

        self._pseudo_play_cursor = 0
        self._pseudo_write_cursor = 0
        self._playing = False
        self._start_position = 0

        self._exhausted = False
        self._dispatched_on_eos = False

        # Optionally, you can set up an "onended" event:
        def on_ended(_):
            self._playing = False
            # Dispatch EOS event if needed.
            asyncio.create_task(MediaEvent('on_eos').sync_dispatch_to_player(self.player))

        self._source_player.onended = on_ended

    def delete(self):
        self._source_player.disconnect()
        self._source_player.onended = None
        self._source_player = None

    def play(self):
        self._playing = True
        self._source_player.start(self._start_position)

    def stop(self):
        self._source_player.stop()
        self._playing = False

    def work(self):
        raise NotImplementedError("This should not be called for this player.")

    def prefill_audio(self):
        pass

    def _update_play_cursor(self):
        return
        corrected_time = self.player.time - self.player.last_seek_time
        #pc = self.source.audio_format.timestamp_to_bytes_aligned(corrected_time)
        #assert pc >= self._pseudo_play_cursor
        #self._pseudo_play_cursor = min(self._pseudo_write_cursor, pc)

    def clear(self):
        super().clear()
        self._pseudo_play_cursor = 0
        self._pseudo_write_cursor = 0
        self._exhausted = False
        self._dispatched_on_eos = False

    def seek(self, position):
        self._start_position = position
        if self._playing:
            self._source_player.start(position)

    def get_play_cursor(self):
        return self._pseudo_play_cursor

    def set_volume(self, volume):
        pass

    def set_position(self, position):
        pass

    def set_min_distance(self, min_distance):
        pass

    def set_max_distance(self, max_distance):
        pass

    def set_pitch(self, pitch):
        pass

    def set_cone_orientation(self, cone_orientation):
        pass

    def set_cone_inner_angle(self, cone_inner_angle):
        pass

    def set_cone_outer_angle(self, cone_outer_angle):
        pass

    def set_cone_outer_gain(self, cone_outer_gain):
        pass


class MediaEvent:
    """Representation of a media event.

    These events are used internally by some audio driver implementation to
    communicate events to the :class:`~pyglet.media.player.Player`.
    One example is the ``on_eos`` event.

    Args:
        event (str): Event description.
        timestamp (float): The time when this event happens.
        *args: Any required positional argument to go along with this event.
    """

    __slots__ = 'event', 'timestamp', 'args'

    def __init__(self, event, timestamp=0.0, *args):
        # Meaning of timestamp is dependent on context; and not seen by application.
        self.event = event
        self.timestamp = timestamp
        self.args = args

    async def sync_dispatch_to_player(self, player):
        await pyglet.app.platform_event_loop.post_event(player, self.event, *self.args)

    def __repr__(self):
        return f"MediaEvent({self.event}, {self.timestamp}, {self.args})"

    def __lt__(self, other):
        if not isinstance(other, MediaEvent):
            return NotImplemented
        return self.timestamp < other.timestamp
