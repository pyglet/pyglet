from pyglet.gl import *

from wydget import element, event, data, util
from wydget.widgets.button import Button, RepeaterButton

class SliderCommon(element.Element):
    slider_size = 16

    def _commonInit(self, pixel_size):
        self.range = self.maximum - self.minimum
        self.scroll_pixel_range = pixel_size - (self.button_size * 2)
        self.bar_pixels = int(max(2, self.scroll_pixel_range / (self.range+1)))
        self.bar_pixel_range = self.scroll_pixel_range - self.bar_pixels

    def _barPosition(self):
        pos = (self.current / float(self.range)) * self.bar_pixel_range
        return  pos

    def setValue(self, value):
        self.current = max(self.minimum, min(self.maximum, value))

    def setCurrent(self, new):
        self.current = max(self.minimum, min(self.maximum, new))
        self.getGUI().dispatch_event(self, 'on_change', self.current)

    def moveToMaximum(self):
        self.setCurrent(self.current + self.step)

    def moveToMinimum(self):
        self.setCurrent(self.current - self.step)

    def moveBar(self, move):
        px = self._barPosition() + move
        self.setCurrent(px * float(self.range) / self.bar_pixel_range)

class VerticalSlider(SliderCommon):
    name='vslider'
    def __init__(self, parent, minimum, maximum, current, step=1,
            x=0, y=0, z=0, width=SliderCommon.slider_size,
            height=None, **kw):

        self.minimum = util.parse_value(minimum, 0)
        self.maximum = util.parse_value(maximum, 0)
        self.current = util.parse_value(current, 0)
        self.step = util.parse_value(step, 0)

        if height is None: height = parent.height

        super(VerticalSlider, self).__init__(parent, x, y, z, width, height,
            **kw)

        self.button_size = bs = self.width

        # do this after the call to super to allow it to set the parent etc.
        self.children = [
            ArrowButtonDown(self, classes=('-repeater-button-min',)),
            ArrowButtonUp(self, y=self.height-bs,
                classes=('-repeater-button-max',)),
        ]

        self._commonInit(self.height)

    def render(self, rect):
        # XXX use view clip
        glPushAttrib(GL_CURRENT_BIT)

        r = util.Rect(0, 0, self.width, self.height).intersect(rect)
        if r:
            glColor4f(.7, .7, .7, 1)
            glRectf(r.x, r.y, r.x+r.width, r.y+r.height)

        bottom = self._barPosition()
        bh = self.button_size
        r = util.Rect(0, bottom+bh, self.width, self.bar_pixels)
        r = r.intersect(rect)
        if r:
            glColor4f(.3, .3, .3, 1)
            glRectf(r.x, r.y, r.x+r.width, r.y+r.height)
        glPopAttrib()

@event.default('vslider')
def on_mouse_press(self, x, y, buttons, modifiers):
    x, y = self.calculateRelativeCoords(x, y)
    bottom = self._barPosition()
    y -= self.button_size   # XXX actually, arrow height
    m = self.bar_pixels / float(self.scroll_pixel_range)
    m *= (self.maximum - self.minimum)
    if y > int(bottom + self.bar_pixels):
        self.moveBar(self.current + self.bar_pixels)
    elif y < int(bottom):
        self.moveBar(self.current - self.bar_pixels)
    return event.EVENT_HANDLED

@event.default('vslider')
def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
    self.moveBar(dy)
    return event.EVENT_HANDLED

@event.default('vslider')
def on_mouse_scroll(self, x, y, dx, dy):
    if dy: self.moveBar(dy)
    elif dx: self.moveBar(dx)
    return event.EVENT_HANDLED

@event.default('.-repeater-button-max')
def on_click(widget, *args):
    widget.parent.moveToMaximum()
    return event.EVENT_HANDLED

@event.default('.-repeater-button-min')
def on_click(widget, *args):
    widget.parent.moveToMinimum()
    return event.EVENT_HANDLED

class HorizontalSlider(SliderCommon):
    name='hslider'
    def __init__(self, parent, minimum, maximum, current, step=1,
            x=0, y=0, z=0, width=None, height=SliderCommon.slider_size, **kw):

        self.minimum = util.parse_value(minimum, 0)
        self.maximum = util.parse_value(maximum, 0)
        self.current = util.parse_value(current, 0)
        self.step = util.parse_value(step, 0)

        if width is None: width = parent.width

        super(HorizontalSlider, self).__init__(parent, x, y, z, width, height,
            **kw)

        print 'post init', height, self

        self.button_size = bs = self.height

        # do this after the call to super to allow it to set the parent etc.
        self.children = [
            ArrowButtonLeft(self, classes=('-repeater-button-min',)),
            ArrowButtonRight(self, x=self.width-bs, 
                classes=('-repeater-button-max',)),
        ]

        self._commonInit(self.width)

    def render(self, rect):
        glPushAttrib(GL_CURRENT_BIT)
        r = util.Rect(0, 0, self.width, self.height).intersect(rect)
        if r:
            glColor4f(.7, .7, .7, 1)
            glRectf(r.x, r.y, r.x+r.width, r.y+r.height)
        bottom = self._barPosition()
        bw = self.button_size
        r = util.Rect(bw + bottom, 0, self.bar_pixels, self.height)
        r = r.intersect(rect)
        if r:
            glColor4f(.3, .3, .3, 1)
            glRectf(r.x, r.y, r.x+r.width, r.y+r.height)
        glPopAttrib()

@event.default('hslider')
def on_mouse_press(self, x, y, buttons, modifiers):
    x, y = self.calculateRelativeCoords(x, y)
    bottom = self._barPosition()
    x -= self.button_size       # XXX actually, arrow width
    if x > int(bottom + self.bar_pixels):
        self.moveBar(self.current + self.bar_pixels)
    if x < int(bottom):
        self.moveBar(self.current - self.bar_pixels)
    return event.EVENT_HANDLED

@event.default('hslider')
def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
    self.moveBar(dx)
    return event.EVENT_HANDLED

@event.default('hslider')
def on_mouse_scroll(self, x, y, dx, dy):
    if dy: self.moveBar(dy)
    elif dx: self.moveBar(dx)
    return event.EVENT_HANDLED

class ArrowButton(RepeaterButton):
    def __init__(self, parent, **kw):
        super(ArrowButton, self).__init__(parent, image=self.arrow, **kw)

    def get_arrow(self):
        if self.image_file not in self.__dict__:
            im = data.load_gui_image(self.image_file)
            self.__dict__[self.image_file] = im
        return self.__dict__[self.image_file]
    arrow = property(get_arrow)

class ArrowButtonUp(ArrowButton):
    image_file = 'slider-arrow-up.png'

class ArrowButtonDown(ArrowButton):
    image_file = 'slider-arrow-down.png'

class ArrowButtonLeft(ArrowButton):
    image_file = 'slider-arrow-left.png'

class ArrowButtonRight(ArrowButton):
    image_file = 'slider-arrow-right.png'

