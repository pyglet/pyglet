'''
TODO:

1. At the moment if there's an error during reading (say the image file is
   corrupt) then libpng will abort, printing a message. You can simulate
   this by disabling the rewind() call.

   Handling this will require use of the png_set_error_fn() API call, and
   additionally setjmp to set the break-out location (the function passed
   to png_set_error_fn to handle the error can't return).

   Handling this will require support from ctypes.
'''



import sys

from ctypes import *

path = util.find_library('c')
libc = cdll.LoadLibrary(path)
libc.fdopen.argtypes = [c_int, c_char_p]
libc.fdopen.restype = c_void_p
libc.rewind.argtypes = [c_void_p]

path = util.find_library('png')
libpng = cdll.LoadLibrary(path)

PNG_LIBPNG_VER_STRING = "1.2.8"

class png_struct(Structure):
    _fields_ = [
        # XXX clearly this isn't correct :)
        ('dummy', c_int),
    ]
png_structp = POINTER(png_struct)

class png_info(Structure):
    _fields_ = [
        # XXX clearly this isn't correct :)
        ('dummy', c_int),
    ]
png_infop = POINTER(png_info)

libpng.png_sig_cmp.argtypes = [c_char_p, c_size_t, c_size_t]
libpng.png_create_read_struct.argtypes = [c_char_p, c_void_p, c_void_p, c_void_p]
libpng.png_create_read_struct.restype = png_structp
libpng.png_create_info_struct.argtypes = [png_structp]
libpng.png_create_info_struct.restype = png_infop
libpng.png_init_io.argtypes = [png_structp, c_void_p]
libpng.png_read_png.argtypes = [png_structp, png_infop, c_int, c_void_p]
row_pointers = POINTER(c_char_p)
libpng.png_get_rows.argtypes = [png_structp, png_infop]
libpng.png_get_rows.restype = POINTER(c_char_p)
libpng.png_get_bit_depth.argtypes = [png_structp, png_infop]
libpng.png_get_color_type.argtypes = [png_structp, png_infop]
libpng.png_get_image_width.argtypes = [png_structp, png_infop]
libpng.png_get_image_height.argtypes = [png_structp, png_infop]
libpng.png_get_valid.argtypes = [png_structp, png_infop, c_uint]
libpng.png_set_expand.argtypes = [png_structp]
libpng.png_set_strip_16.argtypes = [png_structp]
libpng.png_set_gray_to_rgb.argtypes = [png_structp]
libpng.png_destroy_read_struct.argtypes = (POINTER(png_structp), POINTER(png_infop), POINTER(png_infop))
PNG_COLOR_MASK_PALETTE = 1
PNG_COLOR_MASK_COLOR = 2
PNG_COLOR_MASK_ALPHA = 4
PNG_COLOR_TYPE_GRAY = 0
PNG_COLOR_TYPE_PALETTE = (PNG_COLOR_MASK_COLOR | PNG_COLOR_MASK_PALETTE)
PNG_COLOR_TYPE_RGB = (PNG_COLOR_MASK_COLOR)
PNG_COLOR_TYPE_RGB_ALPHA = (PNG_COLOR_MASK_COLOR | PNG_COLOR_MASK_ALPHA)
PNG_COLOR_TYPE_GRAY_ALPHA = (PNG_COLOR_MASK_ALPHA)
PNG_INFO_tRNS = 0x0010

def ptr_add(ptr, offset):
    address = addressof(ptr.contents) + offset
    return pointer(type(ptr.contents).from_address(address))

def is_png(filename):
    ''' Determine whether "filename" is a PNG file '''
    image = open(filename)
    header = image.read(16)
    image.close()
    return libpng.png_sig_cmp(header, 0, 16)

def read(filename):
    ''' Read the PNG from "filename" and return a pyglet.image.Image
    instance with the image data and meta-data.'''
    image = open(filename)

    header = image.read(16)
    if libpng.png_sig_cmp(header, 0, 16):
        raise ValueError, '%r is not a PNG'%(filename,)

    # init our PNG structures
    png_ptr = libpng.png_create_read_struct(PNG_LIBPNG_VER_STRING,
        None, None, None)
    if not png_ptr: raise RuntimeError, 'out of memory'
    info_ptr = libpng.png_create_info_struct(png_ptr)
    if not info_ptr:
        libpng.png_destroy_read_struct(byref(png_ptr), NULL, NULL)
        raise RuntimeError, 'out of memory'

    # ready reading from the file
    fp = libc.fdopen(image.fileno(), 'rb')
    libc.rewind(fp)
    libpng.png_init_io(png_ptr, fp)

    # read the PNG and pull out important info from the info_struct
    libpng.png_read_png(png_ptr, info_ptr, 0, None)
    bit_depth = libpng.png_get_bit_depth(png_ptr, info_ptr)
    color_type = libpng.png_get_color_type(png_ptr, info_ptr)
    width = libpng.png_get_image_width(png_ptr, info_ptr)
    height = libpng.png_get_image_height(png_ptr, info_ptr)

    # determine how to map to RGB or RGBA
    if (color_type == PNG_COLOR_TYPE_PALETTE or
            (color_type == PNG_COLOR_TYPE_GRAY and bit_depth < 8) or
            libpng.png_get_valid(png_ptr, info_ptr, PNG_INFO_tRNS)):
        libpng.png_set_expand(png_ptr)
    if bit_depth == 16:
        libpng.png_set_strip_16(png_ptr)
    if color_type in (PNG_COLOR_TYPE_GRAY, PNG_COLOR_TYPE_GRAY_ALPHA):
        libpng.png_set_gray_to_rgb(png_ptr)

    if color_type in (PNG_COLOR_TYPE_GRAY_ALPHA, PNG_COLOR_TYPE_RGB_ALPHA):
        bpp = 4
    else:
        bpp = 3

    # Copy image data from row pointers (there is no guarantee that data
    # is already sequential).
    image_data = create_string_buffer(width * height * bpp)
    image_data_ptr = cast(image_data, POINTER(c_char))
    row_pointers = libpng.png_get_rows(png_ptr, info_ptr)
    for y in xrange(height):
        row = ptr_add(image_data_ptr, width * bpp * y)
        memmove(row, row_pointers[height-y-1], width * bpp)

    # free up everything
    libpng.png_destroy_read_struct(byref(png_ptr), byref(info_ptr), None)

    # avoid potential circular import
    from pyglet.image import Image
    return Image(image_data, width, height, bpp)

