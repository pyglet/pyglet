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
from pyglet.window.carbon.types import CGRect

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

carbon.CGColorSpaceCreateWithName.restype = c_void_p
carbon.CGBitmapContextCreate.restype = POINTER(c_void_p)

height = 256
width = 256

window = Window(width, height)

components = 4
pitch = width * components
data = (c_ubyte * (width * height * components))()
color_space = carbon.CGColorSpaceCreateDeviceRGB()
context = carbon.CGBitmapContextCreate(data, width, height, 8, pitch, 
    color_space, kCGImageAlphaPremultipliedLast)
carbon.CGColorSpaceRelease(color_space)

carbon.CGContextSetRGBStrokeColor(context, c_float(1), c_float(1), c_float(1),
    c_float(1))
carbon.CGContextSetRGBFillColor(context, c_float(1), c_float(1), c_float(1),
    c_float(1))
carbon.CGContextSetTextDrawingMode(context, kCGTextFill)


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

# Find font by name
font_name = 'Baskerville'
font_id = ATSUFontID()
carbon.ATSUFindFontFromName(
    font_name,
    len(font_name),
    kFontFullName,
    kFontNoPlatformCode,
    kFontNoScriptCode,
    kFontNoLanguageCode,
    byref(font_id))

# Create style for font, including output context
attributes = {
    kATSUSizeTag: fixed(24.),
    kATSUFontTag: font_id,
    kATSURGBAlphaColorTag: ATSURGBAlphaColor(1, 1, 1, 1)
}
style = create_atsu_style(attributes)

# Create UCS2 array from str
text = u'Hello world.'
text_len = len(text)
text = str_ucs2(text)
#print cast(text, POINTER(c_byte * len(text))).contents[:]

# Create layout
attributes = {
    kATSUCGContextTag: context,
}
text_layout = create_atsu_layout(attributes)
carbon.ATSUSetTextPointerLocation(text_layout,
    text,
    kATSUFromTextBeginning,
    kATSUToTextEnd,
    text_len)
carbon.ATSUSetRunStyle(text_layout, style, 
    kATSUFromTextBeginning, kATSUToTextEnd)
carbon.ATSUSetTransientFontMatching(text_layout, True)

# Draw
carbon.ATSUDrawText(text_layout,
    0,
    kATSUToTextEnd,
    fixed(5), fixed(5))

'''
glyphs = (CGGlyph * 100)(*range(65,100))
carbon.CGContextShowGlyphsAtPoint(context, c_float(20.), c_float(20.), 
    glyphs, len(glyphs))
#carbon.CGContextShowTextAtPoint(context, c_float(40), c_float(40), "Hello", 5)

carbon.CGFontRelease(font)
'''

#carbon.CGContextFlush(context)
image = RawImage(data, width, height, 'RGBA', GL_UNSIGNED_BYTE,
top_to_bottom=True)
carbon.CGContextRelease(context)

glClearColor(1, 1, 1, 1)
glClear(GL_COLOR_BUFFER_BIT)
glMatrixMode(GL_PROJECTION)
glOrtho(0, window.width, 0, window.height, -1, 1)
glMatrixMode(GL_MODELVIEW)
texture = image.texture()
texture.draw()

window.flip()

exit = ExitHandler()
window.push_handlers(exit)
while not exit.exit:
    window.dispatch_events()
