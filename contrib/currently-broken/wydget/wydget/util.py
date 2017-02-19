import math

class RestartLayout(Exception):
    '''During layout an element has mutated the scene (eg. through adding
    scrollbars) and thus layout must be restarted).
    '''

def parse_value(value, base_value=0):
    '''Parse a numeric value spec which is one of:

        NNN    integer
        NN.MMM float
        NN%    proportional to base_value
    '''
    if not isinstance(value, str):
        return value
    if value[-1] == '%': 
        value = base_value * float(value[:-1]) / 100
    elif '.' in value:
        return float(value)
    return int(value)

intceil = lambda i: int(math.ceil(i))

class Dimension(object):
    def __init__(self, spec, element, parent, attribute):
        self.spec = spec
        self.element = element
        self.parent = parent
        self.attribute = attribute
        self.percentage = None
        self.is_fixed = True
        if isinstance(spec, str):
            if spec[-1] == '%':
                self.value = None
                self.percentage = float(spec[:-1]) / 100
                self.is_fixed = False
            elif spec.endswith('em'):
                size = parse_value(spec[:-2], None)
                style = element.getStyle()
                self.value = size * style.getGlyphString('M').width
                self.value += element.padding * 2
            elif '.' in spec:
                self.value = float(spec)
            else:
                self.value = int(spec)
        elif spec is None:
            self.value = None
            self.is_fixed = False
        else:
            self.value = int(spec)

    def __repr__(self):
        return '<%s %r on %s id %s>'%(self.__class__.__name__, self.spec,
            self.parent.__class__.__name__, self.parent.id)

    def __hash__(self):
        return hash(self.id)

    def specified(self):
        '''Return the value specified (ie. not using the intrinsic
        dimension as a fallback.
        '''
        if self.percentage is not None:
            pv = getattr(self.parent, self.attribute)
            if pv is None:
                return None
            pv = getattr(self.parent, 'inner_' + self.attribute)
            return intceil(pv * self.percentage)
        return self.value

    def calculate(self):
        '''Determine this dimension falling back on the element's intrinsic
        properties if necessary.
        '''
        if self.percentage is not None:
            pv = getattr(self.parent, self.attribute)
            if pv is None:
                return None
            pv = getattr(self.parent, 'inner_' + self.attribute)
            return pv * self.percentage
        elif self.value is None:
            if self.attribute == 'width':
                return self.element.intrinsic_width()
            else:
                return self.element.intrinsic_height()
        return self.value

class Position(Dimension):
    def calculate(self):
        '''Determine this dimension falling back on the element's intrinsic
        properties if necessary.
        '''
        if self.percentage is not None:
            pv = getattr(self.parent, self.attribute)
            if pv is None:
                return None
            pv = getattr(self.parent.inner_rect, self.attribute)
            return pv * self.percentage
        elif self.value is None:
            return 0
        return self.value


def parse_color(value):
    '''Parse a color value which is one of:

        name    a color name (CSS 2.1 standard colors)
        RGB     a three-value hex color
        RRGGBB  a three-value hex color
    '''
    from layout.base import Color
    if not isinstance(value, str):
        return value
    if value in Color.names:
        return Color.names[value]
    return Color.from_hex(value)

has_fbo = None

def renderToTexture(w, h, function):
    import ctypes
    from pyglet import gl
    from pyglet import image
    from pyglet.gl import gl_info
    global has_fbo
    if has_fbo is None:
        has_fbo = gl_info.have_extension('GL_EXT_framebuffer_object')

    # enforce dimensions are ints
    w, h = int(w), int(h)

    # set up viewport
    gl.glPushAttrib(gl.GL_VIEWPORT_BIT|gl.GL_TRANSFORM_BIT)

    gl.glViewport(0, 0, w, h)
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPushMatrix()
    gl.glLoadIdentity()
    gl.glOrtho(0, w, 0, h, -1, 1)
    gl.glMatrixMode(gl.GL_MODELVIEW)

    if has_fbo:
        # render directly to texture

        # create our frame buffer
        fbo = gl.GLuint()
        gl.glGenFramebuffersEXT(1, ctypes.byref(fbo))
        gl.glBindFramebufferEXT(gl.GL_FRAMEBUFFER_EXT, fbo)

        # allocate a texture and add to the frame buffer
        tex = image.Texture.create_for_size(gl.GL_TEXTURE_2D, w, h, gl.GL_RGBA)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex.id)
        gl.glFramebufferTexture2DEXT(gl.GL_FRAMEBUFFER_EXT,
            gl.GL_COLOR_ATTACHMENT0_EXT, gl.GL_TEXTURE_2D, tex.id, 0)

        status = gl.glCheckFramebufferStatusEXT(gl.GL_FRAMEBUFFER_EXT)
        assert status == gl.GL_FRAMEBUFFER_COMPLETE_EXT

        # now render
        gl.glBindFramebufferEXT(gl.GL_FRAMEBUFFER_EXT, fbo)
        function()
        gl.glBindFramebufferEXT(gl.GL_FRAMEBUFFER_EXT, 0)

        # clean up
        gl.glDeleteFramebuffersEXT(1, ctypes.byref(fbo))

    else:
        # render and copy to texture
        # render
        function()

        # grab the buffer and copy contents to the texture
        buffer = image.get_buffer_manager().get_color_buffer()
        tex = image.Texture.create_for_size(gl.GL_TEXTURE_2D, w, h, gl.GL_RGBA)
        tex.blit_into(buffer.get_region(0, 0, w, h), 0, 0, 0)

    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPopMatrix()
    gl.glPopAttrib()

    # return the region (the whole texture will most likely be larger)
    return tex.get_region(0, 0, w, h)


class Rect(object):
    def __init__(self, x, y, width, height):
        self.x = x; self.y = y
        self.width = width; self.height = height

    def __nonzero__(self):
        return bool(self.width and self.height)

    def __repr__(self):
        return 'Rect(xy=%.4g,%.4g; wh=%.4g,%.4g)'%(self.x, self.y,
            self.width, self.height)

    def __eq__(self, other):
        '''Compare the two rects.

        >>> r1 = Rect(0, 0, 10, 10)
        >>> r1 == Rect(0, 0, 10, 10)
        True
        >>> r1 == Rect(1, 0, 10, 10)
        False
        >>> r1 == Rect(0, 1, 10, 10)
        False
        >>> r1 == Rect(0, 0, 11, 10)
        False
        >>> r1 == Rect(0, 0, 10, 11)
        False
        '''
        return (self.x == other.x and self.y == other.y and
            self.width == other.width and  self.height == other.height)

    def __ne__(self, other):
        '''Compare the two rects.

        >>> r1 = Rect(0, 0, 10, 10)
        >>> r1 != Rect(0, 0, 10, 10)
        False
        >>> r1 != Rect(1, 0, 10, 10)
        True
        >>> r1 != Rect(0, 1, 10, 10)
        True
        >>> r1 != Rect(0, 0, 11, 10)
        True
        >>> r1 != Rect(0, 0, 10, 11)
        True
        '''
        return not (self == other)

    def copy(self):
        return self.__class__(self.x, self.y, self.width, self.height)

    def clippedBy(self, other):
        '''Determine whether this rect is clipped by the other rect.

        >>> r1 = Rect(0, 0, 10, 10)
        >>> r2 = Rect(1, 1, 9, 9)
        >>> r2.clippedBy(r1)
        False
        >>> r1.clippedBy(r2)
        True
        >>> r2 = Rect(1, 1, 11, 11)
        >>> r1.intersect(r2)
        Rect(xy=1,1; wh=9,9)
        >>> r1.clippedBy(r2)
        True
        >>> r2.intersect(r1)
        Rect(xy=1,1; wh=9,9)
        >>> r2.clippedBy(r1)
        True
        >>> r2 = Rect(11, 11, 1, 1)
        >>> r1.clippedBy(r2)
        True
        '''
        i = self.intersect(other)
        if i is None: return True
        if i.x > self.x: return True
        if i.y > self.y: return True
        if i.width < self.width: return True
        if i.height < self.height: return True
        return False

    def intersect(self, other):
        '''Find the intersection of two rects defined as tuples (x, y, w, h).

        >>> r1 = Rect(0, 51, 200, 17)
        >>> r2 = Rect(0, 64, 200, 55)
        >>> r1.intersect(r2)
        Rect(xy=0,64; wh=200,4)

        >>> r1 = Rect(0, 64, 200, 55)
        >>> r2 = Rect(0, 0, 200, 17)
        >>> print r1.intersect(r2)
        None

        >>> r1 = Rect(10, 10, 10, 10)
        >>> r2 = Rect(20, 20, 10, 10)
        >>> print r1.intersect(r2)
        None

        >>> bool(Rect(0, 0, 1, 1))
        True
        >>> bool(Rect(0, 0, 1, 0))
        False
        >>> bool(Rect(0, 0, 0, 1))
        False
        >>> bool(Rect(0, 0, 0, 0))
        False
        '''
        s_tr_x, s_tr_y = self.topright
        o_tr_x, o_tr_y = other.topright
        bl_x = max(self.x, other.x)
        bl_y = max(self.y, other.y)
        tr_x = min(s_tr_x, o_tr_x)
        tr_y = min(s_tr_y, o_tr_y)
        w, h = max(0, tr_x-bl_x), max(0, tr_y-bl_y)
        if not w or not h:
            return None
        return self.__class__(bl_x, bl_y, w, h)

    def get_top(self): return self.y + self.height
    def set_top(self, y): self.y = y - self.height
    top = property(get_top, set_top)

    def get_bottom(self): return self.y
    def set_bottom(self, y): self.y = y
    bottom = property(get_bottom, set_bottom)

    def get_left(self): return self.x
    def set_left(self, x): self.x = x
    left = property(get_left, set_left)

    def get_right(self): return self.x + self.width
    def set_right(self, x): self.x = x - self.width
    right = property(get_right, set_right)

    def get_center(self):
        return (self.x + self.width//2, self.y + self.height//2)
    def set_center(self, center):
        x, y = center
        self.x = x - self.width//2
        self.y = y - self.height//2
    center = property(get_center, set_center)

    def get_midtop(self):
        return (self.x + self.width//2, self.y + self.height)
    def set_midtop(self, midtop):
        x, y = midtop
        self.x = x - self.width//2
        self.y = y - self.height
    midtop = property(get_midtop, set_midtop)

    def get_midbottom(self):
        return (self.x + self.width//2, self.y)
    def set_midbottom(self, midbottom):
        x, y = midbottom
        self.x = x - self.width//2
        self.y = y
    midbottom = property(get_midbottom, set_midbottom)

    def get_midleft(self):
        return (self.x, self.y + self.height//2)
    def set_midleft(self, midleft):
        x, y = midleft
        self.x = x
        self.y = y - self.height//2
    midleft = property(get_midleft, set_midleft)

    def get_midright(self):
        return (self.x + self.width, self.y + self.height//2)
    def set_midright(self, midright):
        x, y = midright
        self.x = x - self.width
        self.y = y - self.height//2
    midright = property(get_midright, set_midright)
 
    def get_topleft(self):
        return (self.x, self.y + self.height)
    def set_topleft(self, pos):
        x, y = pos
        self.x = x
        self.y = y - self.height
    topleft = property(get_topleft, set_topleft)
 
    def get_topright(self):
        return (self.x + self.width, self.y + self.height)
    def set_topright(self, pos):
        x, y = pos
        self.x = x - self.width
        self.y = y - self.height
    topright = property(get_topright, set_topright)
 
    def get_bottomright(self):
        return (self.x + self.width, self.y)
    def set_bottomright(self, pos):
        x, y = pos
        self.x = x - self.width
        self.y = y
    bottomright = property(get_bottomright, set_bottomright)
 
    def get_bottomleft(self):
        return (self.x, self.y)
    def set_bottomleft(self, pos):
        self.x, self.y = pos
    bottomleft = property(get_bottomleft, set_bottomleft)


if __name__ == "__main__":
    import doctest
    doctest.testmod()

