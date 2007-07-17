from pyglet.gl import *
from pyglet.window import mouse
from pyglet import media, clock

from wydget import element, event, util, data, layouts
from wydget.widgets.frame import Frame
from wydget.widgets.label import Image, Label
from wydget.widgets.button import Button

class Movie(element.Element):
    name='movie'
    def __init__(self, parent, file=None, medium=None, playing=False,
            x=0, y=0, z=0, width=None, height=None, scale=True, **kw):
        self.parent = parent
        self.scale = scale

        if file is not None:
            medium = self.medium = media.load(file, streaming=True)
        else:
            assert medium is not None, 'one of file or medium is required'
            self.medium = medium

        # Load the medium, determine if it's video and/or audio
        if not medium.has_video:
            raise ValueError("Movie file doesn't contain video")
        self.video = medium.get_video()
        if width is None:
            width = self.video.width
        if height is None:
            height = self.video.height

        super(Movie, self).__init__(parent, x, y, z, width, height, **kw)

        # basic frame
        c = self.control = Frame(self, bgcolor=(1, 1, 1, .5),
            is_visible=False, width='100%', height=64)
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

        self.video.play()
        if not playing:
            self.video.pause()
        else:
            clock.schedule(self.time_update)

    def render(self, rect):
        image = self.video.texture
        if self.scale:
            glPushMatrix()
            x = float(self.width) / image.width
            y = float(self.height) / image.height
            s = min(x, y)
            w = int(image.width * s)
            h = int(image.height * s)
            glTranslatef(self.width//2 - w//2, self.height//2 - h//2, 0)
            glScalef(s, s, 1)
        image.blit(0, 0, 0)
        if self.scale:
            glPopMatrix()

        '''
        XXX get_region currently does the WRONG THING re: tex coords
        r = self.rect
        if rect != r:
            image = image.get_region(rect.x, rect.y, rect.width, rect.height)
        image.blit(rect.x, rect.y, 0)
        '''

    def time_update(self, ts):
        if not self.control.isVisible(): return
        t = self.video.time

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
        super(Movie, self).delete()
        self.video.stop()


@event.default('movie')
def on_element_enter(widget, x, y):
    widget.control.setVisible(True)
    return event.EVENT_HANDLED

#@event.default('movie')
#def on_mouse_move(widget, x, y):
#    widget.control.setVisible(True)
#    return event.EVENT_HANDLED

@event.default('movie')
def on_element_leave(widget, x, y):
    widget.control.setVisible(False)
    return event.EVENT_HANDLED

@event.default('movie .-play-button', 'on_click')
def on_click_play(widget, x, y, buttons, modifiers, click_count):
    if not buttons & mouse.LEFT: return event.EVENT_UNHANDLED
    video = widget.parent.parent.video
    if video.playing: return event.EVENT_HANDLED
    clock.schedule(widget.parent.parent.time_update)
    video.play()
    widget.setVisible(False)
    widget.parent.pause.setVisible(True)
    return event.EVENT_HANDLED

@event.default('movie .-pause-button', 'on_click')
def on_click_pause(widget, x, y, buttons, modifiers, click_count):
    if not buttons & mouse.LEFT: return event.EVENT_UNHANDLED
    video = widget.parent.parent.video
    if not video.playing: return event.EVENT_HANDLED
    clock.unschedule(widget.parent.parent.time_update)
    video.pause()
    widget.setVisible(False)
    widget.parent.play.setVisible(True)
    return event.EVENT_HANDLED

@event.default('movie .-position', 'on_drag')
def on_drag_position(widget, x, y, dx, dy, buttons, modifiers):
    if not buttons & mouse.LEFT: return event.EVENT_UNHANDLED
    rx = widget.range.x
    rw = widget.range.width
    widget.x = max(rx, min(rx + rw, widget.x + dx))
    movie = widget.parent.parent
    p = float(widget.x - rx) / rw
    movie.video.seek(p * movie.medium.duration)
    return event.EVENT_HANDLED

