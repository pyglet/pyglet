import sys
from ctypes import c_uint32, c_void_p, c_double, POINTER, c_bool

import pyglet.lib

from .lib_corefoundation import CFStringRef, CTRunRef, kCFBooleanTrue
from .cocoatypes import CGFloat, CGGlyph, UniChar, CFIndex, CFRange, CGPoint, CGRect, CGSize

######################################################################

# CORETEXT
ct = pyglet.lib.load_library(framework='CoreText')

# Types
CTFontOrientation = c_uint32      # CTFontDescriptor.h
CTFontSymbolicTraits = c_uint32   # CTFontTraits.h

# CoreText constants
kCTFontAttributeName = c_void_p.in_dll(ct, 'kCTFontAttributeName')
kCTFontFamilyNameAttribute = c_void_p.in_dll(ct, 'kCTFontFamilyNameAttribute')
kCTFontSymbolicTrait = c_void_p.in_dll(ct, 'kCTFontSymbolicTrait')
kCTFontWeightTrait = c_void_p.in_dll(ct, 'kCTFontWeightTrait')
kCTFontWidthTrait = c_void_p.in_dll(ct, 'kCTFontWidthTrait')
kCTFontSlantTrait = c_void_p.in_dll(ct, 'kCTFontSlantTrait')
kCTFontTraitsAttribute = c_void_p.in_dll(ct, 'kCTFontTraitsAttribute')
kCTForegroundColorAttributeName = c_void_p.in_dll(ct, 'kCTForegroundColorAttributeName')
kCTForegroundColorFromContextAttributeName = c_void_p.in_dll(ct, 'kCTForegroundColorFromContextAttributeName')

# constants from CTFontTraits.h
kCTFontItalicTrait = (1 << 0)
kCTFontBoldTrait   = (1 << 1)

ct.CTLineCreateWithAttributedString.restype = c_void_p
ct.CTLineCreateWithAttributedString.argtypes = [c_void_p]

ct.CTLineGetTypographicBounds.restype = c_double
ct.CTLineGetTypographicBounds.argtypes = [c_void_p, POINTER(CGFloat), POINTER(CGFloat), POINTER(CGFloat)]

ct.CTLineDraw.restype = None
ct.CTLineDraw.argtypes = [c_void_p, c_void_p]

ct.CTFontGetBoundingRectsForGlyphs.restype = CGRect
ct.CTFontGetBoundingRectsForGlyphs.argtypes = [c_void_p, CTFontOrientation, POINTER(CGGlyph), POINTER(CGRect), CFIndex]

ct.CTFontGetAdvancesForGlyphs.restype = c_double
ct.CTFontGetAdvancesForGlyphs.argtypes = [c_void_p, CTFontOrientation, POINTER(CGGlyph), POINTER(CGSize), CFIndex]

ct.CTFontCreatePathForGlyph.restype = c_void_p
ct.CTFontCreatePathForGlyph.argtypes = [c_void_p, CGGlyph, c_void_p]

ct.CTFontGetAscent.restype = CGFloat
ct.CTFontGetAscent.argtypes = [c_void_p]

ct.CTFontGetDescent.restype = CGFloat
ct.CTFontGetDescent.argtypes = [c_void_p]

ct.CTFontGetSymbolicTraits.restype = CTFontSymbolicTraits
ct.CTFontGetSymbolicTraits.argtypes = [c_void_p]

ct.CTFontGetGlyphsForCharacters.restype = c_bool
ct.CTFontGetGlyphsForCharacters.argtypes = [c_void_p, POINTER(UniChar), POINTER(CGGlyph), CFIndex]

ct.CTFontCreateWithGraphicsFont.restype = c_void_p
ct.CTFontCreateWithGraphicsFont.argtypes = [c_void_p, CGFloat, c_void_p, c_void_p]

ct.CTFontCopyGraphicsFont.restype = c_void_p
ct.CTFontCopyGraphicsFont.argtypes = [c_void_p, c_void_p]

ct.CTFontDrawGlyphs.restype = None
ct.CTFontDrawGlyphs.argtypes = [c_void_p, POINTER(CGGlyph), POINTER(CGPoint), CFIndex, c_void_p]

ct.CTFontCopyFamilyName.restype = c_void_p
ct.CTFontCopyFamilyName.argtypes = [c_void_p]

ct.CTFontCopyFullName.restype = c_void_p
ct.CTFontCopyFullName.argtypes = [c_void_p]

ct.CTFontCopyPostScriptName.restype = c_void_p
ct.CTFontCopyPostScriptName.argtypes = [c_void_p]

ct.CTFontCreateUIFontForLanguage.restype = c_void_p
ct.CTFontCreateUIFontForLanguage.argtypes = [c_uint32, c_double, c_void_p]

ct.CTFontCreateCopyWithSymbolicTraits.restype = c_void_p
ct.CTFontCreateCopyWithSymbolicTraits.argtypes = [c_void_p, CGFloat, c_void_p, c_uint32, c_uint32]

ct.CTFontCreateCopyWithAttributes.restype = c_void_p
ct.CTFontCreateCopyWithAttributes.argtypes = [c_void_p, c_double, c_void_p, c_void_p]

ct.CTFontCreateWithFontDescriptor.restype = c_void_p
ct.CTFontCreateWithFontDescriptor.argtypes = [c_void_p, CGFloat, c_void_p]

ct.CTFontDescriptorCreateWithAttributes.restype = c_void_p
ct.CTFontDescriptorCreateWithAttributes.argtypes = [c_void_p]

ct.CTFontDescriptorCopyAttribute.restype = c_void_p
ct.CTFontDescriptorCopyAttribute.argtypes = [c_void_p, CFStringRef]

ct.CTFontDescriptorCreateWithNameAndSize.restype = c_void_p
ct.CTFontDescriptorCreateWithNameAndSize.argtypes = [CFStringRef, CGFloat]

ct.CTFontDescriptorCreateMatchingFontDescriptor.restype = c_void_p
ct.CTFontDescriptorCreateMatchingFontDescriptor.argtypes = [c_void_p, c_void_p]

ct.CTFontCopyTraits.restype = c_void_p
ct.CTFontCopyTraits.argtypes = [c_void_p]

ct.CTLineGetGlyphRuns.restype = c_void_p  # CFArrayRef
ct.CTLineGetGlyphRuns.argtypes = [c_void_p]  # CTLineRef

ct.CTRunGetGlyphCount.restype = CFIndex
ct.CTRunGetGlyphCount.argtypes = [CTRunRef]

ct.CTRunGetGlyphs.restype = None
ct.CTRunGetGlyphs.argtypes = [CTRunRef, CFRange, POINTER(CGGlyph)]

ct.CTRunGetPositions.restype = None
ct.CTRunGetPositions.argtypes = [CTRunRef, CFRange, POINTER(CGPoint)]

ct.CTRunGetAttributes.restype = c_void_p
ct.CTRunGetAttributes.argtypes = [CTRunRef]

kCTFontURLAttribute = c_void_p.in_dll(ct, 'kCTFontURLAttribute')
