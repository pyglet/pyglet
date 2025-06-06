"""Plays the audio / video files listed as arguments.

Key Controls Available:
    Space - Play/Pause
    ESC - Close
    Left - Seek to beginning of source
    Right - Next Source
"""
from __future__ import annotations

import warnings
import weakref

import os as _os
from functools import partial

import pyglet

pyglet.options.debug_media = False

from pyglet.media.exceptions import MediaException

from concurrent.futures import ProcessPoolExecutor as _ProcessPoolExecutor

from pyglet.event import EventDispatcher as _EventDispatcher
from pyglet.window import key



class _Dialog(_EventDispatcher):
    """Dialog base class

    This base class sets up a ProcessPoolExecutor with a single
    background Process. This allows the Dialog to display in
    the background without blocking or interfering with the main
    application Process. This also limits to a single open Dialog
    at a time.
    """

    executor = _ProcessPoolExecutor(max_workers=1)
    _dialog = None

    @staticmethod
    def _open_dialog(dialog):
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        return dialog.show()

    def open(self):
        future = self.executor.submit(self._open_dialog, self._dialog)
        future.add_done_callback(self._dispatch_event)

    def _dispatch_event(self, future):
        raise NotImplementedError


class FileOpenDialog(_Dialog):
    def __init__(self, title="Open File", initial_dir=_os.path.curdir, filetypes=None, multiple=False):
        """
        :Parameters:
            `title` : str
                The Dialog Window name. Defaults to "Open File".
            `initial_dir` : str
                The directory to start in.
            `filetypes` : list of tuple
                An optional list of tuples containing (name, extension) to filter by.
                If none are given, all files will be shown and selectable.
                For example: `[("PNG", ".png"), ("24-bit Bitmap", ".bmp")]`
            `multiple` : bool
                True if multiple files can be selected. Defaults to False.
        """
        from tkinter import filedialog
        self._dialog = filedialog.Open(title=title,
                                       initialdir=initial_dir,
                                       filetypes=filetypes or (),
                                       multiple=multiple)

    def _dispatch_event(self, future):
        pyglet.app.platform_event_loop.post_event(self, "on_dialog_open", future.result())

    def on_dialog_open(self, filenames):
        """Event for filename choices"""


FileOpenDialog.register_event_type('on_dialog_open')


class Control(pyglet.event.EventDispatcher):

    def __init__(self, parent):
        super().__init__()
        self._x = 0
        self._y = 0
        self._width = 10
        self._height = 10
        self.batch = parent.batch
        self.parent = weakref.proxy(parent)

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self._update_control()

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
        self._update_control()

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._width = value
        self._update_control()

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._height = value
        self._update_control()

    def _update_control(self):
        raise NotImplementedError()

    def hit_test(self, x, y):
        return (self.x < x < self.x + self.width and
                self.y < y < self.y + self.height)

    def capture_events(self):
        self.parent.window.push_handlers(self)

    def release_events(self):
        self.parent.window.remove_handlers(self)


class Button(Control):
    def __init__(self, parent):
        super().__init__(parent)
        self._charged = False
        self.rect = pyglet.shapes.Rectangle(self.x, self.y, self.width, self.height, color=(255, 255, 255, 255), batch=self.batch)

    @property
    def charged(self) -> bool:
        return self._charged

    @charged.setter
    def charged(self, value: bool) -> None:
        self._charged = value
        self._update_control()

    def _update_control(self):
        if self._charged is True:
            self.rect.color = (255, 255, 255)
        else:
            self.rect.color = (128, 128, 128)

        self.rect.width = self.width
        self.rect.height = self.height
        self.rect.position = (self.x, self.y)

    def on_mouse_press(self, x, y, button, modifiers):
        self.capture_events()
        self.charged = True

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.charged = self.hit_test(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        self.release_events()
        if self.hit_test(x, y):
            self.dispatch_event('on_press')
        self.charged = False


Button.register_event_type('on_press')


class TextButton(Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._text = pyglet.text.Label('.', anchor_x='center', anchor_y='center', batch=self.batch)

    def _update_control(self) -> None:
        super()._update_control()
        self._text.position = (self.x + self.width // 2, self.y + self.height // 2, 0)

    @property
    def text(self) -> str:
        return self._text.text

    @text.setter
    def text(self, text: str) -> None:
        self._text.text = text

class Slider(Control):
    THUMB_WIDTH = 6
    THUMB_HEIGHT = 10
    GROOVE_HEIGHT = 2
    RESPONSIVNESS = 0.3

    def __init__(self, parent):
        super().__init__(parent)
        self.seek_value = None
        self.min = 0
        self.max = 1
        self.value = 0.0
        self.groove_rect = pyglet.shapes.Rectangle(self.x, self.y, self.width, self.height, color=(255, 0, 0, 255), batch=self.batch)
        self.thumb_rect = pyglet.shapes.Rectangle(self.x, self.y, self.width, self.height, color=(255, 0, 0, 255), batch=self.batch)

    def update_timestamp(self, value: float):
        self.value = value
        self._update_rects()

    def _update_control(self):
        self._update_rects()

    def _get_groove(self):
        center_y = self.y + self.height / 2
        return self.x, center_y - self.GROOVE_HEIGHT // 2, self.width, self.GROOVE_HEIGHT

    def _get_thumb(self):
        center_y = self.y + self.height // 2
        pos = self.x + self.value * self.width // (self.max - self.min)
        return pos - self.THUMB_WIDTH // 2, center_y - self.THUMB_HEIGHT // 2, self.THUMB_WIDTH, self.THUMB_HEIGHT

    def _update_rects(self):
        gx, gy, gw, gh = self._get_groove()
        self.groove_rect.position = (gx, gy)
        self.groove_rect.width = gw
        self.groove_rect.height = gh

        tx, ty, tw, th = self._get_thumb()
        self.thumb_rect.position = (tx, ty)
        self.thumb_rect.width = tw
        self.thumb_rect.height = th

    def coordinate_to_value(self, x):
        value = float(x - self.x) / self.width * (self.max - self.min) + self.min
        return value

    def on_mouse_press(self, x, y, button, modifiers):
        value = self.coordinate_to_value(x)
        self.capture_events()
        self.dispatch_event('on_begin_scroll')
        self.dispatch_event('on_change', value)
        pyglet.clock.schedule_once(self.seek_request, self.RESPONSIVNESS)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        # On some platforms, on_mouse_drag is triggered with a high frequency.
        # Seeking takes some time (~200ms). Asking for a seek at every
        # on_mouse_drag event would starve the event loop.
        # Instead we only record the last mouse position and we
        # schedule seek_request to dispatch the on_change event in the future.
        # This will allow subsequent on_mouse_drag to change the seek_value
        # without triggering yet the on_change event.
        value = min(max(self.coordinate_to_value(x), self.min), self.max)
        if self.seek_value is None:
            # We have processed the last recorded mouse position.
            # We re-schedule seek_request
            pyglet.clock.schedule_once(self.seek_request, self.RESPONSIVNESS)
        self.seek_value = value

    def on_mouse_release(self, x, y, button, modifiers):
        self.release_events()
        self.dispatch_event('on_end_scroll')
        self.seek_value = None

    def seek_request(self, dt):
        if self.seek_value is not None:
            self.dispatch_event('on_change', self.seek_value)
            self.seek_value = None


Slider.register_event_type('on_begin_scroll')
Slider.register_event_type('on_end_scroll')
Slider.register_event_type('on_change')


class MediaPlayer:
    GUI_WIDTH = 500
    GUI_HEIGHT = 40
    GUI_PADDING = 4
    GUI_BUTTON_HEIGHT = 16

    def __init__(self, window: pyglet.window.Window):
        self.window = window

        self.batch = pyglet.graphics.Batch()

        try:
            self.player = pyglet.media.VideoPlayer(self.batch)
            print("FFmpeg detected, video playback enabled.")
        except MediaException:
            warnings.warn('Could not create a video player, ensure FFmpeg is installed and detected.')
            self.player = pyglet.media.AudioPlayer()

        # Register this class to get callbacks from player.
        self.player.push_handlers(self)
        self._player_playing = False

        self.slider = Slider(self)
        self.slider.push_handlers(self)
        self.slider.x = self.GUI_PADDING
        self.slider.y = self.GUI_PADDING * 2 + self.GUI_BUTTON_HEIGHT

        self.open_button = TextButton(self)
        self.open_button.text = 'Open Media'
        self.open_button.x = self.GUI_PADDING
        self.open_button.y = self.GUI_PADDING
        self.open_button.height = self.GUI_BUTTON_HEIGHT
        self.open_button.width = 100

        audio_types = [("Common Audio Files", "*.wav *.mp3")]
        additional_types = []
        if isinstance(self.player, pyglet.media.VideoPlayer):
            audio_types = [("Audio Files", "*.wav *.mp3 *.flv *.mov .*ogg")]
            additional_types.append(("Video/Container Files", "*.mp4 *.mkv *.avi"))

        file_types = audio_types + additional_types + [("All Files", "*.*")]
        open_dialog = FileOpenDialog(filetypes=file_types, multiple=True)

        @open_dialog.event
        def on_dialog_open(filenames):
            self.add_tracks(filenames)

        self.open_button.on_press = lambda: open_dialog.open()

        self.play_pause_button = TextButton(self)
        self.play_pause_button.x = self.GUI_PADDING + self.open_button.x + self.open_button.width
        self.play_pause_button.y = self.GUI_PADDING
        self.play_pause_button.height = self.GUI_BUTTON_HEIGHT
        self.play_pause_button.width = 45
        self.play_pause_button.on_press = self.on_play_pause

        self.window_button = TextButton(self)
        self.window_button.x = self.play_pause_button.x + self.play_pause_button.width + self.GUI_PADDING
        self.window_button.y = self.GUI_PADDING
        self.window_button.height = self.GUI_BUTTON_HEIGHT
        self.window_button.width = 90
        self.window_button.text = 'Windowed'
        self.window_button.on_press = lambda: window.set_fullscreen(False)

        self.controls = [
            self.open_button,
            self.slider,
            self.play_pause_button,
            self.window_button,
        ]

        x = self.window_button.x + self.window_button.width + self.GUI_PADDING

        i = 0
        for screen in window.display.get_screens():
            screen_button = TextButton(self)
            screen_button.x = x
            screen_button.y = self.GUI_PADDING
            screen_button.height = self.GUI_BUTTON_HEIGHT
            screen_button.width = 80
            screen_button.text = f'Screen {i + 1}'
            screen_button.on_press = partial(window.set_fullscreen, True, screen=screen)
            self.controls.append(screen_button)
            i += 1
            x += screen_button.width + self.GUI_PADDING

    def play(self):
        self.gui_update_source()
        self.set_default_video_size()
        self.player.play()

    def add_tracks(self, filename_list: list[str]):
        for filename in filename_list:
            media = pyglet.media.load(filename)
            self.player.queue(media)

        self.gui_update_source()
        self.set_default_video_size()

    def on_player_next_source(self):
        self.gui_update_state()
        self.gui_update_source()
        self.set_default_video_size()
        return True

    def on_player_eos(self):
        self.gui_update_state()
        pyglet.clock.schedule_once(self.auto_close, 0.1)
        return True

    def gui_update_source(self):
        if self.player.source:
            source = self.player.source
            self.slider.min = 0.
            self.slider.max = source.duration
        self.gui_update_state()

    def gui_update_state(self):
        if self.player.playing:
            self.play_pause_button.text = 'Pause'
        else:
            self.play_pause_button.text = 'Play'

    def get_video_size(self):
        if not self.player.source or not self.player.source.video_format:
            return 0, 0
        video_format = self.player.source.video_format
        width = video_format.width
        height = video_format.height
        if video_format.sample_aspect > 1:
            width *= video_format.sample_aspect
        elif video_format.sample_aspect < 1:
            height /= video_format.sample_aspect
        return width, height

    def set_default_video_size(self):
        """Make the window size just big enough to show the current
        video and the GUI."""
        if self.window.fullscreen:
            self.window.set_fullscreen(False)
        width = self.GUI_WIDTH
        height = self.GUI_HEIGHT
        video_width, video_height = self.get_video_size()
        width = max(width, video_width)
        height += video_height
        self.window.set_size(int(width), int(height))

    def on_resize(self, width, height):
        """Position and size video image."""
        self.slider.width = width - self.GUI_PADDING * 2

        height -= self.GUI_HEIGHT
        if height <= 0:
            return

        video_width, video_height = self.get_video_size()
        if video_width == 0 or video_height == 0:
            return
        display_aspect = width / float(height)
        video_aspect = video_width / float(video_height)
        if video_aspect > display_aspect:
            self.video_width = width
            self.video_height = width / video_aspect
        else:
            self.video_height = height
            self.video_width = height * video_aspect

        video_x = (width - self.video_width) / 2
        video_y = (height - self.video_height) / 2 + self.GUI_HEIGHT

        self.player.position = (video_x, video_y)
        self.player.width = self.video_width
        self.player.height = self.video_height

    def on_mouse_press(self, x, y, button, modifiers):
        for control in self.controls:
            if control.hit_test(x, y):
                control.on_mouse_press(x, y, button, modifiers)

    def on_key_press(self, symbol, modifiers):
        if symbol == key.SPACE:
            self.on_play_pause()
        elif symbol == key.ESCAPE:
            self.window.dispatch_event('on_close')
        elif symbol == key.LEFT:
            self.player.seek(0)
        elif symbol == key.RIGHT:
            self.player.next_source()

    def on_close(self):
        self.player.pause()
        self.window.close()

    def auto_close(self, dt):
        self.window.close()

    def on_play_pause(self):
        if self.player.playing:
            self.player.pause()
        else:
            if self.player.time >= self.player.source.duration:
                self.player.seek(0)
            self.player.play()
        self.gui_update_state()

    def on_draw(self):
        self.window.clear()

        self.slider.update_timestamp(self.player.time)

        self.batch.draw()

    def on_begin_scroll(self):
        self._player_playing = self.player.playing
        self.player.pause()

    def on_change(self, value):
        self.player.seek(value)

    def on_end_scroll(self):
        if self._player_playing:
            self.player.play()


def main():
    window = pyglet.window.Window(caption="Media Player", resizable=True, visible=False)

    media_player = MediaPlayer(window)
    window.push_handlers(media_player)

    window.set_visible(True)
    media_player.play()

    pyglet.app.run()

if __name__ == '__main__':
    print(__doc__)
    main()
