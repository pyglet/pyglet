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
__version__ = '$Id$'

from ctypes import *

from pyglet.image import ImageData, Animation, AnimationFrame
from pyglet.image.codecs import *

import Quartz, CoreFoundation, LaunchServices 

# TODO:
# more complete list of openable formats?
# which formats actually make sense for pyglet to try to open?

class QuartzImageDecoder(ImageDecoder):
    def _get_all_file_extensions(self):
        """Query the OS to determine all possible image-related files it can open."""
        # A lot of these are RAW file types, which are probably unlikely 
        # candidates for files to be opened anyway.
        # First get a list of uniform type identifiers (they look like 'com.microsoft.bmp').
        types = Quartz.CGImageSourceCopyTypeIdentifiers()
        # Then convert these into a list of associated extensions.
        extensions = []
        for uti in types:
            desc = LaunchServices.UTTypeCopyDescription(uti)
            decl = LaunchServices.UTTypeCopyDeclaration(uti)
            try:
                spec = decl['UTTypeTagSpecification']
                ext = spec['public.filename-extension']
                if str(ext) == ext:
                    extensions.append('.'+ext)
                else:
                    extensions.extend( [ '.'+x for x in ext] )
            except:
                pass
        return extensions

    def get_file_extensions(self):
        # Quartz can actually decode many more formats, but these are the most common.
        return [ '.bmp', '.cur', '.gif', '.ico', '.jp2', '.jpg', '.jpeg', 
                 '.pcx', '.png', '.tga', '.tif', '.tiff', '.xbm', '.xpm' ]

    def get_animation_file_extensions(self):
        return ['.gif']
     
    def _get_format(self, imageRef):
        """Try to figure out the internal format of the image."""
        # This is adapted from the sample code here:
        # http://developer.apple.com/library/ios/#samplecode/GLImageProcessing/Listings/Texture_m
        
        bpp = Quartz.CGImageGetBitsPerPixel(imageRef)
        if bpp == 8: # GL_LUMINANCE
            return 'L'
        elif bpp == 16: # GL_LUMINANCE_ALPHA
            return 'LA'
        elif bpp == 24: # GL_RGB
            return 'RGB'
        elif bpp == 32: # GL_RGBA or GL_BGRA
            info = Quartz.CGImageGetBitmapInfo(imageRef)
            alphaInfo = info & Quartz.kCGBitmapAlphaInfoMask
            if alphaInfo in [Quartz.kCGImageAlphaPremultipliedFirst,
                             Quartz.kCGImageAlphaFirst,
                             Quartz.kCGImageAlphaNoneSkipFirst]:
                return 'BGRA'
            return 'RGBA'
        # If we get here, then we don't know what the format is.
        raise ImageDecodeException(filename or file)

    def _get_pyglet_ImageData_from_source_at_index(self, sourceRef, index):
        imageRef = Quartz.CGImageSourceCreateImageAtIndex(sourceRef, index, None)

        # Get info about the image.
        width = Quartz.CGImageGetWidth(imageRef)
        height = Quartz.CGImageGetHeight(imageRef)
        bytesPerRow = Quartz.CGImageGetBytesPerRow(imageRef)

        # Try to determine the internal format of the image.
        format = self._get_format(imageRef)

        # Copy the uncompressed image data to a buffer.
        imageData = Quartz.CGDataProviderCopyData(Quartz.CGImageGetDataProvider(imageRef))
        bufferSize = CoreFoundation.CFDataGetLength(imageData)
        buffer = (c_byte * bufferSize)()
        # Treat imageData as an NSData object.
        imageData.getBytes_length_(buffer, bufferSize)
        
        del imageRef, imageData
        
        pitch = bytesPerRow
        return ImageData(width, height, format, buffer, -pitch)

    def decode(self, file, filename):
        file_bytes = file.read()
        data = CoreFoundation.CFDataCreate(None, file_bytes, len(file_bytes))
        # Second argument is an options dictionary.  It might be a good idea to provide
        # a value for kCGImageSourceTypeIdentifierHint here using filename extension.
        sourceRef = Quartz.CGImageSourceCreateWithData(data, None)
        image = self._get_pyglet_ImageData_from_source_at_index(sourceRef, 0)
        del data, sourceRef
        return image

    def decode_animation(self, file, filename):
        # If file is not an animated GIF, it will be loaded as a single-frame animation.
        file_bytes = file.read()
        data = CoreFoundation.CFDataCreate(None, file_bytes, len(file_bytes))
        sourceRef = Quartz.CGImageSourceCreateWithData(data, None)

        # Get number of frames in the animation.
        count = Quartz.CGImageSourceGetCount(sourceRef)
        
        frames = []

        for index in range(count):
            # Try to determine frame duration from GIF properties dictionary.
            duration = 0.1  # default duration if none found
            props = Quartz.CGImageSourceCopyPropertiesAtIndex(sourceRef, index, None)
            if Quartz.kCGImagePropertyGIFDictionary in props:
                gif_props = props[Quartz.kCGImagePropertyGIFDictionary]
                if Quartz.kCGImagePropertyGIFDelayTime in gif_props:
                    duration = gif_props[Quartz.kCGImagePropertyGIFDelayTime]
            
            image = self._get_pyglet_ImageData_from_source_at_index(sourceRef, index)
            frames.append( AnimationFrame(image, duration) )

        del data, sourceRef

        return Animation(frames)
        

def get_decoders():
    return [ QuartzImageDecoder() ]

def get_encoders():
    return []
