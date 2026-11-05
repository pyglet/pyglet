"""Demonstrate intro/loop/outro playback with mutable loop counts."""

import sys
from pathlib import Path

import pyglet
from pyglet import shapes
from pyglet.window import key


class LoopingSourceTimeline:
    """Draw and control a timeline for a :class:`~pyglet.media.LoopingSource`."""

    def __init__(
        self,
        source,
        player,
        *,
        duration=None,
        x=20,
        y=38,
        width=580,
        height=22,
        batch=None,
    ):
        self.source = source
        self.player = player
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.duration = duration or source.loop_end
        self.loop_start = source.loop_start
        self.loop_end = source.loop_end
        self.loop_length = self.loop_end - self.loop_start
        self._outro_start_player_time = None
        self.batch = batch or pyglet.graphics.Batch()

        self.start_rect = shapes.Rectangle(
            x, y, width * self.loop_start / self.duration, height,
            color=(70, 120, 190, 255), batch=self.batch,
        )
        self.loop_rect = shapes.Rectangle(
            x + width * self.loop_start / self.duration,
            y,
            width * self.loop_length / self.duration,
            height,
            color=(220, 150, 45, 255),
            batch=self.batch,
        )
        self.end_rect = shapes.Rectangle(
            x + width * self.loop_end / self.duration,
            y,
            width * max(0.0, self.duration - self.loop_end) / self.duration,
            height,
            color=(75, 155, 95, 255),
            batch=self.batch,
        )
        self.cursor = shapes.Rectangle(x, y - 5, 3, height + 10, color=(255, 255, 255), batch=self.batch)
        self.timeline_label = pyglet.text.Label("", x=x, y=y + 44, batch=self.batch)
        self.intro_lbl = pyglet.text.Label("intro", x=x, y=y - 18, font_size=9, batch=self.batch)
        self.loop_lbl = pyglet.text.Label(
            "loop",
            x=x + width * (self.loop_start + self.loop_end) / (2 * self.duration),
            y=y - 18,
            anchor_x="center",
            font_size=9,
            batch=self.batch,
        )
        self.outro_lbl = pyglet.text.Label(
            "outro",
            x=x + width * self.loop_end / self.duration + 4,
            y=y - 18,
            font_size=9,
            batch=self.batch,
        )
        self.label = pyglet.text.Label(
            "Infinite loop: [2.0s, 8.0s). Press 0 for the outro, I for infinite, or 1-9 for repeats.",
            x=x,
            y=y + 80,
            anchor_y="center",
        )

    def source_time(self, elapsed):
        """Map player time to a position in the original source timeline."""
        elapsed = max(0.0, elapsed)
        if self._outro_start_player_time is not None:
            if elapsed >= self._outro_start_player_time:
                return min(self.duration, self.loop_end + elapsed - self._outro_start_player_time)
            return self.loop_start + (elapsed - self.loop_start) % self.loop_length if elapsed >= self.loop_start else elapsed

        current_source = self.player.source
        loop_count = current_source.loop_count if current_source is not None else self.source.loop_count
        if elapsed < self.loop_start:
            return elapsed
        if loop_count == -1:
            return self.loop_start + (elapsed - self.loop_start) % self.loop_length

        repeated_length = (loop_count + 1) * self.loop_length
        if elapsed < self.loop_start + repeated_length:
            return self.loop_start + (elapsed - self.loop_start) % self.loop_length
        return min(self.duration, elapsed - loop_count * self.loop_length)

    def set_loop_count(self, loop_count):
        """Change the loop count while preserving the displayed transition."""
        current_source_time = self.source_time(self.player.time)
        if loop_count == 0 and current_source_time < self.loop_end:
            self._outro_start_player_time = self.player.time + self.loop_end - current_source_time
        else:
            self._outro_start_player_time = None
        self.player.set_loop_count(loop_count)

    def draw(self):
        """Update and draw the timeline."""
        source_time = self.source_time(self.player.time)
        self.cursor.x = self.x + self.width * source_time / self.duration
        self.timeline_label.text = (
            f"source {source_time:5.2f}s / {self.duration:5.2f}s    player {self.player.time:5.2f}s"
        )
        self.label.draw()
        self.batch.draw()

    def on_key_press(self, symbol):
        """Handle the example's loop controls."""
        if symbol == key._0:
            self.set_loop_count(0)
            self.label.text = "Looping disabled; playback will continue into the outro at the next loop boundary."
        elif symbol == key.I:
            self.set_loop_count(-1)
            self.label.text = "Looping infinitely. Press 0 to continue into the outro."
        elif key._1 <= symbol <= key._9:
            loop_count = symbol - key._0
            self.set_loop_count(loop_count)
            self.label.text = f"Loop region will repeat {loop_count} more time(s)."

if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    filename = Path(__file__).parent.parent / "resources" / "audio_loop_low_48khz.wav"

source = pyglet.media.load_audio(filename, streaming=True)
looping_source = pyglet.media.LoopingSource.from_frames(
    source,
    loop_start=96_000,   # 2.0 seconds at 48 kHz
    loop_end=384_000,    # 8.0 seconds at 48 kHz
    loop_count=-1,
)

player = pyglet.media.AudioPlayer()
player.queue(looping_source)
player.play()

window = pyglet.window.Window(620, 150, caption="Looping Source")
timeline = LoopingSourceTimeline(looping_source, player, duration=source.duration)


@window.event
def on_draw():
    window.clear()
    timeline.draw()


@window.event
def on_key_press(symbol, modifiers):
    timeline.on_key_press(symbol)
    if symbol == key.SPACE:
        player.pause() if player.playing else player.play()


@player.event
def on_player_eos():
    timeline.label.text = "Playback finished."


pyglet.app.run()
