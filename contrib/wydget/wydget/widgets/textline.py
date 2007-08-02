from pyglet.gl import *
from pyglet.window import key

from wydget import event, anim, util, element
from wydget.widgets.frame import Frame
from wydget.widgets.label import Label

class Cursor(element.Element):
    name = '-text-cursor'
    def __init__(self, color, *args, **kw):
        self.color = color
        self.alpha = 1
        super(Cursor, self).__init__(*args, **kw)
    def draw(self, *args):
        pass
    def _render(self, rect):
        glPushAttrib(GL_ENABLE_BIT|GL_CURRENT_BIT)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)
        color = self.color[:3] + (self.alpha,)
        glColor4f(*color)
        glRectf(rect.x, rect.y, rect.x + rect.width, rect.y + rect.height)
        glPopAttrib()

class CursorAnimation(anim.Animation):
    def __init__(self, element):
        self.element = element
        super(CursorAnimation, self).__init__()

    def animate(self, dt):
        self.anim_time += dt
        if self.anim_time % 1 < .5:
            self.element.alpha = 1
        else:
            self.element.alpha = 0.2

class TextInputLine(Label):
    def __init__(self, parent, text, *args, **kw):
        self.cursor_index = len(text)
        if 'is_password' in kw:
            self.is_password = kw.pop('is_password')
        else:
            self.is_password = False
        kw['border'] = None
        super(TextInputLine, self).__init__(parent, text, *args, **kw)

        self.cursor = Cursor(self.color, self, 1, 0, 0, 1, self.font_size,
            is_visible=False)

    def setText(self, text):
        self.text = text

        if self.is_password:
            text = u'\u2022' * len(text)

        if text:
            style = self.getStyle()
            self.glyphs = style.getGlyphString(text, size=self.font_size)
            self.image = style.textAsTexture(text,
                font_size=self.font_size, color=self.color,
                bgcolor=self.bgcolor)
            self.width = self.image.width
            self.height = self.image.height
        else:
            self.glyphs = None
            self.image = None
            self.width = 0
            self.height = self.font_size

        # move cursor
        self.setCursorPosition(self.cursor_index)

    def render(self, rect):
        super(TextInputLine, self).render(rect)
        if self.cursor.is_visible:
            self.cursor._render(self.cursor.rect)

    def setCursorPosition(self, index):
        direction = index - self.cursor_index

        self.cursor_index = index

        # determine position in self.glyphs
        if not self.text or index == 0:
            cursor_text_width = 0
        else:
            cursor_text_width = self.glyphs.get_subwidth(0, index)

        parent_width = self.parent.inner_rect.width
        cursor_x = cursor_text_width + self.x

        # offset for current self.image offset
        if direction > 0:
            if cursor_x > parent_width:
                self.x = - (cursor_text_width - parent_width)
        else:
            if cursor_x < 0:
                self.x = -(cursor_text_width)

        if hasattr(self, 'cursor'):
            self.cursor.x = max(0, cursor_text_width)

class TextInput(Frame):
    '''Cursor position indicates which indexed element the cursor is to the
    left of.

    Note the default padding of 2 (rather than 1) pixels to give some space
    from the border.
    '''
    name='textinput'
    is_focusable = True
    def __init__(self, parent, text='', font_size=None, size=None,
            x=0, y=0, z=0, width=None, height=None, border='black',
            padding=2, bgcolor='white', color='black', classes=(), **kw):
        classes += ('-text-input',)
        if font_size is None:
            font_size = parent.getStyle().font_size
        else:
            font_size = util.parse_value(font_size, None)
        self.font_size = font_size
        if size is not None:
            width = size * self.font_size
        super(TextInput, self).__init__(parent, x, y, z, width, height,
            padding=padding, border=border, classes=classes, bgcolor=bgcolor,
            **kw)

        self.ti = TextInputLine(self, text, font_size=font_size,
            bgcolor=bgcolor, color=color, classes=('-text-input-line',))

        if width is None:
            self.width = self.ti.width + self.padding * 2
        if height is None:
            self.height = self.ti.height + self.padding * 2

    def get_text(self):
        return self.ti.text
    def set_text(self, text):
        self.ti.setText(text)
    text = property(get_text, set_text)

    def get_cursor_postion(self):
        return self.ti.cursor_index
    def set_cursor_postion(self, pos):
        self.ti.setCursorPosition(pos)
    cursor_postion = property(get_cursor_postion, set_cursor_postion)

    def get_width(self): return self._width
    def set_width(self, value):
        super(TextInput, self).set_width(value)
        # set up clipping
        ir = self.inner_rect
        self.setViewClip((0, 0, ir.width, ir.height))
    width = property(get_width, set_width)

    def get_height(self): return self._height
    def set_height(self, value):
        super(TextInput, self).set_height(value)
        # set up clipping
        ir = self.inner_rect
        self.setViewClip((0, 0, ir.width, ir.height))
    height = property(get_height, set_height)
 
class PasswordInput(TextInput):
    name='password'
    def __init__(self, *args, **kw):
        super(PasswordInput, self).__init__(*args, **kw)
        self.ti.is_password = True
        self.ti.setText(self.ti.text)

@event.default('.-text-input')
def on_mouse_press(widget, x, y, button, modifiers):
    widget = widget.ti
    x, y = widget.calculateRelativeCoords(x, y)
    diff = abs(x)
    index = 0
    if widget.glyphs is not None:
        for advance in widget.glyphs.cumulative_advance:
            new_diff = abs(x - advance)
            if new_diff > diff: break
            index += 1
            diff = new_diff
        if index >= len(widget.text):
            index = len(widget.text)
    widget.setCursorPosition(index)
    return event.EVENT_HANDLED

@event.default('.-text-input')
def on_gain_focus(widget):
    widget.ti.cursor.animation = CursorAnimation(widget.ti.cursor)
    widget.ti.cursor.is_visible = True
    return event.EVENT_HANDLED

@event.default('.-text-input')
def on_lose_focus(widget):
    widget.ti.cursor.animation.cancel()
    widget.ti.cursor.animation = None
    widget.ti.cursor.is_visible = False
    return event.EVENT_HANDLED

@event.default('.-text-input')
def on_element_enter(widget, x, y):
    w = widget.getGUI().window
    cursor = w.get_system_mouse_cursor(w.CURSOR_TEXT)
    w.set_mouse_cursor(cursor)
    return event.EVENT_HANDLED

@event.default('.-text-input')
def on_element_leave(widget, x, y):
    w = widget.getGUI().window
    cursor = w.get_system_mouse_cursor(w.CURSOR_DEFAULT)
    w.set_mouse_cursor(cursor)
    return event.EVENT_HANDLED

@event.default('.-text-input')
def on_text(widget, text):
    # special-case newlines - we don't want them
    if text == '\r': return event.EVENT_UNHANDLED
    ti = widget.ti
    i = ti.cursor_index
    text = ti.text[0:i] + text + ti.text[i:]
    ti.setText(text)
    ti.setCursorPosition(i+1)
    ti.getGUI().dispatch_event(widget, 'on_change', text)
    return event.EVENT_HANDLED

@event.default('.-text-input')
def on_text_motion(widget, motion):
    ti = widget.ti
    pos = ti.cursor_index
    if motion == key.MOTION_LEFT:
        if pos != 0:
            ti.setCursorPosition(pos-1)
    elif motion == key.MOTION_RIGHT:
        if pos != len(ti.text):
            ti.setCursorPosition(pos+1)
    elif motion in (key.MOTION_UP, key.MOTION_BEGINNING_OF_LINE,
            key.MOTION_BEGINNING_OF_FILE):
        ti.setCursorPosition(0)
    elif motion in (key.MOTION_DOWN, key.MOTION_END_OF_LINE,
            key.MOTION_END_OF_FILE):
        ti.setCursorPosition(len(ti.text))
    elif motion == key.MOTION_BACKSPACE:
        if pos != 0:
            n = pos
            ti.cursor_index -= 1
            text = ti.text[0:n-1] + ti.text[n:]
            ti.setText(text)
            widget.getGUI().dispatch_event(widget, 'on_change', text)
    elif motion == key.MOTION_DELETE:
        if pos != len(ti.text):
            n = pos
            text = ti.text[0:n] + ti.text[n+1:]
            ti.setText(text)
            widget.getGUI().dispatch_event(widget, 'on_change', text)
    else:
        print 'Unhandled MOTION', key.motion_string(motion)

    return event.EVENT_HANDLED

