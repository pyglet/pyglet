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
        if self.width_spec is None:
            self.width = self.image.width + self.padding*2
        if self.height_spec is None:
            self.height = self.image.height + self.padding*2

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

        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_TEXTURE_2D)
        glDisable(GL_DEPTH_TEST)
        if self.is_blended:
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glEnable(GL_BLEND)

        # XXX alignment
        # figure the image rect to render

        image.blit(rect.x, rect.y, 0)

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

    def __init__(self, parent, text, color=(0, 0, 0, 1), font_size=None, **kw):
        self.parent = parent

        # colors
        if isinstance(color, str):
            color = util.parse_color(color)
        self.color = color

        self.font_size = font_size

        super(Label, self).__init__(parent, **kw)

        # sanity check
        if not self.bgcolor:
            self.is_blended = True

        self.setText(text)

    def setText(self, text):
        self.text = text
        pw = self.parent.inner_rect.width
        w = util.parse_value(self.width_spec, pw)
        if w is not None: w -= self.padding * 2

        # free up old image
        if self.image is not None and isinstance(self.image,
                pyglet.image.Texture):
            self.image.delete()

        if self.is_blended:
            label = self.getStyle().text(text, color=self.color,
                font_size=self.font_size, width=w, halign=self.halign)
        else:
            label = self.getStyle().textAsTexture(text, color=self.color,
                bgcolor=self.bgcolor, font_size=self.font_size,
                width=w, halign=self.halign)
        self.setImage(label)
        if self.width_spec is None:
            self.width = label.width + self.padding * 2
        if self.height_spec is None:
            self.height = label.height + self.padding * 2

    def render(self, rect):
        if not self.is_blended:
            return super(Label, self).render(rect)

        # XXX clip with glScissor
        self.image.draw()


class XHTML(LabelCommon):
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
        new_width = util.parse_value(self.width_spec, pw)
        if self.width != new_width:
            self.width = new_width
            self.setText(self.text)

    _default = []
    def setText(self, text):
        self.text = text
        pw = self.parent.inner_rect.width
        w = util.parse_value(self.width_spec, pw)
        if w is not None: w -= self.padding * 2

        # free up old image
        if self.image is not None:
            self.image.delete()

        self.layout = self.getStyle().xhtml('<p>%s</p>'%text, width=w,
            style=self.style)

        self.setImage(style.xhtmlAsTexture(self.layout))

@event.default('xhtml')
def on_mouse_press(widget, x, y, button, modifiers):
    x, y = widget.calculateRelativeCoords(x, y)
    # layouts start at y=0 and go negative
    y -= widget.height
    return widget.layout.on_mouse_press(x, y, button, modifiers)

    '''
    The following is using the layout rendering directly, but it's ver'
    slow.

        self.label = self.getStyle().xhtml('<p>%s</p>'%text, width=w,
            style=self.style)
        if self.width_spec is None:
            self.width = self.label.viewport_width
        if self.height_spec is None:
            self.height = self.label.viewport_height

    def render(self, rect):
        self.label.viewport_x = rect.x
        self.label.viewport_y = rect.y
        self.label.viewport_width = rect.width
        self.label.viewport_height = rect.height
        glPushMatrix()
        glTranslatef(0, self.label.viewport_height, 0)
        self.label.view.draw()
        glPopMatrix()
    '''
