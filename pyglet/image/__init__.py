#!/usr/bin/env python

'''Image loading and high-level texture functions.

Only basic functionality is described here; for full reference see the
accompanying documentation.

To load an image::

    from pyglet.image import *
    image = load_image('picture.png')

The supported image file types include PNG, BMP, GIF, JPG, and many more,
somewhat depending on the operating system.  To load an image from a file-like
object instead of a filename::

    image = load_image('hint.jpg', file=fileobj)

The hint helps the module locate an appropriate decoder to use based on the
file extension.  It is optional.

Once loaded, images can be used directly by most other modules of pyglet (for
example, pyglet.scene2d).  All images have a width and height you can access::

    width, height = image.width, image.height

You can extract a region of an image (this keeps the original image intact;
the memory is shared efficiently)::

    subimage = image.get_region(x, y, width, height)

Remember that y-coordinates are always increasing upwards.

Drawing images
--------------

To draw an image at some point on the screen::

    image.blit(x, y, z)

This assumes an appropriate view transform and projection have been applied.

Texture access
--------------

If you are using OpenGL directly, you can access the image as a texture::

    texture = image.texture

(This is the most efficient way to obtain a texture; some images are
immediately loaded as textures, whereas others go through an intermediate
form).  To use a texture with pyglet.gl::

    from pyglet.gl import *
    glEnable(texture.target)        # typically target is GL_TEXTURE_2D
    glBindTexture(texture.target, texture.id)
    # ... draw with the texture

Pixel access
------------

To access raw pixel data of an image::

    rawimage = image.image_data

(If the image has just been loaded this will be a very quick operation;
however if the image is a texture a relatively expensive readback operation
will occur).  The pixels can be accessed as a string::

    pixels = rawimage.data

You determine the format of these pixels by examining rawimage.pitch,
rawimage.format.  The "pitch" of an image is the number of bytes in a row
(this may validly be more than the number required to make up the width of the
image, it is common to see this for word alignment).  If "pitch" is negative
the rows of the image are ordered from top to bottom, otherwise they are
ordedred from bottom to top.

"format" strings consist of characters that give the byte
order of each color component.  For example, if rawimage.format is 'RGBA',
there are four color components: red, green, blue and alpha, in that order.
Other common format strings are 'RGB', 'LA' (luminance, alpha) and 'I'
(intensity).

You can also set the format and pitch of an image.  This affects how "data"
will be presented the next time it is read or written to::

    # Read the alpha channel only, with rows tightly packed from bottom-to-top.
    rawimage.format = 'A'
    rawimage.pitch = rawimage.width
    data = rawimage.data

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import sys
import re
import warnings
import weakref

from ctypes import *
from math import ceil
from StringIO import StringIO

from pyglet.gl import *
from pyglet.gl.gl_info import *
from pyglet.window import *

class ImageException(Exception):
    pass

def load_image(filename, file=None, decoder=None):
    '''Load an image from a file.

    :note: You can make no assumptions about the return type; usually it will
        be ImageData or CompressedImageData, but decoders are free to return
        any subclass of AbstractImage.

    :Parameters:
        `filename` : str
            Used to guess the image format, and to load the file if `file` is
            unspecified.
        `file` : file-like object or None
            Source of image data in any supported format.        
        `decoder` : ImageDecoder or None
            If unspecified, all decoders that are registered for the filename
            extension are tried.  If none succeed, the exception from the
            first decoder is raised.

    :rtype: AbstractImage
    '''

    if not file:
        file = open(filename, 'rb')
    if not hasattr(file, 'seek'):
        file = StringIO(file.read())

    if decoder:
        return decoder.decode(file, filename)
    else:
        first_exception = None
        for decoder in get_decoders(filename):
            try:
                image = decoder.decode(file, filename)
                return image
            except ImageDecodeException, e:
                first_exception = first_exception or e
                file.seek(0)

        if not first_exception:
            raise ImageDecodeException('No image decoders are available')
        raise first_exception 

def create_image(width, height, pattern=None):
    '''Create an image optionally filled with the given pattern.

    :note: You can make no assumptions about the return type; usually it will
        be ImageData or CompressedImageData, but patterns are free to return
        any subclass of AbstractImage.

    :Parameters:
        `width` : int
            Width of image to create
        `height` : int
            Height of image to create
        `pattern` : ImagePattern or None
            Pattern to fill image with.  If unspecified, the image will
            intially be transparent.

    :rtype: AbstractImage
    '''
    if not pattern:
        pattern = SolidColorImagePattern()
    return pattern.create_image(width, height)

class ImagePattern(object):
    '''Abstract image creation class.'''
    def create_image(width, height):
        '''Create an image of the given size.

        :Parameters:
            `width` : int
                Width of image to create
            `height` : int
                Height of image to create
        
        :rtype: AbstractImage
        '''
        raise NotImplementedError('abstract')

class SolidColorImagePattern(ImagePattern):
    '''Creates an image filled with a solid color.'''

    def __init__(self, color=(0, 0, 0, 0)):
        '''Create a solid image pattern with the given color.

        :Parameters:
            `color` : (int, int, int, int)
                4-tuple of ints in range [0,255] giving RGBA components of
                color to fill with.

        '''
        self.color = '%c%c%c%c' % color

    def create_image(self, width, height):
        data = self.color * width * height
        return ImageData(width, height, 'RGBA', data)

class CheckerImagePattern(ImagePattern):
    '''Create an image with a tileable checker image.
    ''' 

    def __init__(self, color1=(150,150,150,255), color2=(200,200,200,255)):
        '''Initialise with the given colors.

        :Parameters:
            `color1` : (int, int, int, int)
                4-tuple of ints in range [0,255] giving RGBA components of
                color to fill with.  This color appears in the top-left and
                bottom-right corners of the image.
            `color2` : (int, int, int, int)
                4-tuple of ints in range [0,255] giving RGBA components of
                color to fill with.  This color appears in the top-right and
                bottom-left corners of the image.

        '''
        self.color1 = '%c%c%c%c' % color1
        self.color2 = '%c%c%c%c' % color2

    def create_image(self, width, height):
        hw = width/2
        hh = height/2
        row1 = self.color1 * hw + self.color2 * hw
        row2 = self.color2 * hw + self.color1 * hw
        data = row1 * hh + row2 * hh
        return ImageData(width, height, 'RGBA', data)

class AbstractImage(object):
    '''Abstract class representing an image.

    :Ivariables:
        `width` : int
            Width of image
        `height` : int
            Height of image
        `image_data` : ImageData
            An ImageData view of this image.  Changes to the returned instance
            may or may not be reflected in this image.  Read-only.
        `texture` : Texture
            A Texture view of this image.  Changes to the returned instance
            may or may not be reflected in this image.  Read-only.
        `mipmapped_texture` : Texture
            A Texture view of this image.  The returned Texture will have 
            mipmaps filled in for all levels.  Requires that image dimensions
            be powers of 2.  Read-only.

    '''

    def __init__(self, width, height):
        self.width = width
        self.height = height

    def get_image_data(self):
        '''Retrieve an ImageData instance for this image.'''
        raise ImageException('Cannot retrieve image data for %r' % self)

    image_data = property(get_image_data)

    def get_texture(self):
        '''Retrieve a Texture instance for this image.'''
        raise ImageException('Cannot retrieve texture for %r' % self)

    texture = property(get_texture)

    def get_mipmapped_texture(self):
        '''Retrieve a Texture instance with all mipmap levels filled in.'''
        raise ImageException('Cannot retrieve mipmapped texture for %r' % self)

    mipmapped_texture = property(get_mipmapped_texture)

    def save(self, filename=None, file=None, encoder=None):
        '''Save this image to a file.

        :Parameters:
            `filename` : str
                Used to set the image file format, and to open the output file
                if `file` is unspecified.
            `file` : file-like object or None
                File to write image data to.
            `encoder` : ImageEncoder or None
                If unspecified, all encoders matching the filename extension
                are tried.  If all fail, the exception from the first one
                attempted is raised.

        '''
        if not file:
            file = open(filename, 'wb')

        if encoder:
            encoder.encode(self, file, filename)
        else:
            first_exception = None
            for encoder in get_encoders(filename):
                try:
                    encoder.encode(self, file, filename)
                    return
                except ImageDecodeException, e:
                    first_exception = first_exception or e
                    file.seek(0)

            if not first_exception:
                raise ImageEncodeException('No image encoders are available')
            raise first_exception

    def blit(self, x, y, z):
        '''Draw this image to the active framebuffers.'''
        raise ImageException('Cannot blit %r.' % self)

    def blit_into(self, source, x, y, z):
        '''Draw `source` on this image.'''
        raise ImageException('Cannot blit images onto %r.' % self)

    def blit_to_texture(self, target, level, x, y, depth=0):
        '''Draw this image on the currently bound texture at `target`.'''
        raise ImageException('Cannot blit %r to a texture.' % self)

class ImageData(AbstractImage):
    '''An image represented as a string of unsigned bytes.

    :Ivariables:
        `data` : str
            Pixel data, encoded according to `format` and `pitch`.
        `format` : str
            The format string to use when reading or writing `data`.
        `pitch` : int
            Number of bytes per row.  Negative values indicate a top-to-bottom
            arrangement.

    '''

    _swap1_pattern = re.compile('(.)', re.DOTALL)
    _swap2_pattern = re.compile('(.)(.)', re.DOTALL)
    _swap3_pattern = re.compile('(.)(.)(.)', re.DOTALL)
    _swap4_pattern = re.compile('(.)(.)(.)(.)', re.DOTALL)

    _current_texture = None
    _current_mipmap_texture = None

    def __init__(self, width, height, format, data, pitch=None, skip_rows=0):
        '''Initialise image data.

        :Parameters:
            `width` : int
                Width of image data
            `height` : int
                Height of image data
            `format` : str
                A valid format string, such as 'RGB', 'RGBA', 'ARGB', etc.
            `data` : sequence
                String or array/list of bytes giving the decoded data.
            `pitch` : int or None
                If specified, the number of bytes per row.  Negative values
                indicate a top-to-bottom arrangement.  Defaults to 
                ``width * len(format)``.
            `skip_rows` : int
                Skip a number of rows in `data` before the image begins.

        '''
        super(ImageData, self).__init__(width, height)

        self._current_format = self._desired_format = format.upper()
        self._current_data = data
        if not pitch:
            pitch = width * len(format)
        self._current_pitch = self.pitch = pitch
        self.mipmap_images = []
        self._current_skip_rows = skip_rows


    image_data = property(lambda self: self)

    def set_format(self, format):
        self._desired_format = format.upper()
        self._current_texture = None

    format = property(lambda self: self._desired_format, set_format)

    def get_data(self):
        if self._current_pitch != self.pitch or \
           self._current_format != self.format:
            self._current_data = self._convert(self.format, self.pitch)
            self._current_format = self.format
            self._current_pitch = self.pitch

        self._ensure_string_data()
        return self._current_data

    def set_data(self, data):
        self._current_data = data
        self._current_format = self.format
        self._current_pitch = self.pitch
        self._current_skip_rows = 0
        self._current_texture = None
        self._current_mipmapped_texture = None

    data = property(get_data, set_data)

    def set_mipmap_image(self, level, image):
        '''Set a mipmap image for a particular level.

        The mipmap image will be applied to textures obtained via the
        `mipmapped_image` attribute. 

        :Parameters:
            `level` : int
                Mipmap level to set image at, must be >= 1.
            `image` : AbstractImage
                Image to set.  Must have correct dimensions for that mipmap
                level (i.e., width >> level, height >> level)
        '''

        if level == 0:
            raise ImageException(
                'Cannot set mipmap image at level 0 (it is this image)')

        if not _is_pow2(self.width) or not _is_pow2(self.height):
            raise ImageException(
                'Image dimensions must be powers of 2 to use mipmaps.')

        # Check dimensions of mipmap
        width, height = self.width, self.height
        for i in range(level):
            width >>= 1
            height >>= 1
        if width != image.width or height != image.height:
            raise ImageException(
                'Mipmap image has wrong dimensions for level %d' % level)

        # Extend mipmap_images list to required level
        self.mipmap_images += [None] * (level - len(self.mipmap_images))
        self.mipmap_images[level - 1] = data

    def create_texture(self, cls):
        '''Create a texture containing this image.

        If the image's dimensions are not powers of 2, a TextureRegion of
        a larger Texture will be returned that matches the dimensions of this
        image.

        :Parameters:
            `cls` : class (subclass of Texture)
                Class to construct.

        :rtype: cls or cls.region_class
        '''

        texture = cls.create_for_size(
            GL_TEXTURE_2D, self.width, self.height)
        subimage = False
        if texture.width != self.width or texture.height != self.height:
            texture = texture.get_region(0, 0, self.width, self.height)
            subimage = True

        internalformat = self._get_internalformat(self.format)

        glBindTexture(texture.target, texture.id)
        glTexParameteri(texture.target, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

        if subimage:
            width = texture.owner.width
            height = texture.owner.height
            blank = (c_ubyte * (width * height * 4))()
            glTexImage2D(texture.target, texture.level,
                         internalformat,
                         width, height,
                         0,
                         GL_RGBA, GL_UNSIGNED_BYTE,
                         blank) 
            internalformat = None

        self.blit_to_texture(texture.target, texture.level, 
            0, 0, 0, internalformat)
        
        return texture 

    def get_texture(self):
        if not self._current_texture:
            self._current_texture = self.create_texture(Texture)
        return self._current_texture

    texture = property(get_texture)

    def get_mipmapped_texture(self):
        '''Return a Texture with mipmaps.  
        
        If `set_mipmap_image` has been called with at least one image, the set
        of images defined will be used.  Otherwise, mipmaps will be
        automatically generated.

        The texture dimensions must be powers of 2 to use mipmaps.
        '''
        if self._current_mipmap_texture:
            return self._current_mipmap_texture

        if not _is_pow2(self.width) or not _is_pow2(self.height):
            raise ImageException(
                'Image dimensions must be powers of 2 to use mipmaps.')
        
        texture = Texture.create_for_size(
            GL_TEXTURE_2D, self.width, self.height)
        internalformat = self._get_internalformat(self.format)

        glBindTexture(texture.target, texture.id)
        glTexParameteri(texture.target, GL_TEXTURE_MIN_FILTER,
                        GL_LINEAR_MIPMAP_LINEAR)

        if self.mipmap_images:
            self.blit_to_texture(texture.target, texture.level, 
                0, 0, 0, internalformat)
            level = 0
            for image in self.mipmap_images:
                level += 1
                if image:
                    image.blit_to_texture(texture.target, level, 
                        0, 0, 0, internalformat)
            # TODO: should set base and max mipmap level if some mipmaps
            # are missing.
        elif gl_info.have_version(1, 4):
            glTexParameteri(texture.target, GL_GENERATE_MIPMAP, GL_TRUE)
            self.blit_to_texture(texture.target, texture.level, 
                0, 0, 0, internalformat)
        else:
            raise NotImplementedError('TODO: gluBuild2DMipmaps')

        self._current_mipmap_texture = texture
        return texture

    def blit(self, x, y, z):
        self.texture.blit(x, y, z)

    def blit_to_texture(self, target, level, x, y, depth, internalformat=None):
        '''Draw this image to to the currently bound texture at `target`.

        If `internalformat` is specified, glTexImage is used to initialise
        the texture; otherwise, glTexSubImage is used to update a region.
        '''

        data_format = self.format
        data_pitch = abs(self._current_pitch)

        # Determine pixel format from format string
        format, type = self._get_gl_format_and_type(data_format)
        if format is None:
            # Need to convert data to a standard form
            data_format = {
                1: 'L',
                2: 'LA',
                3: 'RGB',
                4: 'RGBA'}.get(len(data_format))
            format, type = self._get_gl_format_and_type(data_format)

        # Get data in required format (hopefully will be the same format it's
        # already in, unless that's an obscure format, upside-down or the
        # driver is old).
        data = self._convert(data_format, data_pitch)

        if data_pitch & 0x1:
            alignment = 1
        elif data_pitch & 0x2:
            alignment = 2
        else:
            alignment = 4
        row_length = data_pitch / len(data_format)
        glPushClientAttrib(GL_CLIENT_PIXEL_STORE_BIT)
        glPixelStorei(GL_UNPACK_ALIGNMENT, alignment)
        glPixelStorei(GL_UNPACK_ROW_LENGTH, row_length)
        glPixelStorei(GL_UNPACK_SKIP_ROWS, self._current_skip_rows)

        if internalformat:
            glTexImage2D(target, level,
                         internalformat,
                         self.width, self.height,
                         0,
                         format, type,
                         data)
        else:
            glTexSubImage2D(target, level,
                            x, y,
                            self.width, self.height,
                            format, type,
                            data)
        glPopClientAttrib()

    def crop(self, x, y, width, height):
        '''Crop this image in-place.

        This is not a particularly efficient implementation (it uses regular
        expressions on the string data).

        :Parameters:
            `x` : int
                Left edge of crop region
            `y` : int
                Bottom edge of crop region (count from bottom of image)
            `width` : int
                Width of crop region
            `height` : int
                Height of crop region

        '''

        self._ensure_string_data()

        x1 = len(self._current_format) * x
        x2 = len(self._current_format) * (x + width)

        data = self._convert(self._current_format, abs(self._current_pitch))
        rows = re.findall('.' * abs(self._current_pitch), data, re.DOTALL)
        rows = [row[x1:x2] for row in rows[y:y+height]]
        self._current_data = ''.join(rows)
        self._current_pitch = width * len(self._current_format)
        self._current_texture = None
        self.width = width
        self.height = height

    def _convert(self, format, pitch):
        '''Return data in the desired format; does not alter this instance's
        current format or pitch.
        '''

        if format == self._current_format and pitch == self._current_pitch:
            return self._current_data

        self._ensure_string_data()
        data = self._current_data

        if pitch != self._current_pitch:
            diff = abs(self._current_pitch) - abs(pitch)
            if diff > 0:
                # New pitch is shorter than old pitch, chop bytes off each row
                pattern = re.compile(
                    '(%s)%s' % ('.' * abs(pitch), '.' * diff), re.DOTALL)
                data = pattern.sub(r'\1', data)    
            elif diff < 0:
                # New pitch is longer than old pitch, add '0' bytes to each row
                pattern = re.compile(
                    '(%s)' % ('.' * abs(self._current_pitch)), re.DOTALL)
                pad = '.' * -diff
                data = pattern.sub(r'\1%s' % pad, data)

            if self._current_pitch * pitch < 0:
                # Pitch differs in sign, swap row order
                rows = re.findall('.' * abs(pitch), data, re.DOTALL)
                rows.reverse()
                data = ''.join(rows)

        if format != self._current_format:
            # Create replacement string, e.g. r'\4\1\2\3' to convert RGBA to
            # ARGB
            repl = ''
            for c in format:
                try:
                    idx = self._current_format.index(c) + 1
                except ValueError:
                    idx = 1
                repl += r'\%d' % idx

            if len(self._current_format) == 1:
                swap_pattern = self._swap1_pattern
            elif len(self._current_format) == 2:
                swap_pattern = self._swap2_pattern
            elif len(self._current_format) == 3:
                swap_pattern = self._swap3_pattern
            elif len(self._current_format) == 4:
                swap_pattern = self._swap4_pattern
            else:
                raise ImageException(
                    'Current image format is wider than 32 bits.')

            packed_pitch = self.width * len(self._current_format)
            if abs(pitch) != packed_pitch:
                # Pitch is wider than pixel data, need to go row-by-row.
                rows = re.findall('.' * abs(pitch), data, re.DOTALL)
                rows = [swap_pattern.sub(repl, r) for r in rows]
                data = ''.join(rows)
            else:
                # Rows are tightly packed, apply regex over whole image.
                data = swap_pattern.sub(repl, data)
        return data

    def _ensure_string_data(self):
        if type(self._current_data) is not str:
            buf = create_string_buffer(len(self._current_data))
            memmove(buf, self._current_data, len(self._current_data))
            self._current_data = buf.raw
            if self._current_skip_rows:
                self._current_data = \
                    self._current_data[self._current_pitch*skip_rows:]
                self._current_skip_rows = 0

    def _get_gl_format_and_type(self, format):
        if format == 'I':
            return GL_LUMINANCE, GL_UNSIGNED_BYTE
        elif format == 'L':
            return GL_LUMINANCE, GL_UNSIGNED_BYTE
        elif format == 'LA':
            return GL_LUMINANCE_ALPHA, GL_UNSIGNED_BYTE
        elif format == 'R':
            return GL_RED, GL_UNSIGNED_BYTE
        elif format == 'G':
            return GL_GREEN, GL_UNSIGNED_BYTE
        elif format == 'B':
            return GL_BLUE, GL_UNSIGNED_BYTE
        elif format == 'A':
            return GL_ALPHA, GL_UNSIGNED_BYTE
        elif format == 'RGB':
            return GL_RGB, GL_UNSIGNED_BYTE
        elif format == 'RGBA':
            return GL_RGBA, GL_UNSIGNED_BYTE
        elif format == 'ARGB':
            if (GL_UNSIGNED_BYTE == GL_UNSIGNED_BYTE and
                gl_info.have_extension('GL_EXT_bgra') and
                gl_info.have_extension('GL_APPLE_packed_pixel')):
                return GL_BGRA, GL_UNSIGNED_INT_8_8_8_8_REV
        elif format == 'ABGR':
            if gl_info.have_extension('GL_EXT_abgr'):
                return GL_ABGR_EXT, GL_UNSIGNED_BYTE
        elif format == 'BGR':
            if gl_info.have_extension('GL_EXT_bgra'):
                return GL_BGR, GL_UNSIGNED_BYTE

        return None, None

    def _get_internalformat(self, format):
        if len(format) == 4:
            return GL_RGBA
        elif len(format) == 3:
            return GL_RGB
        elif len(format) == 2:
            return GL_LUMINANCE_ALPHA
        elif format == 'A':
            return GL_ALPHA
        elif format == 'L':
            return GL_LUMINANCE
        elif format == 'I':
            return GL_INTENSITY
        return GL_RGBA

class CompressedImageData(AbstractImage):
    '''Image representing some compressed data suitable for direct uploading
    to driver.
    '''
    # TODO software decoding interface

    _have_extension = None
    _current_texture = None
    _current_mipmapped_texture = None

    def __init__(self, width, height, gl_format, data, extension=None):
        '''Construct a CompressedImageData with the given compressed data.

        :Parameters:
            `width` : int
                Width of image
            `height` : int
                Height of image
            `gl_format` : int
                GL constant giving format of compressed data; for example,
                ``GL_COMPRESSED_RGBA_S3TC_DXT5_EXT``.
            `data` : sequence
                String or array/list of bytes giving compressed image data.
            `extension` : str or None
                If specified, gives the name of a GL extension to check for
                before creating a texture.
                
        '''
        if not _is_pow2(width) or not _is_pow2(height):
            raise ImageException('Dimensions of %r must be powers of 2' % self)

        super(CompressedImageData, self).__init__(width, height)
        self.data = data
        self.gl_format = gl_format
        self.extension = extension
        self.mipmap_data = []

    def set_mipmap_data(self, level, data):
        '''Set data for a mipmap level.

        Supplied data gives a compressed image for the given mipmap level.
        The image must be of the correct dimensions for the level 
        (i.e., width >> level, height >> level); but this is not checked.  If
        any mipmap levels are specified, they are used; otherwise, mipmaps for
        `mipmapped_texture` are generated automatically.

        :Parameters:
            `level` : int
                Level of mipmap image to set.
            `data` : sequence
                String or array/list of bytes giving compressed image data.
                Data must be in same format as specified in constructor.

        '''
        # Extend mipmap_data list to required level
        self.mipmap_data += [None] * (level - len(self.mipmap_data))
        self.mipmap_data[level - 1] = data

    def verify_driver_supported(self):
        '''Assert that the extension required for this image data is
        supported.

        Raises `ImageException` if not.
        '''

        if self._have_extension is None and self.extension:
            self._have_extension = gl_info.have_extension(self.extension)
        if not self._have_extension:
            raise ImageException('%s is required to decode %r' % \
                (self.extension, self))

    def get_texture(self):
        if self._current_texture:
            return self._current_texture

        self.verify_driver_supported()

        texture = Texture.create_for_size(
            GL_TEXTURE_2D, self.width, self.height)
        glBindTexture(texture.target, texture.id)
        glTexParameteri(texture.target, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

        glCompressedTexImage2DARB(texture.target, texture.level,
            self.gl_format,
            self.width, self.height, 0,
            len(self.data), self.data)
            
        self._current_texture = texture
        return texture

    texture = property(get_texture)

    def get_mipmapped_texture(self):
        if self._current_mipmap_texture:
            return self._current_mipmap_texture

        self.verify_driver_supported()

        texture = Texture.create_for_size(
            GL_TEXTURE_2D, self.width, self.height)
        glBindTexture(texture.target, texture.id)

        glTexParameteri(texture.target, GL_TEXTURE_MIN_FILTER,
                        GL_LINEAR_MIPMAP_LINEAR)

        if not self.mipmap_data:
            if not gl_info.have_version(1, 4):
                raise ImageException(
                  'Require GL 1.4 to generate mipmaps for compressed textures')
            glTexParameteri(texture.target, GL_GENERATE_MIPMAP, GL_TRUE)

        glCompressedTexImage2DARB(texture.target, texture.level,
            self.gl_format,
            self.width, self.height, 0,
            len(self.data), self.data) 

        width, height = self.width, self.height
        level = 0
        for data in self.mipmap_data:
            width >>= 1
            height >>= 1
            level += 1
            glCompressedTexImage2DARB(texture.target, level,
                self.gl_format,
                width, height, 0,
                len(data), data)

        self._current_mipmap_texture = texture
        return texture

    def blit_to_texture(self, target, level, x, y, z):
        self.verify_driver_supported()

        glCompressedTexSubImage2DARB(target, level, 
            x, y,
            self.width, self.height,
            self.gl_format,
            len(self.data), self.data)
        
def _nearest_pow2(v):
    # From http://graphics.stanford.edu/~seander/bithacks.html#RoundUpPowerOf2
    # Credit: Sean Anderson
    v -= 1
    v |= v >> 1
    v |= v >> 2
    v |= v >> 4
    v |= v >> 8
    v |= v >> 16
    return v + 1

def _is_pow2(v):
    # http://graphics.stanford.edu/~seander/bithacks.html#DetermineIfPowerOf2
    return (v & (v - 1)) == 0

class Texture(AbstractImage):
    '''An image loaded into video memory that can be efficiently drawn
    to the framebuffer.

    Typically you will get an instance of Texture by accessing the `texture`
    member of any other AbstractImage.

    :Ivariables:
        `region_class` : class (subclass of TextureRegion)
            Class to use when constructing regions of this texture.
        `tex_coords` : tuple
            4-tuple of 3-tuple of float, giving four 3D texture coordinates
            of the bottom-left, bottom-right, top-right and top-left corners
            of the texture.
        `level` : int
            The mipmap level of this texture.

    '''

    region_class = None # Set to TextureRegion after it's defined
    tex_coords = ((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0))
    level = 0

    def __init__(self, width, height, target, id):
        super(Texture, self).__init__(width, height)
        self.target = target
        self.id = id

    def __del__(self):
        # TODO
        #id = GLuint(self.id)
        #glDeleteTextures(1, byref(id))
        pass

    @classmethod
    def create_for_size(cls, target, min_width, min_height,
                        internalformat=None):
        '''Create a Texture with dimensions at least min_width, min_height.

        :Parameters:
            `target` : int
                GL constant giving texture target to use, typically
                ``GL_TEXTURE_2D``.
            `min_width` : int
                Minimum width of texture (may be increased to createa  power
                of 2).
            `min_height` : int
                Minimum height of texture (may be increased to create a power
                of 2).
            `internalformat` : int
                GL constant giving internal format of texture; for example,
                ``GL_RGBA``.  If unspecified, the texture will not be
                initialised (only the texture name will be created on the
                instance).   If specified, the image will be initialised
                to this format with zero'd data.
        '''
        if target not in (GL_TEXTURE_RECTANGLE_NV, GL_TEXTURE_RECTANGLE_ARB):
            width = _nearest_pow2(min_width)
            height = _nearest_pow2(min_height)
        id = GLuint()
        glGenTextures(1, byref(id))

        if internalformat is not None:
            blank = (GLubyte * (width * height * 4))()
            glBindTexture(target, id.value)
            glTexParameteri(target, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexImage2D(target, 0,
                         internalformat,
                         width, height,
                         0,
                         GL_RGBA, GL_UNSIGNED_BYTE,
                         blank)
                         
        return cls(width, height, target, id.value)

    def get_image_data(self):
        glBindTexture(self.target, self.id)

        # Always extract complete RGBA data.  Could check internalformat
        # to only extract used channels. XXX
        format = 'RGBA'
        gl_format = GL_RGBA

        glPushClientAttrib(GL_CLIENT_PIXEL_STORE_BIT)
        glPixelStorei(GL_PACK_ALIGNMENT, 1)
        buffer = (GLubyte * (self.width * self.height * len(format)))()
        glGetTexImage(self.target, self.level, 
                      gl_format, GL_UNSIGNED_BYTE, buffer)
        glPopClientAttrib()

        return ImageData(self.width, self.height, format, buffer)

    image_data = property(get_image_data)

    texture = property(lambda self: self)

    # no implementation of blit_to_texture yet (could use aux buffer)

    def blit(self, x, y, z):
        # Create interleaved array in T4F_V4F format
        t = self.tex_coords
        w, h = self.width, self.height
        array = (GLfloat * 32)(
             t[0][0], t[0][1], t[0][2], 1.,
             x,       y,       z,       1.,
             t[1][0], t[1][1], t[1][2], 1., 
             x + w,   y,       z,       1.,
             t[2][0], t[2][1], t[2][2], 1., 
             x + w,   y + h,   z,       1.,
             t[3][0], t[3][1], t[3][2], 1., 
             x,       y + h,   z,       1.)

        glPushAttrib(GL_ENABLE_BIT)
        glEnable(self.target)
        glBindTexture(self.target, self.id)
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glInterleavedArrays(GL_T4F_V4F, 0, array)
        glDrawArrays(GL_QUADS, 0, 4)
        glPopClientAttrib()
        glPopAttrib()

    def blit_into(self, source, x, y, z):
        glBindTexture(self.target, self.id)
        source.blit_to_texture(self.target, self.level, x, y, z)

    def get_region(self, x, y, width, height):
        u1 = x / float(self.width)
        v1 = y / float(self.height)
        u2 = (x + width) / float(self.width)
        v2 = (y + height) / float(self.height)
        z1 = self.tex_coords[0][2]
        z2 = self.tex_coords[1][2]
        z3 = self.tex_coords[2][2]
        z4 = self.tex_coords[3][2]
        return self.region_class(width, height, self,
            ((u1, v1, z1), (u2, v1, z2), (u2, v2, z3), (u1, v2, z4)))

class TextureRegion(Texture):
    '''A rectangular region of a texture, presented as if it were
    a separate texture.
    '''

    def __init__(self, width, height, owner, tex_coords):
        super(TextureRegion, self).__init__(
            width, height, owner.target, owner.id)
        
        self.owner = owner
        self.tex_coords = tex_coords

    def get_image_data(self):
        me_x = int(self.tex_coords[0][0] * self.owner.width)
        me_y = int(self.tex_coords[0][1] * self.owner.height)
        image_data = self.owner.get_image_data()
        image_data.crop(me_x, me_y, self.width, self.height)
        return image_data

    image_data = property(get_image_data)

    def get_region(self, x, y, width, height):
        me_x = self.tex_coords[0][0] * self.owner.width
        me_y = self.tex_coords[0][1] * self.owner.height
        u1 = x / float(self.owner.width)
        v1 = y / float(self.owner.height)
        u2 = (x + width) / float(self.owner.width)
        v2 = (y + height) / float(self.owner.height)
        z1 = self.tex_coords[0][2]
        z2 = self.tex_coords[1][2]
        z3 = self.tex_coords[2][2]
        z4 = self.tex_coords[3][2]
        return self.region_class(width, height, self.owner,
            ((u1, v1, z1), (u2, v1, z2), (u2, v2, z3), (u1, v2, z4))) 

    def blit_into(self, source, x, y, z):
        me_x = int(self.tex_coords[0][0] * self.owner.width)
        me_y = int(self.tex_coords[0][1] * self.owner.height)
        self.owner.blit_into(source, x + me_x, y + me_y, z)

Texture.region_class = TextureRegion

class TileableTexture(Texture):
    '''A texture that can be tiled efficiently.

    Use `create_from_image` classmethod to construct.
    '''
    def __init__(self, width, height, target, id):
        if not _is_pow2(width) or not _is_pow2(height):
            raise ImageException(
                'TileableTexture requires dimensions that are powers of 2')
        super(TileableTexture, self).__init__(width, height, target, id)
        
    def get_region(self, x, y, width, height):
        raise ImageException('Cannot get region of %r' % self)

    def blit_tiled(self, x, y, z, width, height):
        '''Blit this texture tiled over the given area.'''
        u1 = v1 = 0
        u2 = width / float(self.width)
        v2 = height / float(self.height)
        w, h = width, height
        t = self.tex_coords
        array = (GLfloat * 32)(
             u1,      v1,      t[0][2], 1.,
             x,       y,       z,       1.,
             u2,      v1,      t[1][2], 1., 
             x + w,   y,       z,       1.,
             u2,      v2,      t[2][2], 1., 
             x + w,   y + h,   z,       1.,
             u1,      v2,      t[3][2], 1., 
             x,       y + h,   z,       1.)

        glPushAttrib(GL_ENABLE_BIT)
        glEnable(self.target)
        glBindTexture(self.target, self.id)
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glInterleavedArrays(GL_T4F_V4F, 0, array)
        glDrawArrays(GL_QUADS, 0, 4)
        glPopClientAttrib()
        glPopAttrib()
        

    @classmethod
    def create_from_image(cls, image):
        if not _is_pow2(image.width) or not _is_pow2(image.height):
            # Potentially unnecessary conversion if a GL format exists.
            image = image.image_data
            image.format = 'RGBA'
            image.pitch = image.width * len(image.format)
            texture_width = _nearest_pow2(image.width)
            texture_height = _nearest_pow2(image.height)
            newdata = c_buffer(texture_width * texture_height *
                               len(image.format))
            gluScaleImage(GL_RGBA,
                          image.width, image.height,
                          GL_UNSIGNED_BYTE,
                          image.data,
                          texture_width,
                          texture_height,
                          GL_UNSIGNED_BYTE,
                          newdata)
            image = ImageData(texture_width, texture_height, image.format,
                              newdata)

        image = image.image_data
        return image.create_texture(cls)

class DepthTexture(Texture):
    '''A texture with depth samples (typically 24-bit).'''
    def blit_into(self, source, x, y, z):
        glBindTexture(self.target, self.id)
        source.blit_to_texture(self.level, x, y, z)

class BufferManager(object):
    '''Manages the set of framebuffers for a context.  This class must
    be singleton per context.
    '''
    def __init__(self):
        self.color_buffer = None
        self.depth_buffer = None

        aux_buffers = GLint()
        glGetIntegerv(GL_AUX_BUFFERS, byref(aux_buffers))
        self.free_aux_buffers = [GL_AUX0, 
                                 GL_AUX1, 
                                 GL_AUX2,
                                 GL_AUX3][:aux_buffers.value]

        stencil_bits = GLint()
        glGetIntegerv(GL_STENCIL_BITS, byref(stencil_bits))
        self.free_stencil_bits = range(stencil_bits.value)

        self.refs = []

    def get_viewport(self):
        viewport = (GLint * 4)()
        glGetIntegerv(GL_VIEWPORT, viewport)
        return viewport
    
    def get_color_buffer(self):
        if not self.color_buffer:
            viewport = self.get_viewport()
            self.color_buffer = ColorBufferImage(*viewport)
        return self.color_buffer

    def get_aux_buffer(self):
        if not self.free_aux_buffers:
            raise ImageException('No free aux buffer is available.')

        gl_buffer = self.free_aux_buffers.pop(0)
        viewport = self.get_viewport()
        buffer = ColorBufferImage(*viewport)
        buffer.gl_buffer = gl_buffer

        def release_buffer(ref, self=self):
            self.free_aux_buffers.insert(0, gl_buffer)
        self.refs.append(weakref.ref(buffer, release_buffer))
            
        return buffer

    def get_depth_buffer(self):
        if not self.depth_buffer:
            viewport = self.get_viewport()
            self.depth_buffer = DepthBufferImage(*viewport)
        return self.depth_buffer

    def get_buffer_mask(self):
        if not self.free_stencil_bits:
            raise ImageException('No free stencil bits are available.')

        stencil_bit = self.free_stencil_bits.pop(0)
        viewport = self.get_viewport()
        buffer = BufferImageMask(x, y, width, height)
        buffer.stencil_bit = stencil_bit

        def release_buffer(ref, self=self):
            self.free_stencil_bits.insert(0, stencil_bit)
        self.refs.append(weakref.ref(buffer, release_buffer))

        return buffer

def get_buffer_manager():
    context = get_current_context()
    if not hasattr(context, 'image_buffer_manager'):
        context.image_buffer_manager = BufferManager()
    return context.image_buffer_manager

# XXX BufferImage could be generalised to support EXT_framebuffer_object's
# renderbuffer.
class BufferImage(AbstractImage):
    gl_buffer = GL_BACK
    gl_format = 0
    format = ''
    owner = None

    # TODO: enable methods

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def get_image_data(self):
        buffer = (GLubyte * (len(self.format) * self.width * self.height))()

        x = self.x
        y = self.y
        if self.owner:
            x += self.owner.x
            y += self.owner.y

        glReadBuffer(self.gl_buffer)
        glPushClientAttrib(GL_CLIENT_PIXEL_STORE_BIT)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glReadPixels(x, y, self.width, self.height, 
                     self.gl_format, GL_UNSIGNED_BYTE, buffer)
        glPopClientAttrib()

        return ImageData(self.width, self.height, self.format, buffer)

    image_data = property(get_image_data)

    def get_region(self, x, y, width, height):
        if self.owner:
            return self.owner.get_region(x + self.x, y + self.y, width, height)

        region = self.__class__(x + self.x, y + self.y, width, height)
        region.owner = self
        return region

class ColorBufferImage(BufferImage):
    gl_format = GL_RGBA
    format = 'RGBA'

    def get_texture(self):
        texture = Texture.create_for_size(GL_TEXTURE_2D, 
            self.width, self.height)
        glBindTexture(texture.target, texture.id)

        if texture.width != self.width or texture.height != self.height:
            texture = texture.get_region(0, 0, self.width, self.height)
            width = texture.owner.width
            height = texture.owner.height
            blank = (c_ubyte * (width * height * 4))()
            glTexImage2D(texture.target, texture.level,
                         GL_RGBA,
                         width, height,
                         0,
                         GL_RGBA, GL_UNSIGNED_BYTE,
                         blank)
            self.blit_to_texture(texture.target, texture.level, 0, 0, 0)
        else:
            glReadBuffer(self.gl_buffer)
            glCopyTexImage2D(texture.target, 0,
                             GL_RGBA,
                             self.x, self.y, self.width, self.height,
                             0)

    texture = property(get_texture)

    def blit_to_texture(self, target, level, x, y, z):
        glReadBuffer(self.gl_buffer)
        glCopyTexSubImage2D(target, level, 
                            x, y,
                            self.x, self.y, self.width, self.height) 

class DepthBufferImage(BufferImage):
    gl_format = GL_DEPTH_COMPONENT
    format = 'L'

    def get_texture(self):
        if not _is_pow2(self.width) or not _is_pow2(self.height):
            raise ImageException(
                'Depth texture requires that buffer dimensions be powers of 2')
        
        texture = DepthTexture.create_for_size(GL_TEXTURE_2D,
            self.width, self.height)
        glBindTexture(texture.target, texture.id)
        glReadBuffer(self.gl_buffer)
        glCopyTexImage2D(texture.target, 0,
                         GL_DEPTH_COMPONENT,
                         self.x, self.y, self.width, self.height,
                         0)
        return texture

    texture = property(get_texture)

    def blit_to_texture(self, target, level, x, y, z):
        glReadBuffer(self.gl_buffer)
        glCopyTexSubImage2D(target, level,
                            x, y,
                            self.x, self.y, self.width, self.height)


class BufferImageMask(BufferImage):
    gl_format = GL_STENCIL_INDEX
    format = 'L'

    # TODO mask methods

class TextureSequence(object):
    def __init__(self, texture):
        self.texture = texture

    def __getitem__(self, slice):
        raise ImageException('Cannot getitem from %r' % self)

    def __setitem__(self, slice, image):
        raise ImageException('Cannot setitem on %r' % self)


# Initialise default codecs
from pyglet.image.codecs import *
add_default_image_codecs()
