import operator
import xml.sax.saxutils

from pyglet.gl import *
import pyglet.image

from wydget import element, event, loadxml, util, data, style

TOP = 'top'
BOTTOM = 'bottom'
LEFT = 'left'
RIGHT = 'right'
CENTER = 'center'

class ImageCommon(element.Element):
    is_blended = False
    image = None

    def __init__(self, parent, x=0, y=0, z=0, width=None, height=None,
            is_blended=False, valign='top', halign='left', **kw):
        self.is_blended = is_blended
        self.valign = valign
        self.halign = halign
        super(ImageCommon, self).__init__(parent, x, y, z, width, height, **kw)

    def setImage(self, image):
        if hasattr(image, 'texture'):
            image = image.texture
        self.image = image
        self.updateSize()

    def updateSize(self):
        if self.width_spec is None:
            self.width = self.image.width + self.padding * 2
        if self.height_spec is None:
            self.height = self.image.height + self.padding * 2

    def render(self, rect):
        image = self.image
        if image is None:
            return

        ir = util.Rect(image.x, image.y, image.width, image.height)
        if ir.clippedBy(rect):
            rect = ir.intersect(rect)
            if rect is None: return

            # XXX incoming rect is scaled :(
            image = image.get_region(rect.x, rect.y, rect.width/self._sx,
                rect.height/self._sy)

        attrib = 0
        if not self.isEnabled():
            attrib = GL_CURRENT_BIT
        if self.is_blended:
            attrib |= GL_ENABLE_BIT

        if attrib:
            glPushAttrib(attrib)

        if attrib & GL_ENABLE_BIT:
            # blend with background
            glEnable(GL_BLEND)

        if attrib & GL_CURRENT_BIT:
            # blend with gray colour to wash out
            glColor4f(.7, .7, .7, 1.)

        # XXX alignment

        # blit() handles enabling GL_TEXTURE_2D and binding
        image.blit(rect.x, rect.y, 0)

        if attrib:
            glPopAttrib()


class Image(ImageCommon):
    name='image'

    def __init__(self, parent, image, is_blended=True, **kw):
        if image is None and file is None:
            raise ValueError, 'image or file required'

        if isinstance(image, str):
            image = data.load_image(image)
        elif hasattr(image, 'texture'):
            image = image.texture

        self.parent = parent

        super(Image, self).__init__(parent, is_blended=is_blended, **kw)

        self.setImage(image)

    def parentDimensionsChanged(self):
        '''Re-layout text if my dimensions changed.
        '''
        change = super(Image, self).parentDimensionsChanged()
        if change:
            # override default behaviour and reset width/height if changed
            # and there was no spec
            self.updateSize()
        return change

class LabelCommon(ImageCommon):
    @classmethod
    def fromXML(cls, element, parent):
        '''Create the object from the XML element and attach it to the parent.
        '''
        kw = loadxml.parseAttributes(parent, element)
        text = xml.sax.saxutils.unescape(element.text)
        obj = cls(parent, text, **kw)
        for child in element.getchildren():
            loadxml.getConstructor(element.tag)(child, obj)
        return obj

class Label(LabelCommon):
    name='label'
    need_background = True

    def __init__(self, parent, text, color=(0, 0, 0, 1), font_size=None,
            rotate=0, width=None, height=None, **kw):
        self.parent = parent
        self.rotate = util.parse_value(rotate, 0)

        # colors
        if isinstance(color, str):
            color = util.parse_color(color)
        self.color = color

        self.font_size = int(font_size or self.getStyle().font_size)

        super(Label, self).__init__(parent, width=width, height=height, **kw)

        # recalculate the width and height based on rotation
        if self.rotate not in (0, 90, 180, 270):
            raise ValueError, 'rotate must be one of 0, 90, 180, 270, '\
                'not %r'%(self.rotate)

        # sanity check
        if not self.bgcolor:
            self.is_blended = True

        self.setText(text)

    def parentDimensionsChanged(self):
        '''Re-layout text if my dimensions changed.
        '''
        change = super(Label, self).parentDimensionsChanged()
        if change:
            self.setText(self._text)
        return change

    def setText(self, text):
        self._text = text
        if self.rotate in (0, 180):
            pw = self.parent.inner_rect.width
            w = util.parse_value(self.width_spec, pw)
            if w is not None:
                w -= self.padding * 2
        else:
            ph = self.parent.inner_rect.height
            w = util.parse_value(self.height_spec, ph)
            if w is not None:
                w -= self.padding * 2

        if self.is_blended or not text:
            label = self.getStyle().text(text, color=self.color,
                font_size=self.font_size, width=w, halign=self.halign,
                valign='top')
            image = label
        else:
            label = self.getStyle().textAsTexture(text, color=self.color,
                bgcolor=self.bgcolor, font_size=self.font_size,
                width=w, halign=self.halign, rotate=self.rotate)
            image = label.texture

        # don't invoke setImage as it doesn't understand rotate
        self.image = image

        self.updateSize()

    text = property(lambda self: self._text, setText)

    def updateSize(self):
        if self.is_blended and self.rotate in (90, 270):
            if self.width_spec is None:
                self.width = self.image.height + self.padding * 2
            if self.height_spec is None:
                self.height = self.image.width + self.padding * 2
        else:
            if self.width_spec is None:
                self.width = self.image.width + self.padding * 2
            if self.height_spec is None:
                self.height = self.image.height + self.padding * 2

    def render(self, rect):
        if not self.is_blended:
            return super(Label, self).render(rect)

        # XXX clip with glScissor
        glPushMatrix()
        w = self.image.width        # (keep to force _clean() )
        h = self.font_size * len(self.image.lines)

        if self.rotate == 0:
            glTranslatef(0, h, 0)
        if self.rotate:
            glRotatef(self.rotate, 0, 0, 1)
        if self.rotate == 270:
            glTranslatef(-w, h, 0)
        if self.rotate == 180:
            glTranslatef(-w, 0, 0)

        self.image.draw()

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
    need_background = True

    def __init__(self, parent, text, style=None, **kw):
        self.parent = parent
        self.style = style
        super(XHTML, self).__init__(parent, **kw)
        assert self.width_spec, 'XHTML requires a width specification'
        self.setText(text)

    def parentDimensionsChanged(self):
        '''Indicate to the child that the parent rect has changed and it
        may have the opportunity to resize.'''
        pw = self.parent.inner_rect.width
        w = util.parse_value(self.width_spec, pw)
        w -= self.padding * 2
        if w != self.width:
            # re-layout the XHTML and re-gen the texture
            self.layout.viewport_width = w
            self.layout.constrain_viewport()
            self.width = self.layout.canvas_width
            if self.height_spec is None:
                self.height = self.layout.canvas_height
        return w != self.width

    _default = []
    def setText(self, text):
        self.text = text
        pw = self.parent.inner_rect.width
        w = util.parse_value(self.width_spec, pw)
        w -= self.padding * 2

        self.layout = self.getStyle().xhtml('<p>%s</p>'%text, width=w,
            style=self.style)

        # update my dimensions
        self.width = self.layout.canvas_width
        if self.height_spec is None:
            self.height = self.layout.canvas_height

    def render(self, rect):
        '''To render we need to:

        1. Translate the y position from our OpenGL-based y-increases-up
           value to the layout y-increases-down value.
        2. Set up a scissor to limit display to the pixel rect we specify.
        '''
        layout = self.layout

        # reposition the viewport based on visible rect
        layout.viewport_x = rect.x
        scrollable_height = layout.canvas_height - rect.height
        layout.viewport_y = int(scrollable_height - rect.y)
        layout.viewport_width = rect.width
        layout.viewport_height = rect.height
        layout.constrain_viewport()

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
        glTranslatef(0, int(layout.canvas_height - layout.viewport_y), 0)
        layout.view.draw()
        glPopMatrix()

        glPopAttrib()


# Note with the following that layouts start at y=0 and go negative
@event.default('xhtml')
def on_mouse_press(widget, x, y, button, modifiers):
    x, y = widget.calculateRelativeCoords(x, y)
    y -= widget.height
    return widget.layout.on_mouse_press(x, y, button, modifiers)

@event.default('xhtml')
def on_element_leave(widget, x, y):
    x, y = widget.calculateRelativeCoords(x, y)
    y -= widget.height
    return widget.layout.on_mouse_leave(x, y)

@event.default('xhtml')
def on_mouse_motion(widget, x, y, button, modifiers):
    x, y = widget.calculateRelativeCoords(x, y)
    y -= widget.height
    return widget.layout.on_mouse_motion(x, y, button, modifiers)

