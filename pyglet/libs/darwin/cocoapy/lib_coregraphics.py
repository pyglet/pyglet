"""CoreGraphics and ImageIO bindings."""
from ctypes import POINTER, c_bool, c_int, c_int32, c_size_t, c_uint32, c_void_p

import pyglet.lib

from .cocoatypes import CGFloat, CGGlyph, CGPoint, CGRect

cg = pyglet.lib.load_library(framework='CoreGraphics')

CGDirectDisplayID = c_uint32     # CGDirectDisplay.h
CGError = c_int32                # CGError.h
CGBitmapInfo = c_uint32          # CGImage.h
CGContextRef = c_void_p
CGFontRef = c_void_p
CTFontRef = c_void_p

# /System/Library/Frameworks/ApplicationServices.framework/Frameworks/...
#     ImageIO.framework/Headers/CGImageProperties.h
imageio = pyglet.lib.load_library(framework='ImageIO')
kCGImagePropertyGIFDictionary = c_void_p.in_dll(imageio, 'kCGImagePropertyGIFDictionary')
kCGImagePropertyGIFDelayTime = c_void_p.in_dll(imageio, 'kCGImagePropertyGIFDelayTime')

# /System/Library/Frameworks/ApplicationServices.framework/Frameworks/...
#     CoreGraphics.framework/Headers/CGColorSpace.h
kCGRenderingIntentDefault = 0

kCGTextFill = 0
kCGTextStroke = 1
kCGTextFillStroke = 2
kCGTextInvisible = 3
kCGTextFillClip = 4
kCGTextStrokeClip = 5
kCGTextFillStrokeClip = 6
kCGTextClip = 7

# CGImage.h
kCGImageAlphaNone = 0
kCGImageAlphaPremultipliedLast = 1
kCGImageAlphaPremultipliedFirst = 2
kCGImageAlphaLast = 3
kCGImageAlphaFirst = 4
kCGImageAlphaNoneSkipLast = 5
kCGImageAlphaNoneSkipFirst = 6
kCGImageAlphaOnly = 7
kCGBitmapAlphaInfoMask = 0x1F
kCGBitmapFloatComponents = 1 << 8
kCGBitmapByteOrderMask = 0x7000
kCGBitmapByteOrderDefault = 0 << 12
kCGBitmapByteOrder16Little = 1 << 12
kCGBitmapByteOrder32Little = 2 << 12
kCGBitmapByteOrder16Big = 3 << 12
kCGBitmapByteOrder32Big = 4 << 12

imageio.CGImageSourceCreateWithData.restype = c_void_p
imageio.CGImageSourceCreateWithData.argtypes = [c_void_p, c_void_p]
imageio.CGImageSourceCreateImageAtIndex.restype = c_void_p
imageio.CGImageSourceCreateImageAtIndex.argtypes = [c_void_p, c_size_t, c_void_p]
imageio.CGImageSourceCopyPropertiesAtIndex.restype = c_void_p
imageio.CGImageSourceCopyPropertiesAtIndex.argtypes = [c_void_p, c_size_t, c_void_p]
imageio.CGImageSourceGetCount.restype = c_size_t
imageio.CGImageSourceGetCount.argtypes = [c_void_p]

# ImageIO owns these symbols; expose them through the CoreGraphics binding for
# the existing image codec API.
cg.CGImageSourceCreateWithData = imageio.CGImageSourceCreateWithData
cg.CGImageSourceCreateImageAtIndex = imageio.CGImageSourceCreateImageAtIndex
cg.CGImageSourceCopyPropertiesAtIndex = imageio.CGImageSourceCopyPropertiesAtIndex
cg.CGImageSourceGetCount = imageio.CGImageSourceGetCount

cg.CGImageGetDataProvider.restype = c_void_p
cg.CGImageGetDataProvider.argtypes = [c_void_p]

cg.CGDataProviderCopyData.restype = c_void_p
cg.CGDataProviderCopyData.argtypes = [c_void_p]

cg.CGDataProviderCreateWithCFData.restype = c_void_p
cg.CGDataProviderCreateWithCFData.argtypes = [c_void_p]

cg.CGImageCreate.restype = c_void_p
cg.CGImageCreate.argtypes = [c_size_t, c_size_t, c_size_t, c_size_t, c_size_t, c_void_p, c_uint32, c_void_p, c_void_p, c_bool, c_int]

cg.CGImageRelease.restype = None
cg.CGImageRelease.argtypes = [c_void_p]

cg.CGImageGetBytesPerRow.restype = c_size_t
cg.CGImageGetBytesPerRow.argtypes = [c_void_p]

cg.CGImageGetWidth.restype = c_size_t
cg.CGImageGetWidth.argtypes = [c_void_p]

cg.CGImageGetHeight.restype = c_size_t
cg.CGImageGetHeight.argtypes = [c_void_p]

cg.CGImageGetBitsPerPixel.restype = c_size_t
cg.CGImageGetBitsPerPixel.argtypes = [c_void_p]

cg.CGImageGetBitmapInfo.restype = CGBitmapInfo
cg.CGImageGetBitmapInfo.argtypes = [c_void_p]

cg.CGColorSpaceCreateDeviceRGB.restype = c_void_p
cg.CGColorSpaceCreateDeviceRGB.argtypes = []

cg.CGDataProviderRelease.restype = None
cg.CGDataProviderRelease.argtypes = [c_void_p]

cg.CGColorSpaceRelease.restype = None
cg.CGColorSpaceRelease.argtypes = [c_void_p]

cg.CGContextFillRect.restype = None
cg.CGContextFillRect.argtypes = [c_void_p, CGRect]

cg.CGBitmapContextCreate.restype = c_void_p
cg.CGBitmapContextCreate.argtypes = [c_void_p, c_size_t, c_size_t, c_size_t, c_size_t, c_void_p, CGBitmapInfo]

cg.CGBitmapContextCreateImage.restype = c_void_p
cg.CGBitmapContextCreateImage.argtypes = [c_void_p]

cg.CGFontCreateWithDataProvider.restype = c_void_p
cg.CGFontCreateWithDataProvider.argtypes = [c_void_p]

cg.CGFontCreateWithFontName.restype = c_void_p
cg.CGFontCreateWithFontName.argtypes = [c_void_p]

cg.CGContextSetFont.restype = None
cg.CGContextSetFont.argtypes = [CGContextRef, CGFontRef]

cg.CGContextSetFontSize.restype = None
cg.CGContextSetFontSize.argtypes = [CGContextRef, CGFloat]

cg.CGContextShowGlyphsAtPositions.restype = None
cg.CGContextShowGlyphsAtPositions.argtypes = [CGContextRef, POINTER(CGGlyph), POINTER(CGPoint), c_size_t]

cg.CGContextTranslateCTM.restype = None
cg.CGContextTranslateCTM.argtypes = [CGContextRef, CGFloat, CGFloat]

cg.CGContextScaleCTM.restype = None
cg.CGContextScaleCTM.argtypes = [CGContextRef, CGFloat, CGFloat]

cg.CGContextDrawImage.restype = None
cg.CGContextDrawImage.argtypes = [c_void_p, CGRect, c_void_p]

cg.CGContextRelease.restype = None
cg.CGContextRelease.argtypes = [c_void_p]

cg.CGContextSetTextPosition.restype = None
cg.CGContextSetTextPosition.argtypes = [c_void_p, CGFloat, CGFloat]

cg.CGContextSetShouldAntialias.restype = None
cg.CGContextSetShouldAntialias.argtypes = [c_void_p, c_bool]

cg.CGContextSetTextDrawingMode.restype = None
cg.CGContextSetTextDrawingMode.argtypes = [c_void_p, c_int32]

cg.CGContextSetLineWidth.restype = None
cg.CGContextSetLineWidth.argtypes = [c_void_p, CGFloat]

cg.CGContextSetLineJoin.restype = None
cg.CGContextSetLineJoin.argtypes = [c_void_p, c_int32]

cg.CGContextSetMiterLimit.restype = None
cg.CGContextSetMiterLimit.argtypes = [c_void_p, CGFloat]

cg.CGContextAddPath.restype = None
cg.CGContextAddPath.argtypes = [c_void_p, c_void_p]

cg.CGContextStrokePath.restype = None
cg.CGContextStrokePath.argtypes = [c_void_p]

cg.CGPathRelease.restype = None
cg.CGPathRelease.argtypes = [c_void_p]

cg.CGContextSetRGBFillColor.restype = None
cg.CGContextSetRGBFillColor.argtypes = [c_void_p, CGFloat, CGFloat, CGFloat, CGFloat]

cg.CGContextSetRGBStrokeColor.restype = None
cg.CGContextSetRGBStrokeColor.argtypes = [c_void_p, CGFloat, CGFloat, CGFloat, CGFloat]

cg.CGFontCopyTableTags.restype = c_void_p
cg.CGFontCopyTableTags.argtypes = [c_void_p]

cg.CGFontCopyTableForTag.restype = c_void_p
cg.CGFontCopyTableForTag.argtypes = [c_void_p, c_uint32]
