from pyglet.gl import *

from wydget import element, event, data, util
from wydget.widgets.button import Button, RepeaterButton

class SliderCommon(element.Element):
    slider_size = 16


    def _barPosition(self):
        pos = (self.current / float(self.range)) * self.bar_pixel_range
        return  pos

    def setValue(self, value):
        self.current = max(self.minimum, min(self.maximum, value))

    def changeCurrent(self, new):
        self.current = max(self.minimum, min(self.maximum, new))
        self.positionBar()
        self.getGUI().dispatch_event(self, 'on_change', self.current)

    def stepToMaximum(self):
        self.changeCurrent(self.current + self.step)

    def stepToMinimum(self):
        self.changeCurrent(self.current - self.step)

class VerticalSlider(SliderCommon):
    name='vslider'
    def __init__(self, parent, minimum, maximum, current, step=1,
            x=0, y=0, z=0, width=SliderCommon.slider_size, arrows=True,
            height=None, bgcolor=(.7, .7, .7, 1), **kw):

        self.minimum = util.parse_value(minimum, 0)
        self.maximum = util.parse_value(maximum, 0)
        self.current = util.parse_value(current, 0)
        self.step = util.parse_value(step, 0)

        if height is None: height = parent.height

        super(VerticalSlider, self).__init__(parent, x, y, z, width, height,
            bgcolor=bgcolor, **kw)

        assert self.height > 32, 'Slider is too small (%s) to be useful'%self.height

        # assume buttons are same height
        bh = ArrowButtonUp.get_arrow().height

        # only have buttons if there's enough room (two buttons plus
        # scrolling room)
        self.have_buttons = self.height > (bh * 2 + 32)
        if self.have_buttons:
            # do this after the call to super to allow it to set the parent etc.
            ArrowButtonDown(self, classes=('-repeater-button-min',)),
            ArrowButtonUp(self, y=self.height-bh,
                    classes=('-repeater-button-max',)),

        # add slider bar
        range = self.maximum - self.minimum
        height = int(max(self.slider_size, self.inner_rect.height / (range+1)))
        width = self.slider_size
        self.bar = SliderBar(self, 'y', 0, 0, width, height)
        self.positionBar()

    def get_inner_rect(self):
        if self.have_buttons:
            bh = ArrowButtonLeft.get_arrow().height
            return util.Rect(0, bh, self.width, self.height - bh*2)
        else:
            return util.Rect(0, 0, self.width, self.height)
    inner_rect = property(get_inner_rect)

    def positionBar(self):
        ir = self.inner_rect
        h = ir.height - self.bar.height
        range = self.maximum - self.minimum
        self.bar.y = ir.y + int(self.current / float(range) * h)

@event.default('vslider')
def on_mouse_press(self, x, y, buttons, modifiers):
    x, y = self.calculateRelativeCoords(x, y)
    r = self.bar.rect
    if y < r.y: self.bar.moveY(-r.height)
    elif y > r.top: self.bar.moveY(r.height)
    return event.EVENT_HANDLED

@event.default('vslider')
def on_mouse_scroll(self, x, y, dx, dy):
    self.moveY(dy)
    return event.EVENT_HANDLED


@event.default('.-repeater-button-max')
def on_click(widget, *args):
    widget.parent.stepToMaximum()
    return event.EVENT_HANDLED

@event.default('.-repeater-button-min')
def on_click(widget, *args):
    widget.parent.stepToMinimum()
    return event.EVENT_HANDLED

class HorizontalSlider(SliderCommon):
    name='hslider'
    def __init__(self, parent, minimum, maximum, current, step=1,
            x=0, y=0, z=0, width=None, height=SliderCommon.slider_size,
            bgcolor=(.7, .7, .7, 1), **kw):

        self.minimum = util.parse_value(minimum, 0)
        self.maximum = util.parse_value(maximum, 0)
        self.current = util.parse_value(current, 0)
        self.step = util.parse_value(step, 0)

        if width is None: width = parent.width

        super(HorizontalSlider, self).__init__(parent, x, y, z, width, height,
            bgcolor=bgcolor, **kw)

        # assume buttons are same width
        bw = ArrowButtonLeft.get_arrow().width

        # only have buttons if there's enough room (two buttons plus
        # scrolling room)
        self.have_buttons = self.width > (bw * 2 + 32)
        if self.have_buttons:
            # do this after the call to super to allow it to set the parent etc.
            ArrowButtonLeft(self, classes=('-repeater-button-min',)),
            ArrowButtonRight(self, x=self.width-bw,
                classes=('-repeater-button-max',)),

        range = self.maximum - self.minimum
        width = int(max(self.slider_size, self.inner_rect.width / (range+1)))
        height = self.slider_size
        self.bar = SliderBar(self, 'x', 0, 0, width, height)
        self.positionBar()

    def get_inner_rect(self):
        if self.have_buttons:
            bw = ArrowButtonLeft.get_arrow().width
            return util.Rect(bw, 0, self.width - bw*2, self.height)
        else:
            return util.Rect(0, 0, self.width, self.height)
    inner_rect = property(get_inner_rect)

    def positionBar(self):
        ir = self.inner_rect
        w = ir.width - self.bar.width
        range = self.maximum - self.minimum
        self.bar.x = ir.x + int(self.current / float(range) * w)


@event.default('hslider')
def on_mouse_press(self, x, y, buttons, modifiers):
    x, y = self.calculateRelativeCoords(x, y)
    r = self.bar.rect
    if x < r.x: self.bar.moveX(-r.width)
    elif x > r.right: self.bar.moveX(r.width)
    return event.EVENT_HANDLED

@event.default('hslider')
def on_mouse_scroll(self, x, y, dx, dy):
    if dx: self.moveX(dx)
    else: self.moveX(dy)
    return event.EVENT_HANDLED


class SliderBar(element.Element):
    name = 'slider-bar'
    def __init__(self, parent, axis, x, y, width, height,
            bgcolor=(.3, .3, .3, 1), **kw):
        self.axis = axis
        super(SliderBar, self).__init__(parent, x, y, 0, width, height,
            bgcolor=bgcolor, **kw)

    def moveY(self, move):
        self.y += move
        p = self.parent
        ir = p.inner_rect
        r = self.rect
        if r.y < ir.y: r.y = p.y
        elif r.top > ir.top: r.top = ir.top
        range = p.maximum - p.minimum
        p.changeCurrent((self.y - ir.y) * float(range) / (ir.height - self.height))

    def moveX(self, move):
        self.x += move
        p = self.parent
        ir = p.inner_rect
        r = self.rect
        if r.x < ir.x: r.x = p.x
        elif r.right > ir.right: r.right = ir.right
        range = p.maximum - p.minimum
        p.changeCurrent((self.x - ir.x) * float(range) / (ir.width - self.width))

@event.default('slider-bar')
def on_mouse_drag(widget, x, y, dx, dy, buttons, modifiers):
    if widget.axis == 'x': widget.moveX(dx)
    else: widget.moveY(dy)
    return event.EVENT_HANDLED


class ArrowButton(RepeaterButton):
    def __init__(self, parent, **kw):
        super(ArrowButton, self).__init__(parent, image=self.arrow, **kw)

    @classmethod
    def get_arrow(cls):
        if not hasattr(cls, 'image_object'):
            cls.image_object = data.load_gui_image(cls.image_file)
        return cls.image_object
    def _get_arrow(self): return self.get_arrow()
    arrow = property(_get_arrow)

class ArrowButtonUp(ArrowButton):
    image_file = 'slider-arrow-up.png'

class ArrowButtonDown(ArrowButton):
    image_file = 'slider-arrow-down.png'

class ArrowButtonLeft(ArrowButton):
    image_file = 'slider-arrow-left.png'

class ArrowButtonRight(ArrowButton):
    image_file = 'slider-arrow-right.png'

