import os

from pyglet.gl import *
from pyglet.window import mouse
from pyglet.media import openal

# XXX hack - openal 1.1 code has issues reporting playback time
openal._have_11 = False

from pyglet import media, clock

from wydget import element, event, util, data, layouts
from wydget.widgets.frame import Frame
from wydget.widgets.label import Image, Label
from wydget.widgets.button import Button

class Music(Frame):
    name='music'

    def __init__(self, parent, file=None, medium=None, title=None,
            playing=False, bgcolor=(1, 1, 1, 1), color=(0, 0, 0, 1),
            font_size=20, **kw):
        '''Pass in a filename as "file" or a pyglet Medium as "medium".
        '''
        self.parent = parent

        if file is not None:
            medium = self.medium = media.load(file, streaming=True)
            if title is None:
                # XXX use an id3 lib or similar?
                title = '[title unknown]'
        else:
            assert medium is not None, 'one of file or medium is required'
            self.medium = medium
            title = '[title unknown]'

        # Load the medium, determine if it's audio
        if not medium.has_audio:
            raise ValueError("Medium doesn't contain audio")
        self.audio = medium.get_sound()

        super(Music, self).__init__(parent, bgcolor=bgcolor, **kw)

        # lay it out
        Label(self, title, color=color, bgcolor=bgcolor, padding=2,
            font_size=font_size)

        # basic frame
        c = self.control = Frame(self, width='100%', height=64,
            is_transparent=True)
        c.play = Image(c, data.load_gui_image('media-play.png'),
            classes=('-play-button',), is_visible=not playing)

        c.range = Image(c, data.load_gui_image('media-range.png'))

        c.time = Label(c, '00:00', font_size=20, is_blended=True)
        layouts.Horizontal(c, valign='center', halign='center',
            padding=10).layout()

        c.pause = Image(c, data.load_gui_image('media-pause.png'),
            x=c.play.x, y=c.play.y, bgcolor=None, classes=('-pause-button',),
            is_visible=playing)

        c.position = Image(c, data.load_gui_image('media-position.png'),
            classes=('-position',))
        c.position.range = c.range
        c.position.y = c.range.y - 2
        c.position.x = c.range.x

        layouts.Vertical(self, halign='center').layout()

        self.audio.play()
        if not playing:
            self.audio.pause()
        else:
            clock.schedule(self.time_update)

    def time_update(self, ts):
        if not self.control.isVisible(): return
        t = self.audio.time

        # time display
        s = int(t)
        m = t // 60
        h = m // 60
        m %= 60
        s = s % 60
        if h: text = '%d:%02d:%02d'%(h, m, s)
        else: text = '%02d:%02d'%(m, s)
        if text != self.control.time.text:
            self.control.time.setText(text)

        # slider position
        p = (t/self.medium.duration)
        p *= self.control.range.width
        self.control.position.x = self.control.range.x + int(p)

    def delete(self):
        super(Music, self).delete()
        self.audio.stop()


@event.default('music .-play-button', 'on_click')
def on_click_play(widget, x, y, buttons, modifiers, click_count):
    if not buttons & mouse.LEFT: return event.EVENT_UNHANDLED
    music = widget.getParent('music')
    audio = music.audio
    if audio.playing: return event.EVENT_HANDLED
    clock.schedule(music.time_update)
    audio.play()
    widget.setVisible(False)
    widget.parent.pause.setVisible(True)
    return event.EVENT_HANDLED

@event.default('music .-pause-button', 'on_click')
def on_click_pause(widget, x, y, buttons, modifiers, click_count):
    if not buttons & mouse.LEFT: return event.EVENT_UNHANDLED
    music = widget.getParent('music')
    audio = music.audio
    if not audio.playing: return event.EVENT_HANDLED
    clock.unschedule(music.time_update)
    audio.pause()
    widget.setVisible(False)
    widget.parent.play.setVisible(True)
    return event.EVENT_HANDLED

@event.default('music .-position', 'on_drag')
def on_drag_position(widget, x, y, dx, dy, buttons, modifiers):
    if not buttons & mouse.LEFT: return event.EVENT_UNHANDLED
    rx = widget.range.x
    rw = widget.range.width
    widget.x = max(rx, min(rx + rw, widget.x + dx))
    p = float(widget.x - rx) / rw
    music = widget.getParent('music')
    music.audio.seek(p * music.medium.duration)
    return event.EVENT_HANDLED

