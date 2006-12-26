#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from ctypes import *
from sys import byteorder

from pyglet.text import *
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

kATSUInvalidFontErr = -8796

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

class CarbonGlyphTextureAtlas(GlyphTextureAtlas):
    '''
    def apply_blend_state(self):
        # Textures have premultiplied alpha
        glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)
    '''

class CarbonGlyphRenderer(GlyphRenderer):
    _bitmap = None
    _bitmap_context = None
    _bitmap_rect = None

    def __init__(self, font):
        super(CarbonGlyphRenderer, self).__init__(font)
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
        image_width = rect.right - rect.left + 2
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
            fixed(-lsb + 1), fixed(baseline)) 

        # Allocate space within an atlas
        glyph = self.font.allocate_glyph(image_width, image_height)
        glyph.flip_vertical()
        glyph.set_bearings(baseline, lsb, advance)
       
        # Copy bitmap into the texture.
        glPushClientAttrib(GL_CLIENT_PIXEL_STORE_BIT)
        glBindTexture(GL_TEXTURE_2D, glyph.texture.id)
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
        

class CarbonFont(BaseFont):
    glyph_renderer_class = CarbonGlyphRenderer
    glyph_texture_atlas_class = CarbonGlyphTextureAtlas

    def __init__(self, name, size, bold=False, italic=False):
        super(CarbonFont, self).__init__()

        if not name:
            name = 'Helvetica'

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

        self.calculate_metrics()

    @classmethod
    def have_font(cls, name):
        font_id = ATSUFontID()
        r = carbon.ATSUFindFontFromName(
            name,
            len(name),
            kFontFullName,
            kFontNoPlatformCode,
            kFontNoScriptCode,
            kFontNoLanguageCode,
            byref(font_id)) 
        return r != kATSUInvalidFontErr

    def calculate_metrics(self):
        # It seems the only way to get the font's ascent and descent is to lay
        # out some glyphs and measure them.

        # This is a (pretend) UCS2 string
        text = '\0a'

        layout = c_void_p()
        carbon.ATSUCreateTextLayout(byref(layout))
        carbon.ATSUSetTextPointerLocation(layout,
            text,
            kATSUFromTextBeginning,
            kATSUToTextEnd,
            1)
        carbon.ATSUSetRunStyle(layout, self.atsu_style, 
            kATSUFromTextBeginning, kATSUToTextEnd)
        carbon.ATSUSetTransientFontMatching(layout, True)

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
        self.ascent = -fix2float(bounds.upperLeft.y)
        self.descent = -fix2float(bounds.lowerLeft.y)
        print self.ascent, self.descent


