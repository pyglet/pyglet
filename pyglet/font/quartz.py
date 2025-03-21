# Tiger and later: need to set kWindowApplicationScaledAttribute for DPI independence?
from __future__ import annotations

import math
import warnings
from ctypes import byref, c_int32, c_void_p, string_at, cast, c_char_p, c_float
from typing import BinaryIO

import pyglet.image
from pyglet.font import base
from pyglet.font.base import Glyph, GlyphPosition
from pyglet.libs.darwin import CGFloat, cocoapy, kCTFontURLAttribute, cfnumber_to_number, \
    kCTFontWeightTrait
from pyglet.font.harfbuzz import harfbuzz_available, get_resource_from_ct_font, \
    get_harfbuzz_shaped_glyphs


cf = cocoapy.cf
ct = cocoapy.ct
quartz = cocoapy.quartz

UIFontWeightUltraLight = -0.8
UIFontWeightThin = -0.6
UIFontWeightLight = -0.4
UIFontWeightRegular = 0.0
UIFontWeightMedium = 0.23
UIFontWeightSemibold = 0.3
UIFontWeightBold = 0.4
UIFontWeightHeavy = 0.56
UIFontWeightBlack = 0.62

name_to_weight = {
    True: UIFontWeightBold,     # Bold as default for True
    False: UIFontWeightRegular,    # Regular for False
    None: UIFontWeightRegular,     # Regular if no weight provided
    "thin": UIFontWeightThin,
    "extralight": UIFontWeightUltraLight,
    "ultralight": UIFontWeightUltraLight,
    "light": UIFontWeightLight,
    "semilight": UIFontWeightLight,
    "normal": UIFontWeightRegular,
    "regular": UIFontWeightRegular,
    "medium": UIFontWeightMedium,
    "demibold": UIFontWeightSemibold,
    "semibold": UIFontWeightSemibold,
    "bold": UIFontWeightBold,
    "extrabold": UIFontWeightBold,
    "ultrabold": UIFontWeightBold,
    "black": UIFontWeightBlack,
    "heavy": UIFontWeightHeavy,
    "extrablack": UIFontWeightBlack,
}

name_to_stretch = {
    None: 1.0,
    False: 1.0,
    "undefined": 1.0,
    "ultracondensed": -0.4,
    "extracondensed": -0.3,
    "condensed": -0.2,
    "semicondensed": -0.1,
    "normal": 0.0,
    "medium": 0.0,
    "semiexpanded": 0.1,
    "expanded": 0.2,
    "extraexpanded": 0.3,
    "ultraexpanded": 0.4,
}


if harfbuzz_available():
    """Build the callbacks and information needed for Harfbuzz to work with CoreText Fonts.
    
    Getting the font data is not always reliable, and since no other way exists to
    retrieve the full font bytes from memory, we must construct callbacks for harfbuzz
    to retrieve the tag tables.
    """
    from pyglet.font.harfbuzz.harfbuzz_lib import hb_lib, hb_destroy_func_t, hb_reference_table_func_t, HB_MEMORY_MODE_READONLY

    def py_coretext_table_data_destroy(user_data: c_void_p):
        """Release the table resources once harfbuzz is done."""
        if user_data:
            cf.CFRelease(user_data)

    py_coretext_table_data_destroy_c = hb_destroy_func_t(py_coretext_table_data_destroy)

    @hb_reference_table_func_t
    def py_coretext_table_callback(face: c_void_p, tag: int, user_data: c_void_p):
        """This callback is invoked by HarfBuzz for each table it needs.

        user_data is a pointer to the CGFont.
        """
        # Use Quartz to get the table data for the given tag.
        table_data = quartz.CGFontCopyTableForTag(user_data, tag)
        if table_data is None:
            return None

        # Get the length and pointer to the raw data.
        length = cf.CFDataGetLength(table_data)
        data_ptr = cf.CFDataGetBytePtr(table_data)
        if not data_ptr:
            # Release the table_data and return empty blob.
            cf.CFRelease(table_data)
            return None

        # Create a blob that references this table data.
        data_ptr_char = cast(data_ptr, c_char_p)
        blob = hb_lib.hb_blob_create(data_ptr_char, length, HB_MEMORY_MODE_READONLY,
                                     table_data, py_coretext_table_data_destroy_c)
        return blob

    # Null callback, so harfbuzz cannot destroy our CGFont.
    _destroy_callback_null = cast(None, hb_destroy_func_t)

class QuartzGlyphRenderer(base.GlyphRenderer):
    font: QuartzFont

    def __init__(self, font: QuartzFont) -> None:
        super().__init__(font)
        self.font = font

    def render_index(self, glyph_index: int):
        ctFont = self.font.ctFont

        # Create an attributed string using text and font.
        # Determine the glyphs involved for the text (if any)
        # Get a bounding rectangle for glyphs in string.
        count = 1
        glyphs = (cocoapy.CGGlyph * count)(glyph_index)

        rect = ct.CTFontGetBoundingRectsForGlyphs(ctFont, 0, glyphs, None, count)

        # Get advance for all glyphs in string.
        advance = ct.CTFontGetAdvancesForGlyphs(ctFont, 0, glyphs, None, count)

        # Set image parameters:
        # We add 2 pixels to the bitmap width and height so that there will be a 1-pixel border
        # around the glyph image when it is placed in the texture atlas.  This prevents
        # weird artifacts from showing up around the edges of the rendered glyph textures.
        # We adjust the baseline and lsb of the glyph by 1 pixel accordingly.
        width = max(int(math.ceil(rect.size.width) + 2), 1)
        height = max(int(math.ceil(rect.size.height) + 2), 1)
        baseline = -int(math.floor(rect.origin.y)) + 1
        lsb = int(math.ceil(rect.origin.x)) - 1
        advance = int(round(advance))

        # Create bitmap context.
        bits_per_components = 8
        bytes_per_row = 4 * width
        colorSpace = c_void_p(quartz.CGColorSpaceCreateDeviceRGB())
        bitmap_context = c_void_p(quartz.CGBitmapContextCreate(
            None,
            width,
            height,
            bits_per_components,
            bytes_per_row,
            colorSpace,
            cocoapy.kCGImageAlphaPremultipliedLast))

        # Draw text to bitmap context.
        quartz.CGContextSetShouldAntialias(bitmap_context, pyglet.options.text_antialiasing)
        quartz.CGContextSetTextPosition(bitmap_context, -lsb, baseline)
        quartz.CGContextSetRGBFillColor(bitmap_context, 1, 1, 1, 1)
        quartz.CGContextSetFont(bitmap_context, ctFont)
        quartz.CGContextSetFontSize(bitmap_context, self.font.pixel_size)
        quartz.CGContextTranslateCTM(bitmap_context, 0, height)  # Move origin to top-left
        quartz.CGContextScaleCTM(bitmap_context, 1, -1)  # Flip vertically

        positions = (cocoapy.CGPoint * 1)(*[cocoapy.CGPoint(0, 0)])
        quartz.CTFontDrawGlyphs(ctFont, glyphs, positions, 1, bitmap_context)

        # Create an image to get the data out.
        image_ref = c_void_p(quartz.CGBitmapContextCreateImage(bitmap_context))

        bytes_per_row = quartz.CGImageGetBytesPerRow(image_ref)
        data_provider = c_void_p(quartz.CGImageGetDataProvider(image_ref))
        image_data = c_void_p(quartz.CGDataProviderCopyData(data_provider))
        buffer_size = cf.CFDataGetLength(image_data)
        buffer_ptr = cf.CFDataGetBytePtr(image_data)
        if buffer_ptr:
            buffer = string_at(buffer_ptr, buffer_size)

            quartz.CGImageRelease(image_ref)
            quartz.CGDataProviderRelease(image_data)
            cf.CFRelease(bitmap_context)
            cf.CFRelease(colorSpace)

            glyph_image = pyglet.image.ImageData(width, height, "RGBA", buffer, bytes_per_row)

            glyph = self.font.create_glyph(glyph_image)
            glyph.set_bearings(baseline, lsb, advance)

            return glyph

        raise Exception("CG Image buffer could not be read.")

    def render(self, text: str) -> base.Glyph:
        # Using CTLineDraw seems to be the only way to make sure that the text
        # is drawn with the specified font when that font is a graphics font loaded from
        # memory.  For whatever reason, [NSAttributedString drawAtPoint:] ignores
        # the graphics font if it not registered with the font manager.
        # So we just use CTLineDraw for both graphics fonts and installed fonts.

        ctFont = self.font.ctFont

        # Create an attributed string using text and font.
        attributes = c_void_p(
            cf.CFDictionaryCreateMutable(None, 2, cf.kCFTypeDictionaryKeyCallBacks, cf.kCFTypeDictionaryValueCallBacks)
        )
        cf.CFDictionaryAddValue(attributes, cocoapy.kCTFontAttributeName, ctFont)
        cf.CFDictionaryAddValue(attributes, cocoapy.kCTForegroundColorFromContextAttributeName , cocoapy.kCFBooleanTrue)
        cf_str = cocoapy.CFSTR(text)
        string = c_void_p(cf.CFAttributedStringCreate(None, cf_str, attributes))

        # Create a CTLine object to render the string.
        line = c_void_p(ct.CTLineCreateWithAttributedString(string))
        cf.CFRelease(string)
        cf.CFRelease(attributes)
        cf.CFRelease(cf_str)

        # Determine the glyphs involved for the text (if any)
        count = len(text)
        chars = (cocoapy.UniChar * count)(*list(map(ord, str(text))))
        glyphs = (cocoapy.CGGlyph * count)()
        ct.CTFontGetGlyphsForCharacters(ctFont, chars, glyphs, count)

        # If a glyph is returned as 0, it does not exist in the current font.
        if glyphs[0] == 0:
            # Use the typographic bounds instead for the placements.
            # This seems to have some sort of fallback information in the bounds.
            ascent, descent = CGFloat(), CGFloat()
            advance = width = int(ct.CTLineGetTypographicBounds(line, byref(ascent), byref(descent), None))
            height = int(ascent.value + descent.value)
            lsb = 0
            baseline = descent.value
        else:
            # Get a bounding rectangle for glyphs in string.
            rect = ct.CTFontGetBoundingRectsForGlyphs(ctFont, 0, glyphs, None, count)

            # Get advance for all glyphs in string.
            advance = ct.CTFontGetAdvancesForGlyphs(ctFont, 0, glyphs, None, count)

            # Set image parameters:
            # We add 2 pixels to the bitmap width and height so that there will be a 1-pixel border
            # around the glyph image when it is placed in the texture atlas.  This prevents
            # weird artifacts from showing up around the edges of the rendered glyph textures.
            # We adjust the baseline and lsb of the glyph by 1 pixel accordingly.

            width = max(int(math.ceil(rect.size.width) + 2), 1)
            height = max(int(math.ceil(rect.size.height) + 2), 1)
            baseline = -int(math.floor(rect.origin.y)) + 1
            lsb = int(math.ceil(rect.origin.x)) - 1
            advance = int(round(advance))

        # Create bitmap context.
        bits_per_components = 8
        bytes_per_row = 4 * width
        colorSpace = c_void_p(quartz.CGColorSpaceCreateDeviceRGB())
        bitmap_context = c_void_p(quartz.CGBitmapContextCreate(
            None,
            width,
            height,
            bits_per_components,
            bytes_per_row,
            colorSpace,
            cocoapy.kCGImageAlphaPremultipliedLast))

        # Draw text to bitmap context.
        quartz.CGContextSetShouldAntialias(bitmap_context, pyglet.options.text_antialiasing)
        quartz.CGContextSetTextPosition(bitmap_context, -lsb, baseline)
        quartz.CGContextSetRGBFillColor(bitmap_context, 1, 1, 1, 1)  # Render white for multiplying.
        quartz.CGContextTranslateCTM(bitmap_context, 0, height)  # Move origin to top-left
        quartz.CGContextScaleCTM(bitmap_context, 1, -1)  # Flip vertically

        ct.CTLineDraw(line, bitmap_context)
        cf.CFRelease(line)
        # Create an image to get the data out.
        image_ref = c_void_p(quartz.CGBitmapContextCreateImage(bitmap_context))

        bytes_per_row = quartz.CGImageGetBytesPerRow(image_ref)
        data_provider = c_void_p(quartz.CGImageGetDataProvider(image_ref))
        image_data = c_void_p(quartz.CGDataProviderCopyData(data_provider))
        buffer_size = cf.CFDataGetLength(image_data)
        buffer_ptr = cf.CFDataGetBytePtr(image_data)
        if buffer_ptr:
            buffer = string_at(buffer_ptr, buffer_size)

            quartz.CGImageRelease(image_ref)
            quartz.CGDataProviderRelease(image_data)
            cf.CFRelease(bitmap_context)
            cf.CFRelease(colorSpace)

            glyph_image = pyglet.image.ImageData(width, height, "RGBA", buffer, bytes_per_row)

            glyph = self.font.create_glyph(glyph_image)
            glyph.set_bearings(baseline, lsb, advance)

            return glyph

        raise Exception("CG Image buffer could not be read.")


class QuartzFont(base.Font):
    glyph_renderer_class: type[base.GlyphRenderer] = QuartzGlyphRenderer
    _loaded_CGFont_table: dict[str, dict[int, tuple[c_void_p, bytes]]] = {}

    def __init__(self, name: str, size: float, weight: str = "normal", italic: bool = False, stretch: bool = False,
                 dpi: int | None = None) -> None:

        super().__init__()

        name = name or "Helvetica"

        self.dpi = dpi or 96
        self.size = size
        self.pixel_size = size * dpi / 72.0
        self.italic = italic
        self.stretch = stretch
        self.weight = weight

        if isinstance(weight, str):
            self.weight_value = name_to_weight[weight]
        elif weight is True:
            self.weight_value = name_to_weight["bold"]
        else:
            self.weight_value = None

        self.italic = italic

        # Construct traits value.
        traits = 0
        if italic:
            traits |= cocoapy.kCTFontItalicTrait

        if isinstance(stretch, str):
            self.stretch_value = name_to_stretch[stretch]
        else:
            self.stretch_value = None

        name = str(name)
        self.traits = traits
        # First see if we can find an appropriate font from our table of loaded fonts.
        result = self._lookup_font_with_family_and_traits(name, traits)
        if result:
            cgFont = result[0]
            # Use cgFont from table to create a CTFont object with the specified size.
            self.ctFont = c_void_p(ct.CTFontCreateWithGraphicsFont(cgFont, self.pixel_size, None, None))
        else:
            # Create a font descriptor for given name and traits and use it to create font.
            descriptor = self._create_font_descriptor(name, traits, self.weight_value, self.stretch_value)
            self.ctFont = c_void_p(ct.CTFontCreateWithFontDescriptor(descriptor, self.pixel_size, None))
            cf.CFRelease(descriptor)
            assert self.ctFont, "Couldn't load font: " + name

        string = c_void_p(ct.CTFontCopyFamilyName(self.ctFont))
        self._family_name = str(cocoapy.cfstring_to_string(string))
        cf.CFRelease(string)

        self.ascent = int(math.ceil(ct.CTFontGetAscent(self.ctFont)))
        self.descent = -int(math.ceil(ct.CTFontGetDescent(self.ctFont)))

        if pyglet.options.text_shaping == 'harfbuzz' and harfbuzz_available():
            self._cg_font = None
            self.hb_resource = get_resource_from_ct_font(self)


    def _get_hb_face(self):
        assert self._cg_font is None

        # Create a CGFont from the CTFont for the face.
        self._cg_font = quartz.CTFontCopyGraphicsFont(self.ctFont, None)
        if self._cg_font is None:
            raise ValueError("Could not get CGFont from CTFont")

        # Create the HarfBuzz face using our table callback.
        return hb_lib.hb_face_create_for_tables(py_coretext_table_callback, self._cg_font, _destroy_callback_null)

    def get_font_data(self) -> bytes:
        """Get the font file in bytes if possible.

        Unfortunately CoreText doesn't have a good way to retrieve directly from a font object. Attempt to get the
        filename from the system. If the filename is unknown, it most likely was loaded from memory. In which case,
        the data was added and cached at some point with `add_font_data`.
        """
        filename = self.filename
        if filename == "Unknown":
            result = self._lookup_font_with_family_and_traits(self.name, self.traits)
            if result:
                _, data = result
            else:
                raise Exception("Couldn't load font data by name and traits. Report as a bug with the font file.")
        else:
            with open(filename, "rb") as f:
                data = f.read()

        return data

    @property
    def filename(self) -> str:
        descriptor = self._create_font_descriptor(self.name, self.traits, self.weight_value, self.stretch_value)
        ref = c_void_p(ct.CTFontDescriptorCopyAttribute(descriptor, kCTFontURLAttribute))
        if ref:
            url = cocoapy.ObjCInstance(ref)  # NSURL
            filepath = url.fileSystemRepresentation().decode()
            cf.CFRelease(ref)
            cf.CFRelease(descriptor)
            return filepath

        cf.CFRelease(descriptor)
        return "Unknown"

    @property
    def name(self) -> str:
        return self._family_name

    def __del__(self) -> None:
        cf.CFRelease(self.ctFont)

    def _lookup_font_with_family_and_traits(self, family: str, traits: int) -> tuple[c_void_p, bytes] | None:
        # This method searches the _loaded_CGFont_table to find a loaded
        # font of the given family with the desired traits.  If it can't find
        # anything with the exact traits, it tries to fall back to whatever
        # we have loaded that's close.  If it can't find anything in the
        # given family at all, it returns None.

        # Check if we've loaded the font with the specified family.
        if family not in self._loaded_CGFont_table:
            return None
        # Grab a dictionary of all fonts in the family, keyed by traits.
        fonts = self._loaded_CGFont_table[family]
        if not fonts:
            return None
        # Return font with desired traits if it is available.
        if traits in fonts:
            return fonts[traits]
        # Otherwise try to find a font with some of the traits.
        for (t, f) in fonts.items():
            if traits & t:
                return f
        # Otherwise try to return a regular font.
        if 0 in fonts:
            return fonts[0]
        # Otherwise return whatever we have.
        return list(fonts.values())[0]

    def _create_font_descriptor(self, family_name: str, traits: int,
                                weight: float | None = None,
                                stretch: float | None = None) -> c_void_p:
        # Create an attribute dictionary.
        attributes = c_void_p(
            cf.CFDictionaryCreateMutable(None, 0, cf.kCFTypeDictionaryKeyCallBacks, cf.kCFTypeDictionaryValueCallBacks))
        # Add family name to attributes.
        cfname = cocoapy.CFSTR(family_name)
        cf.CFDictionaryAddValue(attributes, cocoapy.kCTFontFamilyNameAttribute, cfname)
        cf.CFRelease(cfname)

        # Construct a CFNumber to represent the traits.
        itraits = c_int32(traits)
        symTraits = c_void_p(cf.CFNumberCreate(None, cocoapy.kCFNumberSInt32Type, byref(itraits)))
        if symTraits:
            # Construct a dictionary to hold the traits values.
            traitsDict = c_void_p(cf.CFDictionaryCreateMutable(None, 0, cf.kCFTypeDictionaryKeyCallBacks,
                                                               cf.kCFTypeDictionaryValueCallBacks))
            if traitsDict:
                if weight is not None:
                    weight_value = c_float(weight)
                    cfWeight = c_void_p(cf.CFNumberCreate(None, cocoapy.kCFNumberFloatType, byref(weight_value)))
                    if cfWeight:
                        cf.CFDictionaryAddValue(traitsDict, cocoapy.kCTFontWeightTrait, cfWeight)
                        cf.CFRelease(cfWeight)

                if stretch is not None:
                    stretch_value = c_float(stretch)
                    cfWidth = c_void_p(cf.CFNumberCreate(None, cocoapy.kCFNumberFloatType, byref(stretch_value)))
                    if cfWidth:
                        cf.CFDictionaryAddValue(traitsDict, cocoapy.kCTFontWidthTrait, cfWidth)
                        cf.CFRelease(cfWidth)

                # Add CFNumber traits to traits dictionary.
                cf.CFDictionaryAddValue(traitsDict, cocoapy.kCTFontSymbolicTrait, symTraits)
                # Add traits dictionary to attributes.
                cf.CFDictionaryAddValue(attributes, cocoapy.kCTFontTraitsAttribute, traitsDict)
                cf.CFRelease(traitsDict)

            cf.CFRelease(symTraits)
        # Create font descriptor with attributes.
        descriptor = c_void_p(ct.CTFontDescriptorCreateWithAttributes(attributes))
        cf.CFRelease(attributes)
        return descriptor

    @classmethod
    def have_font(cls: type[QuartzFont], name: str) -> bool:
        name = str(name)
        if name in cls._loaded_CGFont_table:
            return True

        # Query CoreText to see if the font exists.
        descriptor = ct.CTFontDescriptorCreateWithNameAndSize(cocoapy.CFSTR(name), 0.0)
        matched = ct.CTFontDescriptorCreateMatchingFontDescriptor(descriptor, None)

        exists = True if matched else False

        if descriptor:
            cf.CFRelease(descriptor)

        if matched:
            cf.CFRelease(matched)

        return exists

    @classmethod
    def add_font_data(cls: type[QuartzFont], data: BinaryIO) -> None:
        # Create a cgFont with the data.  There doesn't seem to be a way to
        # register a font loaded from memory such that the operating system will
        # find it later.  So instead we just store the cgFont in a table where
        # it can be found by our __init__ method.
        # Note that the iOS CTFontManager *is* able to register graphics fonts,
        # however this method is missing from CTFontManager on MacOS 10.6
        dataRef = c_void_p(cf.CFDataCreate(None, data, len(data)))
        provider = c_void_p(quartz.CGDataProviderCreateWithCFData(dataRef))
        cgFont = c_void_p(quartz.CGFontCreateWithDataProvider(provider))

        cf.CFRelease(dataRef)
        quartz.CGDataProviderRelease(provider)

        # Create a template CTFont from the graphics font so that we can get font info.
        ctFont = c_void_p(ct.CTFontCreateWithGraphicsFont(cgFont, 1, None, None))

        # Get info about the font to use as key in our font table.
        string = c_void_p(ct.CTFontCopyFamilyName(ctFont))
        familyName = str(cocoapy.cfstring_to_string(string))
        cf.CFRelease(string)

        string = c_void_p(ct.CTFontCopyFullName(ctFont))
        fullName = str(cocoapy.cfstring_to_string(string))
        cf.CFRelease(string)

        traits = ct.CTFontGetSymbolicTraits(ctFont)
        cf.CFRelease(ctFont)

        # Store font in table. We store it under both its family name and its
        # full name, since its not always clear which one will be looked up.
        if familyName not in cls._loaded_CGFont_table:
            cls._loaded_CGFont_table[familyName] = {}
        cls._loaded_CGFont_table[familyName][traits] = (cgFont, data)

        if fullName not in cls._loaded_CGFont_table:
            cls._loaded_CGFont_table[fullName] = {}
        cls._loaded_CGFont_table[fullName][traits] = (cgFont, data)

    def get_text_size(self, text: str) -> tuple[int, int]:
        ctFont = self.ctFont

        attributes = c_void_p(
            cf.CFDictionaryCreateMutable(None, 1, cf.kCFTypeDictionaryKeyCallBacks, cf.kCFTypeDictionaryValueCallBacks)
        )
        cf.CFDictionaryAddValue(attributes, cocoapy.kCTFontAttributeName, ctFont)
        cf_str = cocoapy.CFSTR(text)
        string = c_void_p(cf.CFAttributedStringCreate(None, cf_str, attributes))

        line = c_void_p(ct.CTLineCreateWithAttributedString(string))

        ascent, descent = CGFloat(), CGFloat()
        width = ct.CTLineGetTypographicBounds(line, byref(ascent), byref(descent), None)
        height = ascent.value + descent.value

        cf.CFRelease(string)
        cf.CFRelease(attributes)
        cf.CFRelease(line)
        cf.CFRelease(cf_str)
        return round(width), round(height)

    def _get_font_weight(self):
        traits = ct.CTFontCopyTraits(self.ctFont)
        font_weight = cfnumber_to_number(c_void_p(cf.CFDictionaryGetValue(traits, kCTFontWeightTrait)))
        cf.CFRelease(traits)
        return font_weight

    def _get_font_stretch(self):
        traits = ct.CTFontCopyTraits(self.ctFont)
        font_width = cfnumber_to_number(c_void_p(cf.CFDictionaryGetValue(traits, cocoapy.kCTFontWidthTrait)))
        cf.CFRelease(traits)
        return font_width

    def render_glyph_indices(self, indices: list[int]) -> None:
        # Process any glyphs that have not been rendered.
        self._initialize_renderer()

        missing = set()
        for glyph_indice in set(indices):
            if glyph_indice not in self.glyphs:
                missing.add(glyph_indice)

        # Missing glyphs, get their info.
        for glyph_indice in missing:
            self.glyphs[glyph_indice] = self._glyph_renderer.render_index(glyph_indice)

    def get_glyphs(self, text: str) -> tuple[list[Glyph], list[GlyphPosition]]:
        """Create and return a list of Glyphs for `text`.

        If any characters do not have a known glyph representation in this
        font, a substitution will be made.

        Args:
            text:
                Text to render.
        """
        self._initialize_renderer()

        if pyglet.options.text_shaping == "harfbuzz" and harfbuzz_available():
            return get_harfbuzz_shaped_glyphs(self, text)

        glyphs = []  # glyphs that are committed.
        offsets = []
        for c in base.get_grapheme_clusters(str(text)):
            if c == "\t":
                c = " "  # noqa: PLW2901
            if c not in self.glyphs:
                self.glyphs[c] = self._glyph_renderer.render(c)
            glyphs.append(self.glyphs[c])
            offsets.append(base.GlyphPosition(0, 0, 0, 0))

        return glyphs, offsets