from pyglet.gl import *

from wydget import element, event, data, util
from wydget.widgets.button import Button, RepeaterButton
from wydget.widgets.label import Label

class SliderCommon(element.Element):
    slider_size = 16
    def _barPosition(self):
        pos = (self.current / float(self.range)) * self.bar_pixel_range
        return  pos

    def setValue(self, value):
        self.current = self.type(max(self.minimum, min(self.maximum, value)))

    def changeCurrent(self, new):
        self.setValue(new)
        self.positionBar()
        self.getGUI().dispatch_event(self, 'on_change', self.current)
        if self.show_value:
            self.bar.setText(str(self.current))

    def stepToMaximum(self):
        self.changeCurrent(self.current + self.step)

    def stepToMinimum(self):
        self.changeCurrent(self.current - self.step)

class VerticalSlider(SliderCommon):
    '''
    The current value will be of the same type as the minimum value.
    '''
    name='vslider'
    def __init__(self, parent, minimum, maximum, current, step=1,
            bar_size=None, show_value=False, bar_text_color='white',
            bar_color=(.3, .3, .3, 1), x=0, y=0, z=0,
            width=SliderCommon.slider_size, height='100%',
            bgcolor='gray', **kw):

        self.minimum = util.parse_value(minimum, 0)
        self.type = type(self.minimum)
        self.maximum = util.parse_value(maximum, 0)
        self.range = self.maximum - self.minimum
        self.current = util.parse_value(current, 0)
        self.step = util.parse_value(step, 0)
        self.show_value = show_value

        super(VerticalSlider, self).__init__(parent, x, y, z, width, height,
            bgcolor=bgcolor, **kw)

        assert self.height > 32, 'Slider too small (%spx)'%self.height

        # assume buttons are same height
        bh = ArrowButtonUp.get_arrow().height

        # only have buttons if there's enough room (two buttons plus
        # scrolling room)
        self.have_buttons = self.height > (bh * 2 + 32)
        if self.have_buttons:
            # do this after the call to super to allow it to set the parent etc.
            ArrowButtonDown(self, classes=('-repeater-button-min',))
            ArrowButtonUp(self, y=self.height-bh,
                    classes=('-repeater-button-max',))

        # add slider bar
        i_height = self.inner_rect.height
        self.bar_size = util.parse_value(bar_size, i_height)
        if self.bar_size is None:
            self.bar_size = int(max(self.slider_size, i_height /
                (self.range+1)))

        s = show_value and str(self.current) or ' '
        # note: dimensions are funny because the bar is rotated 90 degrees
        self.bar = SliderBar(self, 'y', s, self.width, self.bar_size,
            bgcolor=bar_color, color=bar_text_color)
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
        self.bar.y = ir.y + int(self.current / float(self.range) * h)

@event.default('vslider')
def on_mouse_press(self, x, y, buttons, modifiers):
    x, y = self.calculateRelativeCoords(x, y)
    r = self.bar.rect
    if y < r.y: self.bar.moveY(-r.height)
    elif y > r.top: self.bar.moveY(r.height)
    return event.EVENT_HANDLED

@event.default('vslider')
def on_mouse_scroll(self, x, y, dx, dy):
    if dy: self.changeCurrent(self.current + dy * self.step)
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
    '''
    The current value will be of the same type as the minimum value.
    '''
    name='hslider'
    def __init__(self, parent, minimum, maximum, current, step=1,
            bar_size=None, show_value=False, bar_text_color='white',
            bar_color=(.3, .3, .3, 1), x=0, y=0, z=0, width='100%',
            height=SliderCommon.slider_size, bgcolor='gray', **kw):

        self.minimum = util.parse_value(minimum, 0)
        self.type = type(self.minimum)
        self.maximum = util.parse_value(maximum, 0)
        self.range = self.maximum - self.minimum
        self.current = util.parse_value(current, 0)
        self.step = util.parse_value(step, 0)
        self.show_value = show_value

        super(HorizontalSlider, self).__init__(parent, x, y, z, width, height,
            bgcolor=bgcolor, **kw)

        assert self.width > 32, 'Slider too small (%spx)'%self.width

        # assume buttons are same width
        bw = ArrowButtonLeft.get_arrow().width

        # only have buttons if there's enough room (two buttons plus
        # scrolling room)
        self.have_buttons = self.width > (bw * 2 + 32)
        if self.have_buttons:
            ArrowButtonLeft(self, classes=('-repeater-button-min',)),
            ArrowButtonRight(self, x=self.width-bw,
                classes=('-repeater-button-max',)),

        # slider bar size
        i_width = self.inner_rect.width
        self.bar_size = util.parse_value(bar_size, i_width)
        if self.bar_size is None:
            self.bar_size = int(max(self.slider_size, i_width / (self.range+1)))

        s = show_value and str(self.current) or ' '
        self.bar = SliderBar(self, 'x', s, self.bar_size,
            self.height, bgcolor=bar_color, color=bar_text_color)

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
    if dx: self.changeCurrent(self.current + dx * self.step)
    else: self.changeCurrent(self.current + dy * self.step)
    return event.EVENT_HANDLED


class SliderBar(Label):
    name = 'slider-bar'
    def __init__(self, parent, axis, initial, width, height, **kw):
        self.axis = axis
        rotate = 90 if axis == 'y' else 0
        super(SliderBar, self).__init__(parent, str(initial), width=width,
            height=height, halign='center', rotate=rotate, **kw)

    def moveY(self, move):
        self.setY(self.y + move)

    def setY(self, y):
        self.y = y
        p = self.parent
        ir = p.inner_rect
        r = self.rect
        if r.y < ir.y: r.y = p.y
        elif r.top > ir.top: r.top = ir.top
        range = p.maximum - p.minimum
        p.changeCurrent((self.y - ir.y) * float(range) / (ir.height - self.height))

    def moveX(self, move):
        self.setX(self.x + move)

    def setX(self, x):
        self.x = x
        p = self.parent
        ir = p.inner_rect
        r = self.rect
        if r.x < ir.x: r.x = p.x
        elif r.right > ir.right: r.right = ir.right
        range = p.maximum - p.minimum
        p.changeCurrent((self.x - ir.x) * float(range) / (ir.width - self.width))


@event.default('slider-bar')
def on_mouse_drag(widget, x, y, dx, dy, buttons, modifiers):
    # XXX enforce buttons
    if widget.axis == 'x':
        s = widget.getParent('hslider')
        x, y = s.calculateRelativeCoords(x, y)
        value = x / s.inner_rect.width
    else:
        s = widget.getParent('vslider')
        x, y = s.calculateRelativeCoords(x, y)
        value = y / s.inner_rect.height
    s.changeCurrent(value * s.range + s.minimum)
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

