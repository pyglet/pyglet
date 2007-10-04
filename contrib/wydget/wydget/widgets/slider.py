from pyglet.gl import *
from pyglet import clock
from pyglet.window import mouse

from wydget import element, event, data, util, anim
from wydget.widgets.button import Button, RepeaterButton
from wydget.widgets.label import Label
from wydget.widgets.frame import Frame

class SliderCommon(Frame):
    slider_size = 16

    def resize(self):
        if not super(SliderCommon, self).resize(): return False
        self.handleSizing()
        return True

    def get_value(self):
        return self._value
    def set_value(self, value, event=False, position_bar=True):
        self._value = self.type(max(self.minimum, min(self.maximum, value)))
        if position_bar:
            self.positionBar()
        if self.show_value:
            self.bar.tect = str(self._value)
        if event:
            self.getGUI().dispatch_event(self, 'on_change', self._value)
    value = property(get_value, set_value)

    def stepToMaximum(self, multiplier=1):
        self.set_value(self._value + multiplier * self.step, event=True)

    def stepToMinimum(self, multiplier=1):
        self.set_value(self._value - multiplier * self.step, event=True)

class VerticalSlider(SliderCommon):
    '''
    The value will be of the same type as the minimum value.
    '''
    name='vslider'
    def __init__(self, parent, minimum, maximum, value, step=1,
            bar_size=None, show_value=False, bar_text_color='white',
            bar_color=(.3, .3, .3, 1), x=None, y=None, z=None,
            width=SliderCommon.slider_size, height='100%',
            bgcolor='gray', **kw):

        self.minimum = util.parse_value(minimum, 0)
        self.type = type(self.minimum)
        self.maximum = util.parse_value(maximum, 0)
        self.range = self.maximum - self.minimum
        self._value = util.parse_value(value, 0)
        self.step = util.parse_value(step, 0)
        self.show_value = show_value
        self.bar_spec = bar_size
        self.bar_color = util.parse_color(bar_color)
        self.bar_text_color = util.parse_color(bar_text_color)
        self.bar = self.dbut = self.ubut = None

        super(VerticalSlider, self).__init__(parent, x, y, z, width, height,
            bgcolor=bgcolor, **kw)

    def handleSizing(self):
        try:
            # if the bar size spec is a straight integer, use it
            min_size = int(self.bar_spec) + self.slider_size
        except:
            min_size = self.slider_size * 2
        height = self.height
        if height < min_size:
            height = min_size

        # assume buttons are same height
        bh = ArrowButtonUp.get_arrow().height

        # only have buttons if there's enough room (two buttons plus
        # scrolling room)
        self.have_buttons = height > (bh * 2 + min_size)
        if self.have_buttons and self.dbut is None:
            # do this after the call to super to allow it to set the parent etc.
            self.dbut = ArrowButtonDown(self, classes=('-repeater-button-min',),
                color='black')
            self.ubut = ArrowButtonUp(self, y=height-bh, color='black',
                classes=('-repeater-button-max',))
        elif not self.have_buttons and self.dbut is not None:
            self.dbut.delete()
            self.ubut.delete()
            self.dbut = self.ubut = None

        # add slider bar
        #i_height = self.inner_rect.height
        i_height = height
        self.bar_size = util.parse_value(self.bar_spec, i_height)
        if self.bar_size is None:
            self.bar_size = int(max(self.slider_size, i_height /
                (self.range+1)))

        s = self.show_value and str(self._value) or ' '
        # note: dimensions are funny because the bar is rotated 90 degrees
        if self.bar is None:
            self.bar = SliderBar(self, 'y', s, self.width, self.bar_size,
                bgcolor=self.bar_color, color=self.bar_text_color)
        else:
            self.bar.text = s
            self.bar.height = self.bar_size

        self.height = height

        # fix up sizing and positioning of elements
        if self.dbut is not None:
            self.dbut.resize()
            self.ubut.resize()
        self.bar.resize()
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
        self.bar.x = 0
        self.bar.y = ir.y + int(self._value / float(self.range) * h)

@event.default('vslider')
def on_mouse_press(self, x, y, buttons, modifiers):
    x, y = self.calculateRelativeCoords(x, y)
    r = self.bar.rect
    if y < r.y: self.stepToMinimum()
    elif y > r.top: self.stepToMaximum()
    return event.EVENT_HANDLED

@event.default('vslider')
def on_mouse_scroll(self, x, y, dx, dy):
    if dy: self.stepToMaximum(dy)
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
    The value will be of the same type as the minimum value.
    '''
    name='hslider'
    def __init__(self, parent, minimum, maximum, value, step=1,
            bar_size=None, show_value=False, bar_text_color='white',
            bar_color=(.3, .3, .3, 1), x=None, y=None, z=None, width='100%',
            height=SliderCommon.slider_size, bgcolor='gray', **kw):

        self.minimum = util.parse_value(minimum, 0)
        self.type = type(self.minimum)
        self.maximum = util.parse_value(maximum, 0)
        self.range = self.maximum - self.minimum
        self._value = util.parse_value(value, 0)
        self.step = util.parse_value(step, 0)
        self.show_value = show_value
        self.bar_spec = bar_size
        self.bar_color = util.parse_color(bar_color)
        self.bar_text_color = util.parse_color(bar_text_color)
        self.bar = self.lbut = self.rbut = None

        # for step repeat when clicking in the bar
        self.delay_timer = None

        super(HorizontalSlider, self).__init__(parent, x, y, z, width, height,
            bgcolor=bgcolor, **kw)

    def handleSizing(self):
        try:
            # if the bar size spec is a straight integer, use it
            min_size = int(self.bar_spec) + self.slider_size
        except:
            min_size = self.slider_size * 2
        width = self.width
        if width < min_size:
            width = min_size

        # assume buttons are same width
        bw = ArrowButtonLeft.get_arrow().width

        # only have buttons if there's enough room (two buttons plus
        # scrolling room)
        self.have_buttons = width > (bw * 2 + min_size)
        if self.have_buttons and self.lbut is None:
            self.lbut = ArrowButtonLeft(self, classes=('-repeater-button-min',),
                color='black')
            self.rbut = ArrowButtonRight(self, x=width-bw, color='black',
                classes=('-repeater-button-max',))
        elif not self.have_buttons and self.lbut is not None:
            self.lbut.delete()
            self.rbut.delete()
            self.lbut = self.rbut = None

        # slider bar size
        #i_width = self.inner_rect.width
        i_width = width
        self.bar_size = util.parse_value(self.bar_spec, i_width)
        if self.bar_size is None:
            self.bar_size = int(max(self.slider_size, i_width / (self.range+1)))

        s = self.show_value and str(self._value) or ' '
        # we force blending here so we don't generate a bazillion textures
        if self.bar is None:
            self.bar = SliderBar(self, 'x', s, self.bar_size, self.height,
                bgcolor=self.bar_color, color=self.bar_text_color)
        else:
            self.bar.text = s
            self.bar.width = self.bar_size

        self.width = width

        # fix up sizing and positioning of elements
        if self.lbut is not None:
            self.lbut.resize()
            self.rbut.resize()
        self.bar.resize()
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
        self.bar.x = ir.x + int(self._value / float(range) * w)
        self.bar.y = 0

    repeating = False
    def startRepeat(self, direction):
        self.delay_timer = None
        self.repeat_time = 0
        self.repeating = True
        self.repeat_direction = direction
        clock.schedule(self.repeat)

    def repeat(self, dt):
        self.repeat_time += dt
        if self.repeat_time > .1:
            self.repeat_time -= .1
            self.repeat_direction()

    def stopRepeat(self):
        if self.delay_timer is not None:
            self.delay_timer.cancel()
            self.delay_timer = None
        if self.repeating:
            clock.unschedule(self.repeat)
        self.repeating = False

@event.default('hslider')
def on_mouse_press(self, x, y, buttons, modifiers):
    x, y = self.calculateRelativeCoords(x, y)
    r = self.bar.rect
    if x < r.x:
        self.stepToMinimum()
        self.delay_timer = anim.Delayed(self.startRepeat,
            self.stepToMinimum, delay=.5)
    elif x > r.right:
        self.stepToMaximum()
        self.delay_timer = anim.Delayed(self.startRepeat,
            self.stepToMaximum, delay=.5)
    return event.EVENT_HANDLED

@event.default('hslider')
def on_mouse_release(self, x, y, buttons, modifiers):
    self.stopRepeat()
    return event.EVENT_HANDLED

@event.default('hslider')
def on_mouse_scroll(self, x, y, dx, dy):
    if dx: self.stepToMaximum(dx)
    else: self.stepToMaximum(dy)
    return event.EVENT_HANDLED


class SliderBar(Label):
    name = 'slider-bar'
    def __init__(self, parent, axis, initial, width, height, **kw):
        self.axis = axis
        rotate = 90 if axis == 'y' else 0
        super(SliderBar, self).__init__(parent, str(initial), width=width,
            height=height, halign='center', rotate=rotate, **kw)

@event.default('slider-bar')
def on_mouse_drag(widget, x, y, dx, dy, buttons, modifiers):
    if not buttons & mouse.LEFT:
        return event.EVENT_UNHANDLED
    if widget.axis == 'x':
        s = widget.getParent('hslider')
        x = s.calculateRelativeCoords(x, y)[0]
        w = s.inner_rect.width - widget.width
        xoff = s.inner_rect.x
        if x < xoff:
            widget.x = xoff
        elif x > (xoff + s.inner_rect.width):
            widget.x = w + xoff
        else:
            widget.x = max(xoff, min(w + xoff, widget.x + dx))
        value = (widget.x - xoff) / float(w)
    else:
        s = widget.getParent('vslider')
        y = s.calculateRelativeCoords(x, y)[1]
        h = s.inner_rect.height - widget.height
        yoff = s.inner_rect.y
        if y < yoff:
            widget.y = yoff
        elif y > (yoff + s.inner_rect.height):
            widget.y = h + yoff
        else:
            widget.y = max(yoff, min(h + yoff, widget.y + dy))
        value = (widget.y - yoff) / float(h)

    s.set_value(value * s.range + s.minimum, position_bar=False, event=True)
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

