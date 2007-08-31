from pyglet.gl import *
from pyglet.window import mouse
from pyglet import media, clock

from wydget import element, event, util, data, layouts, anim
from wydget.widgets.frame import Frame
from wydget.widgets.label import Image, Label
from wydget.widgets.button import Button

class Movie(element.Element):
    name='movie'
    def __init__(self, parent, file=None, source=None, playing=False,
            x=0, y=0, z=0, width=None, height=None, scale=True, **kw):
        self.parent = parent
        self.scale = scale

        if file is not None:
            source = media.load(file, streaming=True)
        else:
            assert source is not None, 'one of file or source is required'

        self.player = media.Player()

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

        # basic frame
        c = self.control = Frame(self, bgcolor=(1, 1, 1, .5),
            is_visible=False, width='100%', height=64)
        c.play = Image(c, data.load_gui_image('media-play.png'),
            classes=('-play-button',), is_visible=not playing)
        c.anim = None

        c.range = Image(c, data.load_gui_image('media-range.png'))

        c.time = Label(c, '00:00', font_size=20)
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

        # make sure we get at least one frame to display
        self.player.queue(source)
        clock.schedule(self.update)
        self.playing = playing
        if playing:
            self.player.play()

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
        self.control.pause.setVisible(True)
        self.control.play.setVisible(False)
        self.playing = True

    def render(self, rect):
        # XXX handle scaling / clipping properly
        if self.player.texture:
            self.player.texture.blit(rect.x, rect.y, width=rect.width,
                height=rect.height)

       # self.video_x, self.video_y,
       #     width=self.video_width, height=self.video_height)

        #image = self.video.texture
        #if self.scale:
        #    glPushMatrix()
        #    x = float(self.width) / image.width
        #    y = float(self.height) / image.height
        #    s = min(x, y)
        #    w = int(image.width * s)
        #    h = int(image.height * s)
        #    glTranslatef(self.width//2 - w//2, self.height//2 - h//2, 0)
        #    glScalef(s, s, 1)
        #image.blit(0, 0, 0)
        #if self.scale:
        #    glPopMatrix()


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

