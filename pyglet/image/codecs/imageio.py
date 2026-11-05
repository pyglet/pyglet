from __future__ import annotations
from ctypes import Array, c_void_p, c_ubyte
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO

from pyglet.image import ImageData, Animation, AnimationFrame
from pyglet.image.codecs import ImageDecoder
from pyglet.libs.darwin.cocoapy import NSMakeRect, cf, cg
from pyglet.libs.darwin.cocoapy import cfnumber_to_number
from pyglet.libs.darwin.cocoapy import kCGImageAlphaPremultipliedLast
from pyglet.libs.darwin.cocoapy import kCGImagePropertyGIFDelayTime
from pyglet.libs.darwin.cocoapy import kCGImagePropertyGIFDictionary

if TYPE_CHECKING:
    from pyglet.image.codecs import ImageEncoder


class ImageIODecoder(ImageDecoder):
    """Decode images with Image I/O and render pixels through Core Graphics."""

    def get_file_extensions(self) -> list[str]:
        # Image I/O can decode many more formats, but these are the most common.
        return [ '.bmp', '.cur', '.gif', '.ico', '.jp2', '.jpg', '.jpeg',
                 '.pcx', '.png', '.tga', '.tif', '.tiff', '.xbm', '.xpm' ]

    def get_animation_file_extensions(self) -> list[str]:
        return ['.gif']

    def _get_pyglet_ImageData_from_source_at_index(self, sourceRef: c_void_p, index: int) -> ImageData:
        imageRef = c_void_p(cg.CGImageSourceCreateImageAtIndex(sourceRef, index, None))

        # Regardless of the internal format of the image (L, LA, RGB, RGBA, etc)
        # we just automatically convert everything to an RGBA format.
        format = 'RGBA'
        rgbColorSpace = c_void_p(cg.CGColorSpaceCreateDeviceRGB())
        bitsPerComponent = 8
        width: int = cg.CGImageGetWidth(imageRef)
        height: int = cg.CGImageGetHeight(imageRef)
        bytesPerRow = 4 * width

        # Create a buffer to store the RGBA formatted data.
        bufferSize = height * bytesPerRow
        buffer: Array[c_ubyte] = (c_ubyte * bufferSize)()

        # Create a bitmap context for the RGBA formatted data.
        # Note that premultiplied alpha is required:
        # http://developer.apple.com/library/mac/#qa/qa1037/_index.html
        bitmap = c_void_p(cg.CGBitmapContextCreate(buffer,
                                                       width, height,
                                                       bitsPerComponent,
                                                       bytesPerRow,
                                                       rgbColorSpace,
                                                       kCGImageAlphaPremultipliedLast))

        # Write the image data into the bitmap.
        cg.CGContextDrawImage(bitmap, NSMakeRect(0,0,width,height), imageRef)

        cg.CGImageRelease(imageRef)
        cg.CGContextRelease(bitmap)
        cg.CGColorSpaceRelease(rgbColorSpace)

        pitch = bytesPerRow
        return ImageData(width, height, format, buffer, -pitch)

    def decode(self, filename: str, file: BinaryIO | None) -> ImageData:
        file_bytes = Path(filename).read_bytes() if file is None else file.read()
        data = c_void_p(cf.CFDataCreate(None, file_bytes, len(file_bytes)))
        # Second argument is an options dictionary.  It might be a good idea to provide
        # a value for kCGImageSourceTypeIdentifierHint here using filename extension.
        sourceRef = c_void_p(cg.CGImageSourceCreateWithData(data, None))
        image = self._get_pyglet_ImageData_from_source_at_index(sourceRef, 0)

        cf.CFRelease(data)
        cf.CFRelease(sourceRef)

        return image

    def decode_animation(self, filename: str, file: BinaryIO | None) -> Animation:
        # If file is not an animated GIF, it will be loaded as a single-frame animation.
        file_bytes = Path(filename).read_bytes() if file is None else file.read()
        data = c_void_p(cf.CFDataCreate(None, file_bytes, len(file_bytes)))
        sourceRef = c_void_p(cg.CGImageSourceCreateWithData(data, None))

        # Get number of frames in the animation.
        count: int = cg.CGImageSourceGetCount(sourceRef)

        frames: list[AnimationFrame] = []

        for index in range(count):
            # Try to determine frame duration from GIF properties dictionary.
            duration: float | None = 0.1  # default duration if none found
            props = c_void_p(cg.CGImageSourceCopyPropertiesAtIndex(sourceRef, index, None))
            if cf.CFDictionaryContainsKey(props, kCGImagePropertyGIFDictionary):
                gif_props = c_void_p(cf.CFDictionaryGetValue(props, kCGImagePropertyGIFDictionary))
                if cf.CFDictionaryContainsKey(gif_props, kCGImagePropertyGIFDelayTime):
                    duration = cfnumber_to_number(c_void_p(cf.CFDictionaryGetValue(gif_props, kCGImagePropertyGIFDelayTime)))

            cf.CFRelease(props)
            image = self._get_pyglet_ImageData_from_source_at_index(sourceRef, index)
            frames.append( AnimationFrame(image, duration) )

        cf.CFRelease(data)
        cf.CFRelease(sourceRef)

        return Animation(frames)


def get_decoders() -> list[ImageIODecoder]:
    return [ImageIODecoder()]

def get_encoders() -> list[ImageEncoder]:
    return []
