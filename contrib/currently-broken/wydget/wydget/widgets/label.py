import operator
import xml.sax.saxutils
from xml.etree import ElementTree
from pyglet.gl import *
import pyglet.image

from wydget import element, event, loadxml, util, data, style

TOP = 'top'
BOTTOM = 'bottom'
LEFT = 'left'
RIGHT = 'right'
CENTER = 'center'

class ImageCommon(element.Element):
    image = None
    blend_color = False

    def __init__(self, parent, x=None, y=None, z=None, width=None,
            height=None, is_blended=False, valign='top', halign='left',
            **kw):
        self.is_blended = is_blended
        self.valign = valign
        self.halign = halign
        super(ImageCommon, self).__init__(parent, x, y, z, width, height, **kw)

    def setImage(self, image):
        if hasattr(image, 'texture'):
            image = image.texture
        self.image = image
        self.setDirty()

    def intrinsic_width(self):
        return self.image.width + self.padding * 2
    def intrinsic_height(self):
        return self.image.height + self.padding * 2

    def render(self, rect):
        image = self.image
        if image is None:
            return

        ir = util.Rect(image.x, image.y, image.width, image.height)
        if ir.clippedBy(rect):
            rect = ir.intersect(rect)
            if rect is None: return

            image = image.get_region(rect.x, rect.y, rect.width, rect.height)

        attrib = 0
        if not self.isEnabled():
            attrib = GL_CURRENT_BIT
        elif self.blend_color and self.color is not None:
            attrib = GL_CURRENT_BIT
        if self.is_blended:
            attrib |= GL_ENABLE_BIT

        if attrib:
            glPushAttrib(attrib)

        if attrib & GL_ENABLE_BIT:
            # blend with background
            glEnable(GL_BLEND)

        if attrib & GL_CURRENT_BIT:
            if not self.isEnabled():
                # blend with gray colour to wash out
                glColor4f(.7, .7, .7, 1.)
            else:
                glColor4f(*self.color)

        # XXX alignment

        # blit() handles enabling GL_TEXTURE_2D and binding
        image.blit(rect.x, rect.y, 0)

        if attrib:
            glPopAttrib()


class Image(ImageCommon):
    name='image'
    blend_color = True

    def __init__(self, parent, image, is_blended=True, color=None, **kw):
        if image is None and file is None:
            raise ValueError, 'image or file required'

        if isinstance(image, str):
            image = data.load_image(image)
        elif hasattr(image, 'texture'):
            image = image.texture

        self.parent = parent

        self.color = util.parse_color(color)

        super(Image, self).__init__(parent, is_blended=is_blended, **kw)

        self.setImage(image)


class LabelCommon(element.Element):
    def __init__(self, parent, text, x=None, y=None, z=None, width=None,
            height=None, font_size=None, valign='top', halign='left',
            color='black', rotate=0, **kw):
        self.valign = valign
        self.halign = halign
        self.font_size = int(font_size or parent.getStyle().font_size)
        self.color = util.parse_color(color)
        self.rotate = util.parse_value(rotate, 0)
        assert self.rotate in (0, 90, 180, 270), \
            'rotate must be one of 0, 90, 180, 270, not %r'%(self.rotate, )
        # set parent now so style is available
        self.parent = parent
        super(LabelCommon, self).__init__(parent, x, y, z, width, height, **kw)
        self.text = text

    @classmethod
    def fromXML(cls, element, parent):
        '''Create the object from the XML element and attach it to the parent.
        '''
        kw = loadxml.parseAttributes(element)
        text = xml.sax.saxutils.unescape(element.text)
        obj = cls(parent, text, **kw)
        for child in element.getchildren():
            loadxml.getConstructor(element.tag)(child, obj)
        return obj


class Label(LabelCommon):
    name='label'

    label = None
    unconstrained = None

    _text = None
    def set_text(self, text):
        if text == self._text: return
        self._text = text
        self.label = None
        self.unconstrained = None
        if hasattr(self, 'parent'):
            self.setDirty()
    text = property(lambda self: self._text, set_text)

    def resetGeometry(self):
        self.label = None
        self.unconstrained = None
        super(Label, self).resetGeometry()

    def _render(self):
        # get the unconstrained render first to determine intrinsic dimensions
        style = self.getStyle()
        self.unconstrained = style.text(self._text, font_size=self.font_size,
            halign=self.halign, valign='top')

        if self.rotate in (0, 180):
            w = self.width or self.width_spec.specified()
            if w is not None:
                w -= self.padding * 2
        else:
            w = self.height or self.height_spec.specified()
            if w is not None:
                w -= self.padding * 2
        self.label = style.text(self._text, color=self.color,
            font_size=self.font_size, width=w, halign=self.halign,
            valign='top')

    def set_width(self, width):
        # TODO this doesn't cope with the text being wrapped when width <
        # self.label.width
        self._width = width
        if self.rotate in (0, 180) and self.label is not None:
            self.label.width = width
        self.setDirty()
    width = property(lambda self: self._width, set_width)

    def set_height(self, height):
        # TODO this doesn't cope with the text being wrapped when height <
        # self.label.width
        self._height = height
        if self.rotate in (90, 270) and self.label is not None:
            self.label.width = height
        self.setDirty()
    height = property(lambda self: self._height, set_height)

    def intrinsic_width(self):
        # determine the width of the text with no width limitation
        if self.unconstrained is None:
            self._render()
        if self.rotate in (90, 270):
            return self.unconstrained.height + self.padding * 2
        return self.unconstrained.width + self.padding * 2

    def intrinsic_height(self):
        # determine the height of the text with no width limitation
        if self.unconstrained is None:
            self._render()
        if self.rotate in (90, 270):
            return self.unconstrained.width + self.padding * 2
        return self.unconstrained.height + self.padding * 2

    def getRects(self, *args):
        if self.label is None:
            self._render()
        return super(Label, self).getRects(*args)

    def render(self, rect):
        if self.label is None:
            self._render()
        glPushMatrix()
        w = self.label.width
        h = self.label.height

        if self.rotate:
            glRotatef(self.rotate, 0, 0, 1)
        else:
            glTranslatef(0, h, 0)

        if self.rotate == 270:
            glTranslatef(-w+self.padding, h, 0)
        elif self.rotate == 180:
            glTranslatef(-w+self.padding, 0, 0)

        scissor = not (rect.x == rect.y == 0 and rect.width >= w and
            rect.height >= h)

        if scissor:
            glPushAttrib(GL_SCISSOR_BIT)
            glEnable(GL_SCISSOR_TEST)
            x, y = self.calculateAbsoluteCoords(rect.x, rect.y)
            glScissor(int(x), int(y), int(rect.width), int(rect.height))

        self.label.draw()

        if scissor:
            glPopAttrib()

        glPopMatrix()

class XHTML(LabelCommon):
    '''Render an XHTML layout.

    Note that layouts use a different coordinate system:

    Canvas dimensions
        layout.canvas_width and layout.canvas_height
    Viewport
        layout.viewport_x, layout.viewport_y, layout.viewport_width
        and layout.viewport_height

    The y coordinates start 0 at the *top* of the canvas and increase
    *down* the canvas.
    '''
    name='xhtml'

    def __init__(self, parent, text, style=None, **kw):
        assert 'width' in kw, 'XHTML requires a width specification'
        self.parent = parent
        self.style = style
        super(XHTML, self).__init__(parent, text, **kw)

    @classmethod
    def fromXML(cls, element, parent):
        '''Create the object from the XML element and attach it to the parent.
        '''
        kw = loadxml.parseAttributes(element)
        children = element.getchildren()
        if children:
            text = ''.join(ElementTree.tostring(child) for child in children)
        else:
            text = ''
        text = element.text + text + element.tail
        obj = cls(parent, text, **kw)
        return obj

    def set_text(self, text):
        self._text = text
        self._render()
        if hasattr(self, 'parent'):
            self.setDirty()
    text = property(lambda self: self._text, set_text)

    def _render(self):
        w = self.width
        if w is None:
            if self.width_spec.is_fixed or self.parent.width is not None:
                w = self.width = self.width_spec.calculate()
            else:
                # use an arbitrary initial value
                w = self.width = 512
        self._target_width = w
        w -= self.padding * 2
        self.label = self.getStyle().xhtml('<p>%s</p>'%self._text, width=w,
            style=self.style)
        self.height = self.label.canvas_height

    def intrinsic_width(self):
        if not self.width:
            if self.label is not None:
                self.width = self.label.canvas_width + self.padding * 2
            else:
                self._render()
        return self.width
    def intrinsic_height(self):
        if not self.height:
            if self.label is not None:
                self.height = self.label.canvas_height + self.padding * 2
            else:
                self._render()
        return self.height

    def resize(self):
        # calculate the new width if necessary
        if self._width is None:
            w = self.width_spec.calculate()
            if w is None: return False
            self.width = w
            # and reshape the XHTML layout if width changed
            if w != self._target_width:
                self._target_width = w
                self.label.viewport_width = self.width
                self.label.constrain_viewport()

        # always use the canvas height
        self.height = self.label.canvas_height
        return True

    def render(self, rect):
        '''To render we need to:

        1. Translate the y position from our OpenGL-based y-increases-up
           value to the layout y-increases-down value.
        2. Set up a scissor to limit display to the pixel rect we specify.
        '''
        # reposition the viewport based on visible rect
        label = self.label
        label.viewport_x = rect.x
        scrollable_height = label.canvas_height - rect.height
        label.viewport_y = int(scrollable_height - rect.y)
        label.viewport_width = rect.width
        label.viewport_height = rect.height
        label.constrain_viewport()

        scissor = not (rect.x == rect.y == 0 and rect.width == self.width and
            rect.height == self.height)

        if scissor:
            glPushAttrib(GL_CURRENT_BIT|GL_SCISSOR_BIT)
            glEnable(GL_SCISSOR_TEST)
            x, y = self.calculateAbsoluteCoords(rect.x, rect.y)
            glScissor(int(x), int(y), int(rect.width), int(rect.height))
        else:
            glPushAttrib(GL_CURRENT_BIT)

        glPushMatrix()
        glTranslatef(0, int(label.canvas_height - label.viewport_y), 0)
        label.view.draw()
        glPopMatrix()

        glPopAttrib()


# Note with the following that layouts start at y=0 and go negative
@event.default('xhtml')
def on_mouse_press(widget, x, y, button, modifiers):
    x, y = widget.calculateRelativeCoords(x, y)
    y -= widget.height
    return widget.label.on_mouse_press(x, y, button, modifiers)

@event.default('xhtml')
def on_element_leave(widget, x, y):
    x, y = widget.calculateRelativeCoords(x, y)
    y -= widget.height
    return widget.label.on_mouse_leave(x, y)

@event.default('xhtml')
def on_mouse_motion(widget, x, y, button, modifiers):
    x, y = widget.calculateRelativeCoords(x, y)
    y -= widget.height
    return widget.label.on_mouse_motion(x, y, button, modifiers)

