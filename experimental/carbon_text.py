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

class ATSFontFilterUnion(Union):
    # Types not correct
    _fields_ = [
        ('generationFilter', c_void_p),
        ('fontFamilyFilter', c_void_p),
        ('fontFamilyApplierFunctionFilter', c_void_p),
        ('fontApplierFunctionFilter', c_void_p)
    ]

class ATSFontFilter(Structure):
    _fields_ = [
        ('version', c_uint32),
        ('filterSelector', c_int),
        ('filter', ATSFontFilterUnion)
    ]

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

'''
Iterate over fonts of a family..

family_name = _create_cfstring('Lucinda Grande')
family_ref = carbon.ATSFontFamilyFindFromName(family_name, 0)
# release family_name

filter = ATSFontFilter()
filter.version = 0
filter.filterSelector = kATSFontFilterSelectorFontFamily
iterator = c_void_p()

carbon.ATSFontIteratorCreate(
    kATSFontContextUnspecified, # Future: use local when not system font
    filter,
    c_void_p,
    kATSOptionFlagsRestrictedScope,
    byref(iterator))


ats_font = c_void_p()
carbon.ATSFontIteratorNext(iterator, byref(ats_font))
# XXX unfinished

carbon.ATSFontIteratorRelease(byref(iterator))
'''


'''
# Create font by name and size
cf_font_name = _create_cfstring('Baskerville')
carbon.ATSFontFindFromName.restype = POINTER(c_int)
ats_font = carbon.ATSFontFindFromName(cf_font_name, 0)
carbon.CGFontCreateWithPlatformFont.restype = c_void_p
font = carbon.CGFontCreateWithPlatformFont(byref(ats_font))
carbon.CGContextSetFont(context, font)
carbon.CGContextSetFontSize(context, c_float(24.))
#carbon.CGContextSelectFont(context, "Lucida Grande", c_float(16.), 1)

#carbon.CGContextShowTextAtPoint(context, c_float(40), c_float(40), "Hello", 5)

glyphs = (CGGlyph * 100)(*range(65,100))
carbon.CGContextShowGlyphsAtPoint(context, c_float(20.), c_float(20.), 
    glyphs, len(glyphs))
'''

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

def create_atsu_layout(attributes):
    text_layout = c_void_p()
    carbon.ATSUCreateTextLayout(byref(text_layout))

    if attributes:
        # attributes is a dict of ATSUAttributeTag => ctypes value
        tags, values = zip(*attributes.items())
        tags = (c_int * len(tags))(*tags)
        sizes = (c_uint * len(values))(*[sizeof(v) for v in values])
        values = (c_void_p * len(values))(*[cast(pointer(v), c_void_p) \
                                            for v in values])

        carbon.ATSUSetLayoutControls(text_layout, len(tags), tags, sizes, values)
    return text_layout

def str_ucs2(text):
    if byteorder == 'big':
        text = text.encode('utf_16_be')
    else:
        text = text.encode('utf_16_le')   # explicit endian avoids BOM
    return create_string_buffer(text + '\0')

class Font(object):
    def __init__(self, name, size):
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
            kATSURGBAlphaColorTag: ATSURGBAlphaColor(1, 1, 1, 1)
        }
        self.atsu_style = create_atsu_style(attributes)

class Glyph(object):
    def __init__(self, tex_id, vertices, tex_coords, advance):
        '''
            tex_id: GL texture to bind
            vertices: (x1, y1, x2, y2) relative to baseline before
                left-side bearing.  x1y1 is lower left, x2y2 is upper right.
            tex_coords: (u1, v1, u2, v2) texture coordinates for vertices.
            advance: right-side bearing relative to LSB.
        '''
        self.tex_id = tex_id
        self.vertices = vertices
        self.tex_coords = tex_coords
        self.advance = advance

    def draw(self):
        '''Debug method: use the higher level APIs for performance and
        kerning.'''
        glBindTexture(GL_TEXTURE_2D, self.tex_id)
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

class GlyphTexture(Texture):
    x = 0
    y = 0
    line_height = 0

    def allocate(self, width, height):
        '''Returns (x, y) position for a new glyph, and reserves that
        space.'''
        if self.x + width > self.width:
            self.x = 0
            self.y += self.line_height
            self.line_height = 0
        if self.y + height > self.height:
            raise Error('No more room in this GlyphTexture')

        self.line_height = max(self.line_height, height)
        x = self.x
        self.x += width
        return x, self.y

class GlyphRenderer(object):
    _bitmap = None
    _bitmap_context = None
    _bitmap_rect = None

    def __init__(self, font):
        self._create_bitmap_context(256, 256)
        self.font = font

    def __del__(self):
        if self._bitmap_context:
            carbon.CGContextRelease(self._bitmap_context)

    def render(self, text, glyph_texture):
        # Convert text to UCS2
        text_len = len(text)
        text = str_ucs2(text)

        # Create ATSU text layout for this text and font
        attributes = {
            kATSUCGContextTag: self._bitmap_context,
        }
        layout = create_atsu_layout(attributes)
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
        image_height = rect.bottom - rect.top + 1
        baseline = rect.bottom
        lsb = rect.left
        vertices = (
            float(rect.left), 
            -float(rect.bottom), 
            float(rect.right)+1, 
            -float(rect.top)+1)  # +1 looks wrong but works.

        # Resize Quartz context if necessary
        if (image_width > self._bitmap_rect.size.width or
            image_height > self._bitmap_rect.size.height):
            self._create_bitmap_context(
                max(image_width, self._bitmap_rect.size.width),
                max(image_height, self._bitmap_rect.size.height))

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
        advance = fix2float(bounds.upperRight.x) - fix2float(bounds.lowerLeft.x)

        # Draw to the bitmap
        carbon.CGContextClearRect(self._bitmap_context, self._bitmap_rect)
        carbon.ATSUDrawText(layout,
            0,
            kATSUToTextEnd,
            fixed(-lsb), fixed(baseline)) 

        # Find out where to place it within the texture
        x, y = glyph_texture.allocate(image_width, image_height)
        
        # Copy bitmap into the texture.
        glPushClientAttrib(GL_CLIENT_PIXEL_STORE_BIT)
        glBindTexture(GL_TEXTURE_2D, glyph_texture.id)
        glPixelStorei(GL_UNPACK_ROW_LENGTH, int(self._bitmap_rect.size.width))
        glPixelStorei(GL_UNPACK_SKIP_ROWS, 
            int(self._bitmap_rect.size.height - image_height))
        glTexSubImage2D(GL_TEXTURE_2D, 0,
            x, y,
            image_width,
            image_height,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            self._bitmap)
        glPopClientAttrib()

        tex_coords = (
            float(x) / glyph_texture.width,
            float(y + image_height) / glyph_texture.height,
            float(x + image_width) / glyph_texture.width,
            float(y) / glyph_texture.height)

        return Glyph(glyph_texture.id, vertices, tex_coords, advance)

    def _create_bitmap_context(self, width, height):
        '''Create or recreate bitmap and Quartz context.'''
        if self._bitmap_context:
            carbon.ReleaseContext(self._bitmap_context)
        components = 4
        pitch = width * components
        self._bitmap = (c_ubyte * (width * height * components))()
        color_space = carbon.CGColorSpaceCreateDeviceRGB()
        context = carbon.CGBitmapContextCreate(self._bitmap, 
            width, height, 8, pitch, 
            color_space, kCGImageAlphaPremultipliedLast)
        carbon.CGColorSpaceRelease(color_space)

        # XXX need this?
        carbon.CGContextSetRGBFillColor(context, 
            c_float(1), c_float(1), c_float(1), c_float(1))
        carbon.CGContextSetTextDrawingMode(context, kCGTextFill)

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
        
# Create layout
# Draw
'''
glyphs = (CGGlyph * 100)(*range(65,100))
carbon.CGContextShowGlyphsAtPoint(context, c_float(20.), c_float(20.), 
    glyphs, len(glyphs))
#carbon.CGContextShowTextAtPoint(context, c_float(40), c_float(40), "Hello", 5)

carbon.CGFontRelease(font)
'''

#carbon.CGContextFlush(context)
'''
image = RawImage(data, width, height, 'RGBA', GL_UNSIGNED_BYTE,
top_to_bottom=True)
carbon.CGContextRelease(context)
'''

glClearColor(.5, 0, 0, 1)
glClear(GL_COLOR_BUFFER_BIT)
glMatrixMode(GL_PROJECTION)
glOrtho(0, window.width, 0, window.height, -1, 1)
glMatrixMode(GL_MODELVIEW)

texture = GlyphTexture.create(256, 256, GL_LUMINANCE_ALPHA)
font = Font('Baskerville', 12)
renderer = GlyphRenderer(font)
glyphs = {}
for c in 'Mabcdefghijklmnopqrstuvwxyz.T. ':
    glyphs[c] = renderer.render(c, texture)
del renderer

texture.draw()
glEnable(GL_BLEND)
glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA) # this is premultiplied alpha!
glTranslatef(0, 20, 0)

'''
# Draw baseline
glDisable(GL_TEXTURE_2D)
glBegin(GL_LINES)
glVertex2f(0,0)
glVertex2f(1000,0)
glEnd()
'''


glEnable(GL_TEXTURE_2D)
for c in 'Mr. T.g':
    glyphs[c].draw()
    glTranslatef(glyphs[c].advance, 0, 0)

window.flip()

exit = ExitHandler()
window.push_handlers(exit)
while not exit.exit:
    window.dispatch_events()
