# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright 
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

# TODO Tiger and later: need to set kWindowApplicationScaledAttribute for DPI
# independence?

from ctypes import *
import math

from pyglet.font import base
import pyglet.image

import Quartz, CoreFoundation, CoreText, Cocoa

class QuartzGlyphRenderer(base.GlyphRenderer):
    def __init__(self, font):
        super(QuartzGlyphRenderer, self).__init__(font)
        self.font = font

    def render(self, text):
        # Using CTLineDraw seems to be the only way to make sure that the text
        # is drawn with the specified font when that font is a graphics font loaded from
        # memory.  For whatever reason, [NSAttributedString drawAtPoint:] ignores
        # the graphics font if it not registered with the font manager.
        # So we just use CTLineDraw for both graphics fonts and installed fonts.

        ctFont = self.font.ctFont

        # Create an attributed string using text and font.
        attributes = CoreFoundation.CFDictionaryCreateMutable(None, 1, CoreFoundation.kCFTypeDictionaryKeyCallBacks, CoreFoundation.kCFTypeDictionaryValueCallBacks)
        CoreFoundation.CFDictionaryAddValue(attributes, CoreText.kCTFontAttributeName, ctFont)
        string = CoreFoundation.CFAttributedStringCreate(None, unicode(text), attributes)

        # Create a CTLine object to render the string.
        line = CoreText.CTLineCreateWithAttributedString(string)
        
        # Get a bounding rectangle for glyphs in string.
        result, glyphs = CoreText.CTFontGetGlyphsForCharacters(ctFont, text, None, len(text))
        rect, rects = CoreText.CTFontGetBoundingRectsForGlyphs(ctFont, 0, glyphs, None, len(glyphs))
        size = rect.size

        # Get advance for all glyphs in string.
        advance, advances = CoreText.CTFontGetAdvancesForGlyphs(ctFont, CoreText.kCTFontDefaultOrientation, glyphs, None, len(glyphs))

        # Set image parameters:
        # We add 2 pixels to the bitmap width and height so that there will be a 1-pixel border
        # around the glyph image when it is placed in the texture atlas.  This prevents
        # weird artifacts from showing up around the edges of the rendered glyph textures.
        # We adjust the baseline and lsb of the glyph by 1 pixel accordingly.
        width = max(int(math.ceil(rect.size.width) + 2), 1)
        height = max(int(math.ceil(rect.size.height) + 2), 1)
        baseline = -int(math.floor(rect.origin.y)) + 1
        lsb = int(math.floor(rect.origin.x)) - 1
        advance = int(round(advance))

        # Create bitmap context.
        bitsPerComponent = 8
        bytesPerRow = 4*width
        colorSpace = Quartz.CGColorSpaceCreateDeviceRGB()
        bitmap = Quartz.CGBitmapContextCreate(None, width, height, bitsPerComponent, bytesPerRow, colorSpace, Quartz.kCGImageAlphaPremultipliedLast)

        # Draw text to bitmap context.
        Quartz.CGContextSetShouldAntialias(bitmap, True)
        Quartz.CGContextSetTextPosition(bitmap, -lsb, baseline)
        CoreText.CTLineDraw(line, bitmap)

        # Create an image to get the data out.
        imageRef = Quartz.CGBitmapContextCreateImage(bitmap)

        bytesPerRow = Quartz.CGImageGetBytesPerRow(imageRef)
        imageData = Quartz.CGDataProviderCopyData(Quartz.CGImageGetDataProvider(imageRef))
        buffer = (c_byte * (height * bytesPerRow))()
        byteRange = CoreFoundation.CFRangeMake(0, CoreFoundation.CFDataGetLength(imageData))
        CoreFoundation.CFDataGetBytes(imageData, byteRange, buffer)

        pimage = pyglet.image.ImageData(width, height, 'RGBA', buffer, bytesPerRow)

        glyph = self.font.create_glyph(pimage)
        glyph.set_bearings(baseline, lsb, advance)
        t = list(glyph.tex_coords)
        glyph.tex_coords = t[9:12] + t[6:9] + t[3:6] + t[:3]
        
        return glyph

class QuartzFont(base.Font):
    glyph_renderer_class = QuartzGlyphRenderer
    _loaded_cgFont_table = {}

    def _create_font_with_traits(self, ctFont, bold, italic):
        # Setup the symbolic trait value from passed in flags.
        traitValue = 0
        if bold: traitValue |= CoreText.kCTFontBoldTrait
        if italic: traitValue |= CoreText.kCTFontItalicTrait
        # The symbolic trait mask is used to restrict which traits are changed.
        traitMask = CoreText.kCTFontBoldTrait | CoreText.kCTFontItalicTrait
        # Try to create a font in the same family as ctFont but with the desired traits.
        # Values of 0.0 for size and None for the text matrix preserve the values of the 
        # original font.  
        newFont = CoreText.CTFontCreateCopyWithSymbolicTraits(ctFont, 0.0, None, traitValue, traitMask)
        # If no font with the desired traits can be found, then return the original font.
        if newFont:
            return newFont
        else:
            return ctFont
        

    def __init__(self, name, size, bold=False, italic=False, dpi=None):
        super(QuartzFont, self).__init__()

        if not name: name = 'Helvetica'

        # I don't know what is the right thing to do here.
        if dpi is None: dpi = 96
        size = size * dpi / 72.0

        name = unicode(name)
        if name in self._loaded_cgFont_table:
            # Grab previously loaded cgFont from table and use it to 
            # create a CTFont object with the specified size.
            cgFont = self._loaded_cgFont_table[name]
            self.ctFont = CoreText.CTFontCreateWithGraphicsFont(cgFont, size, None, None)

            # Add the bold and italic traits if possible.
            if bold or italic:
                self.ctFont = _create_font_with_traits(self.ctFont, bold, italic)
        else:
            # Use Cocoa for non-graphics fonts, because it is easier to set the
            # font traits this way.  (I would use CTFontCreateWithFontDescriptor, but
            # I can't get PyObjC to do the right thing with the attributes dictionary)
            manager = Cocoa.NSFontManager.sharedFontManager()
                
            traits = 0
            if bold: traits |= Cocoa.NSBoldFontMask
            if italic: traits |= Cocoa.NSItalicFontMask

            # This method should always return something, falling back to the closest
            # similar font if it can't find one with the given name or traits.
            self.ctFont = manager.fontWithFamily_traits_weight_size_(name, traits, 0, size)
            
        self.ascent = CoreText.CTFontGetAscent(self.ctFont)
        self.descent = -CoreText.CTFontGetDescent(self.ctFont)

    @classmethod
    def have_font(cls, name):
        name = unicode(name)
        if name in cls._loaded_cgFont_table: return True
        # Try to create the font to see if it exists.
        return Quartz.CGFontCreateWithFontName(name) is not None

    @classmethod
    def add_font_data(cls, data):
        # Create a cgFont with the data.  There doesn't seem to be a way to 
        # register a font loaded from memory such that the operating system will 
        # find it later.  So instead we just store the cgFont in a table where
        # it can be found by our __init__ method.
        # Note that the iOS CTFontManager *is* able to register graphics fonts,
        # however this method is missing from CTFontManager on MacOS 10.6
        dataRef = CoreFoundation.CFDataCreate(None, data, len(data))
        provider = Quartz.CGDataProviderCreateWithCFData(dataRef)
        cgFont = Quartz.CGFontCreateWithDataProvider(provider)
        
        # Get the full name of the font and use it as the key to store
        # in our table of fonts loaded from memory.
        fullName = unicode(Quartz.CGFontCopyFullName(cgFont))
        cls._loaded_cgFont_table[fullName] = cgFont

        
