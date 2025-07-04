from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, NoReturn

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
        self._audio_state_proxy = create_proxy(self._update_button_state)
        self.ctx.onstatechange = self._audio_state_proxy

    def _update_button_state(self, event=None):
        state = self.ctx.state
        if state == "suspended":
            if not self._start_button:
                self._create_approval()
            self._start_button.style.display = "block"
        else:
            if self._start_button:
                self._start_button.style.display = "none"

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
        # Create a button element to resume audio, as browsers may block it due to abuse of page sounds.
        assert self._start_button is None
        self._start_button = js.document.createElement("button")
        self._start_button.innerHTML = "Click to Enable Audio"
        self._start_button.style.top = "50%"
        self._start_button.style.left = "50%"
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
        return PyodideJSListener(self)

    def delete(self):
        pass

def _convert_coordinates(coordinates: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = coordinates
    return x, y, -z

class PyodideJSListener(AbstractListener):
    """Not currently supported."""

    def __init__(self, driver: JSAudioDriver):
        super().__init__()
        self._driver = driver
        self._listener = driver.ctx.listener

    def _set_volume(self, volume):
        pass

    def _set_position(self, position: tuple[float, float, float]):
        self._position = position
        self._listener.positionX = position[0]
        self._listener.positionY = position[0]
        self._listener.positionZ = position[0]

    def _set_forward_orientation(self, orientation):
        self._forward_orientation = orientation

        x, y, z = _convert_coordinates(orientation)
        self._listener.forwardX = x
        self._listener.forwardY = y
        self._listener.forwardZ = z

    def _set_up_orientation(self, orientation):
        self._up_orientation = orientation
        x, y, z = _convert_coordinates(orientation)
        self._listener.upX = x
        self._listener.upY = y
        self._listener.upZ = z

    def _set_orientation(self):
        pass


class PyodideJSAudioPlayer(AbstractAudioPlayer):
    def __init__(self, driver: JSAudioDriver, source: JavascriptWebAudioSource, player: Player) -> None:
        super().__init__(source, player)
        self.driver = driver
        self._buffer_loaded = False

        self._source_player = driver.ctx.createBufferSource()
        # Audio buffer has not been loaded yet.
        if not source.audio_buffer:
            self._buffer_loaded = False
            source.add_player(self)
        else:
            self._buffer_loaded = True
            self._source_player.buffer = source.audio_buffer

        # Only create a gain node if the volume is actually adjusted.

        self._gain_node = self.driver.ctx.createGain()
        self._panner_node = self.driver.ctx.createPanner()
        # Connect Source to Gain Node
        self._source_player.connect(self._gain_node)
        # Connect Gain to Panner
        self._gain_node.connect(self._panner_node)

        # Connect Panner to Destination
        self._panner_node.connect(self.driver.ctx.destination)

        self._pseudo_play_cursor = 0
        self._pseudo_write_cursor = 0
        self._playing = False
        self._start_position = 0

        self._exhausted = False
        self._dispatched_on_eos = False

        # Optionally, you can set up an "onended" event:
        def on_ended(_) -> None:  # noqa: ANN001
            self._playing = False
            # Dispatch EOS event if needed.
            asyncio.create_task(MediaEvent('on_eos').sync_dispatch_to_player(self.player))

        self._source_player.onended = on_ended

    def on_source_finished_loading(self, source: JavascriptWebAudioSource) -> None:
        self._source_player.buffer = source.audio_buffer
        self._buffer_loaded = True

    def __del__(self) -> None:
        self.delete()

    def delete(self) -> None:
        if self._gain_node:
            self._gain_node.disconnect()
            self._gain_node = None

        if self._panner_node:
            self._panner_node.disconnect()
            self._panner_node = None

        if self._source_player:
            self._source_player.disconnect()
            self._source_player.onended = None
            self._source_player = None

    def play(self) -> None:
        self._playing = True
        self._source_player.start(self._start_position)

    def stop(self) -> None:
        self._source_player.stop()
        self._playing = False

    def work(self) -> NoReturn:
        raise NotImplementedError("This should not be called for this player.")

    def prefill_audio(self) -> None:
        pass

    def _update_play_cursor(self) -> None:
        return

    def clear(self) -> None:
        super().clear()
        self._pseudo_play_cursor = 0
        self._pseudo_write_cursor = 0
        self._exhausted = False
        self._dispatched_on_eos = False

    def seek(self, position: float) -> None:
        self._start_position = position
        if self._playing:
            self._source_player.start(position)

    def get_play_cursor(self) -> float:
        return self._pseudo_play_cursor

    def set_volume(self, volume: float) -> None:
        if self._gain_node:
            self._gain_node.gain.value = volume

    def set_position(self, position: tuple[float, float, float]) -> None:
        if self._panner_node:
            x, y, z = position
            self._panner_node.positionX.value = x
            self._panner_node.positionY.value = y
            self._panner_node.positionZ.value = z

    def set_min_distance(self, min_distance: float) -> None:
        if self._panner_node:
            self._panner_node.refDistance = min_distance

    def set_max_distance(self, max_distance: float) -> None:
        if self._panner_node:
            self._panner_node.maxDistance = max_distance

    def set_pitch(self, pitch: float) -> None:
        if self._source_player:
            self._source_player.playbackRate.value = pitch

    def set_cone_orientation(self, cone_orientation: tuple[float, float, float]) -> None:
        if self._panner_node:
            x, y, z = cone_orientation
            self._panner_node.orientationX.value = x
            self._panner_node.orientationY.value = y
            self._panner_node.orientationZ.value = z

    def set_cone_inner_angle(self, cone_inner_angle: float) -> None:
        if self._panner_node:
            self._panner_node.coneInnerAngle = cone_inner_angle

    def set_cone_outer_angle(self, cone_outer_angle: float) -> None:
        if self._panner_node:
            self._panner_node.coneOuterAngle = cone_outer_angle

    def set_cone_outer_gain(self, cone_outer_gain: float) -> None:
        if self._panner_node:
            self._panner_node.coneOuterGain = cone_outer_gain


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
