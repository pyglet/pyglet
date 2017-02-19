from pyglet.gl import *
from pyglet.window import mouse
from pyglet import media, clock

from wydget import element, event, util, data, layouts, anim
from wydget.widgets.frame import Frame
from wydget.widgets.label import Image, Label
from wydget.widgets.button import Button

class Movie(Frame):
    name='movie'
    def __init__(self, parent, file=None, source=None, playing=False,
            x=0, y=0, z=0, width=None, height=None, scale=True, **kw):
        self.parent = parent
        self.scale = scale

        if file is not None:
            source = self.source = media.load(file, streaming=True)
        else:
            assert source is not None, 'one of file or source is required'

        self.player = media.Player()
        self.player.eos_action = self.player.EOS_PAUSE
        self.player.on_eos = self.on_eos

        # poke at the video format
        if not source.video_format:
            raise ValueError("Movie file doesn't contain video")
        video_format = source.video_format
        if width is None:
            width = video_format.width
            if video_format.sample_aspect > 1:
                width *= video_format.sample_aspect
        if height is None:
            height = video_format.height
            if video_format.sample_aspect < 1:
                height /= video_format.sample_aspect

        super(Movie, self).__init__(parent, x, y, z, width, height, **kw)

        # control frame top-level
        c = self.control = Frame(self, bgcolor=(1, 1, 1, .5),
            is_visible=False, width='100%', height=64)

        # controls underlay
        f = Frame(c, is_transparent=True, width='100%', height='100%')
        f.layout = layouts.Horizontal(f, valign='center', halign='center',
            padding=10)
        c.play = Image(f, data.load_gui_image('media-play.png'),
            classes=('-play-button',), is_visible=not playing)
        c.pause = Image(f, data.load_gui_image('media-pause.png'),
            bgcolor=None, classes=('-pause-button',), is_visible=playing)
        fi = Frame(f, is_transparent=True)
        c.range = Image(fi, data.load_gui_image('media-range.png'))
        im = data.load_gui_image('media-position.png')
        c.position = Image(fi, im, x=0, y=-2, classes=('-position',))
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

        if self.control is None:
            # the player update may have resulted in this element being
            # culled
            return

        if not self.control.isVisible():
            return
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

    def pause(self):
        if not self.playing: return
        clock.unschedule(self.update)
        self.player.pause()
        self.control.play.setVisible(True)
        self.control.pause.setVisible(False)
        self.playing = False

    def play(self):
        if self.playing: return
        clock.schedule(self.update)
        self.player.play()
        self.control.play.setVisible(False)
        self.control.pause.setVisible(True)
        self.playing = True

    def render(self, rect):
        t = self.player.texture
        if not t: return
        x = float(self.width) / t.width
        y = float(self.height) / t.height
        s = min(x, y)
        w = int(t.width * s)
        h = int(t.height * s)
        x = rect.x
        y = rect.y
        if w < self.width: x += self.width//2 - w//2
        if h < self.height: y += self.height//2 - h//2
        t.blit(x, y, width=w, height=h)

    def on_eos(self):
        self.player.seek(0)
        self.pause()
        self.control.position.x = 0
        self.control.time.text = '00:00'
        self.getGUI().dispatch_event(self, 'on_eos')

    def delete(self):
        self.pause()
        if self.control.anim is not None:
            self.control.anim.cancel()
        self.control = None
        super(Movie, self).delete()


@event.default('movie')
def on_element_enter(widget, *args):
    widget.control.setVisible(True)
    widget.control.anim = anim.Delayed(widget.control.setVisible, False,
        delay=5)
    return event.EVENT_HANDLED

@event.default('movie')
def on_mouse_motion(widget, *args):
    if widget.control.anim is not None:
        widget.control.anim.cancel()
    widget.control.setVisible(True)
    widget.control.anim = anim.Delayed(widget.control.setVisible, False,
        delay=5)
    return event.EVENT_HANDLED

@event.default('movie')
def on_element_leave(widget, *args):
    widget.control.setVisible(False)
    if widget.control.anim is not None:
        widget.control.anim.cancel()
    return event.EVENT_HANDLED

@event.default('movie .-play-button')
def on_click(widget, x, y, buttons, modifiers, click_count):
    if not buttons & mouse.LEFT: return event.EVENT_UNHANDLED
    widget.getParent('movie').play()
    return event.EVENT_HANDLED

@event.default('movie .-pause-button')
def on_click(widget, x, y, buttons, modifiers, click_count):
    if not buttons & mouse.LEFT: return event.EVENT_UNHANDLED
    widget.getParent('movie').pause()
    return event.EVENT_HANDLED

@event.default('movie .-position')
def on_mouse_press(widget, x, y, buttons, modifiers):
    if not buttons & mouse.LEFT: return event.EVENT_UNHANDLED
    widget.getParent('movie').pause()
    return event.EVENT_HANDLED

@event.default('movie .-position')
def on_mouse_release(widget, x, y, buttons, modifiers):
    if not buttons & mouse.LEFT: return event.EVENT_UNHANDLED
    widget.getParent('movie').play()
    return event.EVENT_HANDLED

@event.default('movie .-position')
def on_drag(widget, x, y, dx, dy, buttons, modifiers):
    if not buttons & mouse.LEFT: return event.EVENT_UNHANDLED
    movie = widget.getParent('movie')
    rw = movie.control.range.width
    widget.x = max(0, min(rw, widget.x + dx))
    p = float(widget.x) / rw
    movie.player.seek(p * movie.player.source.duration)
    return event.EVENT_HANDLED

