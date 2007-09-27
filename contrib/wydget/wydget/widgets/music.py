import os

from pyglet.gl import *
from pyglet.window import mouse

from pyglet import media, clock

from wydget import element, event, util, data, layouts
from wydget.widgets.frame import Frame
from wydget.widgets.label import Image, Label
from wydget.widgets.button import Button

class Music(Frame):
    name='music'

    def __init__(self, parent, file=None, source=None, title=None,
            playing=False, bgcolor=(1, 1, 1, 1), color=(0, 0, 0, 1),
            font_size=20, **kw):
        '''Pass in a filename as "file" or a pyglet Source as "source".
        '''
        self.parent = parent

        if file is not None:
            source = media.load(file, streaming=True)
        else:
            assert source is not None, 'one of file or source is required'

        self.player = media.Player()

        # poke at the audio format
        if not source.audio_format:
            raise ValueError("File doesn't contain audio")

        super(Music, self).__init__(parent, bgcolor=bgcolor, **kw)

        # lay it out

        # control frame top-level
        c = self.control = Frame(self, width='100%', height=64)

        ft = Frame(c, is_transparent=True, width='100%', height='100%')
        ft.layout = layouts.Vertical(ft)
        Label(ft, title or 'unknown', color=color, bgcolor=bgcolor,
            padding=2, font_size=font_size)

        # controls underlay
        f = Frame(ft, is_transparent=True, width='100%', height='100%')
        f.layout = layouts.Horizontal(f, valign='center', halign='center',
            padding=10)
        c.play = Image(f, data.load_gui_image('media-play.png'),
            classes=('-play-button',), is_visible=not playing)
        c.pause = Image(f, data.load_gui_image('media-pause.png'),
            bgcolor=None, classes=('-pause-button',), is_visible=playing)
        fi = Frame(f, is_transparent=True)
        c.range = Image(fi, data.load_gui_image('media-range.png'))
        c.position = Image(fi, data.load_gui_image('media-position.png'),
            y=-2, classes=('-position',))
        c.time = Label(f, '00:00', font_size=20)
        c.anim = None

        # make sure we get at least one frame to display
        self.player.queue(source)
        clock.schedule(self.update)
        self.playing = False
        if playing:
            self.play()

    def update(self, dt):
        self.player.dispatch_events()

    def pause(self):
        if not self.playing: return
        clock.unschedule(self.time_update)
        self.player.pause()
        self.control.pause.setVisible(False)
        self.control.play.setVisible(True)
        self.playing = False

    def play(self):
        if self.playing: return
        clock.schedule(self.time_update)
        self.player.play()
        self.control.pause.setVisible(True)
        self.control.play.setVisible(False)
        self.playing = True

    def on_eos(self):
        self.player.seek(0)
        self.pause()
        self.control.time.text = '00:00'
        self.getGUI().dispatch_event(self, 'on_eos', self)

    def time_update(self, ts):
        if not self.control.isVisible(): return
        t = self.player.time

        # time display
        s = int(t)
        m = t // 60
        h = m // 60
        m %= 60
        s = s % 60
        if h: text = '%d:%02d:%02d'%(h, m, s)
        else: text = '%02d:%02d'%(m, s)
        if text != self.control.time.text:
            self.control.time.text = text

        # slider position
        p = (t/self.player.source.duration)
        self.control.position.x = int(p * self.control.range.width)

    def delete(self):
        self.pause()
        super(Music, self).delete()


@event.default('music .-play-button')
def on_click(widget, x, y, buttons, modifiers, click_count):
    if not buttons & mouse.LEFT: return event.EVENT_UNHANDLED
    widget.getParent('music').play()
    return event.EVENT_HANDLED

@event.default('music .-pause-button')
def on_click(widget, x, y, buttons, modifiers, click_count):
    if not buttons & mouse.LEFT: return event.EVENT_UNHANDLED
    widget.getParent('music').pause()
    return event.EVENT_HANDLED

@event.default('music .-position')
def on_mouse_press(widget, x, y, buttons, modifiers):
    if not buttons & mouse.LEFT: return event.EVENT_UNHANDLED
    widget.getParent('music').pause()
    return event.EVENT_HANDLED

@event.default('music .-position')
def on_mouse_release(widget, x, y, buttons, modifiers):
    if not buttons & mouse.LEFT: return event.EVENT_UNHANDLED
    widget.getParent('music').play()
    return event.EVENT_HANDLED

@event.default('music .-position')
def on_drag(widget, x, y, dx, dy, buttons, modifiers):
    if not buttons & mouse.LEFT: return event.EVENT_UNHANDLED
    music = widget.getParent('music')
    rw = music.control.range.width
    widget.x = max(0, min(rw, widget.x + dx))
    p = float(widget.x) / rw
    music.player.seek(p * music.player.source.duration)
    return event.EVENT_HANDLED


