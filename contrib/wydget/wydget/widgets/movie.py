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
        c.range = Image(f, data.load_gui_image('media-range.png'))
        c.time = Label(f, '00:00', font_size=20)
        c.anim = None

        # current position over the top
        c.position = Image(self, data.load_gui_image('media-position.png'),
            classes=('-position',))
        c.position.range = c.range

        # make sure we get at least one frame to display
        self.player.queue(source)
        clock.schedule(self.update)
        self.playing = False
        if playing:
            self.play()

    def resize(self):
        if not super(Movie, self).resize(): return False
        p = self.control.position
        p.y = (self.control.range.y - p.height // 2)
        return True

    def update(self, dt):
        self.player.dispatch_events()

    def pause(self):
        if not self.playing: return
        clock.unschedule(self.time_update)
        self.player.pause()
        self.control.play.setVisible(True)
        self.control.pause.setVisible(False)
        self.playing = False

    def play(self):
        if self.playing: return
        clock.schedule(self.time_update)
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

       # self.video_x, self.video_y,
       #     width=self.video_width, height=self.video_height)

        #image = self.video.texture
        #if self.scale:
        #    glPushMatrix()
        #    glTranslatef(self.width//2 - w//2, self.height//2 - h//2, 0)
        #    glScalef(s, s, 1)
        #image.blit(0, 0, 0)
        #if self.scale:
        #    glPopMatrix()

    def on_eos(self):
        self.pause()
        self.player.seek(0)
        self.control.position.x = self.control.range.x
        self.control.time.text = '00:00'
        self.getGUI().dispatch_event(self, 'on_eos')

    def time_update(self, ts):
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
        p *= self.control.range.width
        self.control.position.x = self.control.range.x + int(p)

    def delete(self):
        clock.unschedule(self.update)
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
    rx = widget.range.x
    rw = widget.range.width
    widget.x = max(rx, min(rx + rw, widget.x + dx))
    movie = widget.getParent('movie')
    p = float(widget.x - rx) / rw
    movie.player.seek(p * movie.player.source.duration)
    return event.EVENT_HANDLED

