import xml.sax.saxutils

from pyglet.gl import *
from pyglet import clock
from pyglet.window import key, mouse

from wydget import element, event, util, anim, data, loadxml
from wydget.widgets.label import ImageCommon, Label


class ButtonCommon(object):
    is_focusable = True
    is_pressed = False
    is_over = False

class Button(ButtonCommon, ImageCommon):
    '''A button represented by one to three images.

        image         - the normal-state image to be displayed
        pressed_image - button is pressed
        over_image    - the mouse is over the button or the button is focused

    If text is supplied, it is rendered over the image, centered.
    '''
    name = 'button'

    def __init__(self, parent, image, text=None, pressed_image=None,
            over_image=None, is_blended=True, font_size=None,
            color=(0, 0, 0, 1),
            x=0, y=0, z=0, width=None, height=None, **kw):
        super(Button, self).__init__(parent, x, y, z, width, height, 
            is_blended=is_blended, **kw)

        if image is None:
            raise ValueError, 'image argument is required'

        self.setImage(image)
        self.setPressedImage(pressed_image)
        self.setOverImage(over_image)
        self.color = util.parse_color(color)

        if text:
            self.font_size = int(font_size or self.getStyle().font_size)
            self.bg = self.base_image
            self.over_bg = self.over_image
            self.pressed_bg = self.pressed_image
            # clear so we don't delete these 
            self.base_image = self.over_image = self.pressed_image = None
        self.text = text

    @classmethod
    def fromXML(cls, element, parent):
        '''Create the object from the XML element and attach it to the parent.
        '''
        kw = loadxml.parseAttributes(element)
        if element.text:
            text = xml.sax.saxutils.unescape(element.text)
        else:
            text = None
        if 'image' in kw:
            kw['text'] = text
            obj = Button(parent, **kw)
        else:
            obj = TextButton(parent, text, **kw)
        for child in element.getchildren():
            loadxml.getConstructor(child.tag)(child, obj)
        return obj

    def setImage(self, image, attribute='base_image'):
        if isinstance(image, str):
            image = data.load_image(image).texture
        elif hasattr(image, 'texture'):
            image = image.texture
        setattr(self, attribute, image)
        if attribute == 'base_image':
            self.image = self.base_image
        self.setDirty()
    def setPressedImage(self, image):
        self.setImage(image, 'pressed_image')
    def setOverImage(self, image):
        self.setImage(image, 'over_image')

    _text = None
    def set_text(self, text):
        if text == self._text: return
        self._text = text

        self.over_image = None
        self.pressed_image = None

        # XXX restrict text width?
        label = self.getStyle().text(text, font_size=self.font_size,
            color=self.color, valign='top')
        label.width        # force clean
        num_lines = len(label.lines)

        # size of resulting button images
        w, h = self.width, self.height = self.bg.width, self.bg.height

        # center
        tx = self.bg.width // 2 - label.width // 2
        ty = self.bg.height // 2 - label.height // 2

        def f(bg):
            def _inner():
                glPushAttrib(GL_CURRENT_BIT|GL_COLOR_BUFFER_BIT)
                glClearColor(1, 1, 1, 0)
                glClear(GL_COLOR_BUFFER_BIT)
                glPushMatrix()
                glLoadIdentity()
                bg.blit(0, 0, 0)
                glTranslatef(tx, ty + label.height, 0)
                # prevent the text's alpha channel being written into the new
                # texture
                glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_FALSE)
                label.draw()
                glPopMatrix()
                glPopAttrib()
            return _inner

        self.setImage(util.renderToTexture(w, h, f(self.bg)))

        if self.over_bg is not None:
            self.setImage(util.renderToTexture(w, h, f(self.over_bg)),
                'over_image')

        if self.pressed_bg is not None:
            self.setImage(util.renderToTexture(w, h, f(self.pressed_bg)),
                'pressed_image')
    text = property(lambda self: self._text, set_text)

    def render(self, rect):
        '''Select the correct image to render.
        '''
        if self.is_pressed and self.is_over and self.pressed_image:
            self.image = self.pressed_image
        elif self.is_over and self.over_image:
            self.image = self.over_image
        else:
            self.image = self.base_image
        # XXX handle isFocused()
        super(Button, self).render(rect)


class TextButton(ButtonCommon, Label):
    '''A button with text on it.

    Will be rendered over the standard Element rendering.
    '''
    name = 'button'

    _default = []
    def __init__(self, parent, text, bgcolor='white', color='black',
            border='black', focus_border=(.3, .3, .7, 1),
            pressed_bgcolor=(1, .9, .9, 1), over_bgcolor=(.9, .9, 1, 1),
            **kw):

        super(TextButton, self).__init__(parent, text, bgcolor=bgcolor,
            color=color, border=border, **kw)

        # colouring attributes
        self.base_bgcolor = self.bgcolor
        self.pressed_bgcolor = util.parse_color(pressed_bgcolor)
        self.over_bgcolor = util.parse_color(over_bgcolor)
        self.base_border = self.border
        self.focus_border = util.parse_color(focus_border)

    def renderBorder(self, clipped):
        if self.isFocused():
            self.border = self.focus_border
        else:
            self.border = self.base_border
        super(TextButton, self).renderBorder(clipped)

    def renderBackground(self, clipped):
        '''Select the correct image to render.
        '''
        if not self.isEnabled():
            self.bgcolor = (.7, .7, .7, 1)
        elif self.is_pressed and self.is_over and self.pressed_bgcolor:
            self.bgcolor = self.pressed_bgcolor
        elif self.is_over and self.over_bgcolor:
            self.bgcolor = self.over_bgcolor
        else:
            self.bgcolor = self.base_bgcolor
        super(TextButton, self).renderBackground(clipped)


class RepeaterButton(Button):
    '''Generates on_click events periodically if the mouse button is held
    pressed over the button.

    on mouse press, schedule a timeout for .5 secs and after that time
    schedule a call to the callback every .1 secs.

    on mouse release, cancel the timer

    on mouse leave, cancel the *second* timer only

    on mouse enter, reinstate the second timer

    '''
    name = 'repeater-button'
    is_focusable = False

    delay_timer = None
    def __init__(self, parent, delay=.5, **kw):
        super(RepeaterButton, self).__init__(parent, **kw)
        self.delay = delay

    repeating = False
    def startRepeat(self):
        self.delay_timer = None
        self.repeat_time = 0
        self.repeating = True
        clock.schedule(self.repeat)

    def repeat(self, dt):
        self.repeat_time += dt
        if self.repeat_time > .1:
            self.repeat_time -= .1
            self.getGUI().dispatch_event(self, 'on_click', 0, 0,
                self.buttons, self.modifiers, 1)

    def stopRepeat(self):
        if self.delay_timer is not None:
            self.delay_timer.cancel()
            self.delay_timer = None
        if self.repeating:
            clock.unschedule(self.repeat)
        self.repeating = False


@event.default('button, text-button')
def on_gain_focus(self, source):
    if source == 'mouse':
        # mouse clicks should not focus buttons
        return event.EVENT_UNHANDLED
    return event.EVENT_HANDLED

@event.default('button')
def on_element_enter(self, x, y):
    self.is_over = True
    return event.EVENT_HANDLED

@event.default('button')
def on_element_leave(self, x, y):
    self.is_over = False
    return event.EVENT_HANDLED

@event.default('button')
def on_mouse_press(self, x, y, button, modifiers):
    self.is_pressed = True
    return event.EVENT_UNHANDLED

@event.default('button')
def on_mouse_release(self, x, y, button, modifiers):
    self.is_pressed = False
    return event.EVENT_UNHANDLED


@event.default('repeater-button')
def on_mouse_press(self, x, y, buttons, modifiers):
    self.is_pressed = True
    if self.delay:
        self.delay_timer = anim.Delayed(self.startRepeat, delay=self.delay)
    else:
        self.startRepeat()
    self.buttons = buttons
    self.modifiers = modifiers
    self.getGUI().dispatch_event(self, 'on_click', x, y, buttons,
        modifiers, 1)
    self.is_pressed = True
    return event.EVENT_HANDLED

@event.default('repeater-button')
def on_mouse_release(self, x, y, buttons, modifiers):
    self.is_pressed = False
    self.stopRepeat()
    return event.EVENT_HANDLED

@event.default('repeater-button')
def on_element_enter(self, x, y):
    if self.is_pressed:
        self.startRepeat()
    self.is_over = True
    return event.EVENT_HANDLED

@event.default('repeater-button')
def on_element_leave(self, x, y):
    self.is_over = False
    self.stopRepeat()
    return event.EVENT_HANDLED

@event.default('button, repeater-button')
def on_text(self, text):
    if text in ' \r':
        self.getGUI().dispatch_event(self, 'on_click', 0, 0, mouse.LEFT, 0, 1)
        return event.EVENT_HANDLED
    return event.EVENT_UNHANDLED

