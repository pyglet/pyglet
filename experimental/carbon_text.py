#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from sys import byteorder
from ctypes import *

from pyglet.GL.VERSION_1_1 import *
from pyglet.window import *
from pyglet.window.event import *
from pyglet.image import *
from pyglet.window.carbon import carbon 
from pyglet.window.carbon import _create_cfstring
from pyglet.window.carbon.types import Rect, CGRect

Fixed = c_int32

class FixedPoint(Structure):
    _fields_ = [
        ('x', Fixed),
        ('y', Fixed)
    ]

class ATSTrapezoid(Structure):
    _fields_ = [
        ('upperLeft', FixedPoint),
        ('upperRight', FixedPoint),
        ('lowerRight', FixedPoint),
        ('lowerLeft', FixedPoint)
    ]

# TODO: most of the ATS and CG here not used any more.

CGGlyph = c_ushort
ATSUFontID = c_uint32
RGBColor = c_short * 3
ATSURGBAlphaColor = c_float * 4

kCGImageAlphaNone = 0
kCGImageAlphaPremultipliedLast = 1
kCGTextFill = 0

kATSFontContextUnspecified = 0
kATSFontContextGlobal = 1
kATSFontContextLocal = 2

kATSFontFilterSelectorUnspecified = 0
kATSFontFilterSelectorGeneration = 3
kATSFontFilterSelectorFontFamily = 7
kATSFontFilterSelectorFontFamilyApplierFunction = 8
kATSFontFilterSelectorFontApplierFunction = 9

kATSOptionFlagsDoNotNotify = 0x00000001 << 8
kATSOptionFlagsIterationScopeMask = 0x00000007 << 12
kATSOptionFlagsDefaultScope = 0x00000000 << 12
kATSOptionFlagsUnRestrictedScope = 0x00000001 << 12
kATSOptionFlagsRestrictedScope = 0x00000002 << 12
kATSOptionFlagsProcessSubdirectories = 0x00000001 << 6

kATSUFromTextBeginning = c_ulong(0xFFFFFFFF)
kATSUToTextEnd = c_ulong(0xFFFFFFFF)

kATSUQDBoldfaceTag            = 256
kATSUQDItalicTag              = 257
kATSUFontTag                  = 261
kATSUSizeTag                  = 262
kATSUCGContextTag             = 32767
kATSUColorTag                 = 263
kATSURGBAlphaColorTag         = 288

kATSULineWidthTag             = 1


kFontFullName                 = 4
kFontNoPlatformCode           = c_ulong(-1)
kFontNoScriptCode             = c_ulong(-1)
kFontNoLanguageCode           = c_ulong(-1)

kATSUseDeviceOrigins          = 1


carbon.CGColorSpaceCreateWithName.restype = c_void_p
carbon.CGBitmapContextCreate.restype = POINTER(c_void_p)

height = 256
width = 256

window = Window(width, height)


def fixed(value):
    # This is a guess... could easily be wrong
    #return c_int32(int(value) * (1 << 16))

    return c_int32(carbon.Long2Fix(c_long(int(value))))

carbon.Fix2X.restype = c_double
def fix2float(value):
    return carbon.Fix2X(value)

def create_atsu_style(attributes):
    # attributes is a dict of ATSUAttributeTag => ctypes value
    tags, values = zip(*attributes.items())
    tags = (c_int * len(tags))(*tags)
    sizes = (c_uint * len(values))(*[sizeof(v) for v in values])
    values = (c_void_p * len(values))(*[cast(pointer(v), c_void_p) \
                                        for v in values])

    style = c_void_p()
    carbon.ATSUCreateStyle(byref(style))
    carbon.ATSUSetAttributes(style, len(tags), tags, sizes, values)
    return style

def set_layout_attributes(layout, attributes):
    if attributes:
        # attributes is a dict of ATSUAttributeTag => ctypes value
        tags, values = zip(*attributes.items())
        tags = (c_int * len(tags))(*tags)
        sizes = (c_uint * len(values))(*[sizeof(v) for v in values])
        values = (c_void_p * len(values))(*[cast(pointer(v), c_void_p) \
                                            for v in values])

        carbon.ATSUSetLayoutControls(layout, len(tags), tags, sizes, values)

def str_ucs2(text):
    if byteorder == 'big':
        text = text.encode('utf_16_be')
    else:
        text = text.encode('utf_16_le')   # explicit endian avoids BOM
    return create_string_buffer(text + '\0')

# XXX NewTextureAtlas to become AllocatingTextureAtlas(TextureAtlas)
#     NewTextureSubImage to become TextureSubImage.

class NewTextureAtlasOutOfSpaceException(ImageException):
    pass

class NewTextureSubImage(object):
    def __init__(self, texture, x, y, width, height):
        self.texture_id = texture.id
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.tex_coords = (
            float(x) / texture.width,
            float(y) / texture.height,
            float(x + width) / texture.width,
            float(y + height) / texture.height)

    def flip_vertical(self):
        self.tex_coords = (
            self.tex_coords[0], 
            self.tex_coords[3], 
            self.tex_coords[2],
            self.tex_coords[1])

class NewTextureAtlas(Texture):
    x = 0
    y = 0
    line_height = 0
    subimage_class = NewTextureSubImage

    def allocate(self, width, height):
        '''Returns (x, y) position for a new glyph, and reserves that
        space.'''
        if self.x + width > self.width:
            self.x = 0
            self.y += self.line_height
            self.line_height = 0
        if self.y + height > self.height:
            raise NewTextureAtlasOutOfSpaceException()

        self.line_height = max(self.line_height, height)
        x = self.x
        self.x += width
        return self.subimage_class(self, x, self.y, width, height)

class Glyph(NewTextureSubImage):
    advance = 0
    vertices = (0, 0, 0, 0)

    def set_bearings(self, baseline, left_side_bearing, advance):
        self.advance = advance
        self.vertices = (
            left_side_bearing,
            -baseline,
            left_side_bearing + self.width,
            -baseline + self.height)

    def draw(self):
        '''Debug method: use the higher level APIs for performance and
        kerning.'''
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glBegin(GL_QUADS)
        glTexCoord2f(self.tex_coords[0], self.tex_coords[1])
        glVertex2f(self.vertices[0], self.vertices[1])
        glTexCoord2f(self.tex_coords[2], self.tex_coords[1])
        glVertex2f(self.vertices[2], self.vertices[1])
        glTexCoord2f(self.tex_coords[2], self.tex_coords[3])
        glVertex2f(self.vertices[2], self.vertices[3])
        glTexCoord2f(self.tex_coords[0], self.tex_coords[3])
        glVertex2f(self.vertices[0], self.vertices[3])
        glEnd()

    def get_kerning_pair(self, right_glyph):
        return 0

class GlyphTextureAtlas(NewTextureAtlas):
    subimage_class = Glyph

class StyledText(object):
    '''One contiguous sequence of characters sharing the same
    GL state.'''
    # TODO Not there yet: must be split on texture atlas changes.
    def __init__(self, text, font):
        self.text = text
        self.font = font
        self.glyphs = font.get_glyphs(text)

class TextLayout(object):
    '''Will eventually handle all complex layout, line breaking,
    justification and state sorting/coalescing.'''
    def __init__(self, styled_texts):
        self.styled_texts = styled_texts

    def draw(self):
        glPushMatrix()
        for styled_text in self.styled_texts:
            styled_text.font.apply_blend_state()
            for glyph in styled_text.glyphs:
                glyph.draw()
                glTranslatef(glyph.advance, 0, 0)
        glPopMatrix()

class Font(object):
    texture_width = 256
    texture_height = 256

    # TODO: a __new__ method to instantiate correct Font for platform

    def __init__(self):
        self.textures = []
        self.glyphs = {}

    # TODO: static add_font(file) and add_font_directory(dir) methods.

    def create_glyph_texture(self):
        texture = GlyphTextureAtlas.create(
            self.texture_width,
            self.texture_height,
            GL_LUMINANCE_ALPHA)
        return texture

    def apply_blend_state(self):
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)

    def allocate_glyph(self, width, height):
        # Search atlases for a free spot
        for texture in self.textures:
            try:
                return texture.allocate(width, height)
            except NewTextureAtlasOutOfSpaceException:
                pass

        # If requested glyph size is bigger than atlas size, increase
        # next atlas size.  A better heuristic could be applied earlier
        # (say, if width is > 1/4 texture_width).
        if width > self.texture_width or height > self.texture_height:
            self.texture_width, self.texture_height, u, v= \
                Texture.get_texture_size(width * 2, height * 2)

        texture = self.create_glyph_texture()
        self.textures.insert(0, texture)

        # This can't fail.
        return texture.allocate(width, height)

    def get_glyph_renderer(self):
        raise NotImplementedError('Subclass must override')

    def get_glyphs(self, text):
        glyph_renderer = None
        for c in text:
            if c not in self.glyphs:
                if not glyph_renderer:
                    glyph_renderer = self.get_glyph_renderer()
                self.glyphs[c] = glyph_renderer.render(c)
        return [self.glyphs[c] for c in text] 

    def render(self, text):
        return TextLayout([StyledText(text, self)])

class GlyphRenderer(object):
    def render(self, text):
        pass

class CarbonFont(Font):
    def __init__(self, name, size, bold=False, italic=False):
        super(CarbonFont, self).__init__()

        font_id = ATSUFontID()
        carbon.ATSUFindFontFromName(
            name,
            len(name),
            kFontFullName,
            kFontNoPlatformCode,
            kFontNoScriptCode,
            kFontNoLanguageCode,
            byref(font_id))

        attributes = {
            kATSUSizeTag: fixed(size),
            kATSUFontTag: font_id,
            kATSURGBAlphaColorTag: ATSURGBAlphaColor(1, 1, 1, 1),
            kATSUQDBoldfaceTag: c_byte(bold),
            kATSUQDItalicTag: c_byte(italic)
        }
        self.atsu_style = create_atsu_style(attributes)

    def apply_blend_state(self):
        # Textures have premultiplied alpha
        glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)

    def get_glyph_renderer(self):
        return CarbonGlyphRenderer(self)

class CarbonGlyphRenderer(object):
    _bitmap = None
    _bitmap_context = None
    _bitmap_rect = None

    def __init__(self, font):
        self._create_bitmap_context(256, 256)
        self.font = font

    def __del__(self):
        if self._bitmap_context:
            carbon.CGContextRelease(self._bitmap_context)

    def render(self, text):
        # Convert text to UCS2
        text_len = len(text)
        text = str_ucs2(text)

        # Create ATSU text layout for this text and font
        layout = c_void_p()
        carbon.ATSUCreateTextLayout(byref(layout))
        set_layout_attributes(layout, {
            kATSUCGContextTag: self._bitmap_context})
        carbon.ATSUSetTextPointerLocation(layout,
            text,
            kATSUFromTextBeginning,
            kATSUToTextEnd,
            text_len)
        carbon.ATSUSetRunStyle(layout, self.font.atsu_style, 
            kATSUFromTextBeginning, kATSUToTextEnd)
        carbon.ATSUSetTransientFontMatching(layout, True)

        # Get bitmap dimensions required
        rect = Rect()
        carbon.ATSUMeasureTextImage(layout, 
            kATSUFromTextBeginning,
            kATSUToTextEnd,
            0, 0,
            byref(rect))
        image_width = rect.right - rect.left + 1
        image_height = rect.bottom - rect.top + 2
        baseline = rect.bottom + 1
        lsb = rect.left
        
        # Resize Quartz context if necessary
        if (image_width > self._bitmap_rect.size.width or
            image_height > self._bitmap_rect.size.height):
            self._create_bitmap_context(
                int(max(image_width, self._bitmap_rect.size.width)),
                int(max(image_height, self._bitmap_rect.size.height)))
            
            set_layout_attributes(layout, {
                kATSUCGContextTag: self._bitmap_context})

        # Get typographic box, which gives advance.
        bounds_actual = c_uint32()
        bounds = ATSTrapezoid()
        carbon.ATSUGetGlyphBounds(
            layout,
            0, 0,
            kATSUFromTextBeginning,
            kATSUToTextEnd,
            kATSUseDeviceOrigins,
            1,
            byref(bounds),
            byref(bounds_actual))
        advance = fix2float(bounds.lowerRight.x) - fix2float(bounds.lowerLeft.x)

        # Draw to the bitmap
        carbon.CGContextClearRect(self._bitmap_context, self._bitmap_rect)
        carbon.ATSUDrawText(layout,
            0,
            kATSUToTextEnd,
            fixed(-lsb), fixed(baseline)) 

        # Allocate space within an atlas
        glyph = self.font.allocate_glyph(image_width, image_height)
        glyph.flip_vertical()
        glyph.set_bearings(baseline, lsb, advance)
       
        # Copy bitmap into the texture.
        glPushClientAttrib(GL_CLIENT_PIXEL_STORE_BIT)
        glBindTexture(GL_TEXTURE_2D, glyph.texture_id)
        glPixelStorei(GL_UNPACK_ROW_LENGTH, int(self._bitmap_rect.size.width))
        glPixelStorei(GL_UNPACK_SKIP_ROWS, 
            int(self._bitmap_rect.size.height - image_height))
        glTexSubImage2D(GL_TEXTURE_2D, 0,
            glyph.x, glyph.y,
            image_width,
            image_height,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            self._bitmap)
        glPopClientAttrib()

        return glyph

    def _create_bitmap_context(self, width, height):
        '''Create or recreate bitmap and Quartz context.'''
        if self._bitmap_context:
            carbon.CGContextRelease(self._bitmap_context)
        components = 4
        pitch = width * components
        self._bitmap = (c_ubyte * (pitch * height))()
        color_space = carbon.CGColorSpaceCreateDeviceRGB()
        context = carbon.CGBitmapContextCreate(self._bitmap, 
            width, height, 8, pitch, 
            color_space, kCGImageAlphaPremultipliedLast)
        carbon.CGColorSpaceRelease(color_space)

        # Disable RGB decimated antialiasing, use standard
        # antialiasing which won't break alpha.
        carbon.CGContextSetShouldSmoothFonts(context, False)
        carbon.CGContextSetShouldAntialias(context, True)

        self._bitmap_context = context 
        self._bitmap_rect = CGRect()
        self._bitmap_rect.origin.x = 0
        self._bitmap_rect.origin.y = 0
        self._bitmap_rect.size.width = width
        self._bitmap_rect.size.height = height
        


glClearColor(.5, 0, 0, 1)
glClear(GL_COLOR_BUFFER_BIT)
glMatrixMode(GL_PROJECTION)
glOrtho(0, window.width, 0, window.height, -1, 1)
glMatrixMode(GL_MODELVIEW)

glEnable(GL_TEXTURE_2D)
font = CarbonFont('Zapfino', 36)
glTranslatef(0, 20, 0)
font.render('Hello, world!').draw()

'''
# Draw baseline
glDisable(GL_TEXTURE_2D)
glBegin(GL_LINES)
glVertex2f(0,0)
glVertex2f(1000,0)
glEnd()
'''

window.flip()

exit = ExitHandler()
window.push_handlers(exit)
while not exit.exit:
    window.dispatch_events()
