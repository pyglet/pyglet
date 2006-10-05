'''

POSSIBLE TODO ITEMS:

1. error callbacks
2. load directly into a large buffer rather than via the rows
'''



import sys

from ctypes import *

path = util.find_library('c')
libc = cdll.LoadLibrary(path)
#libc = cdll.LoadLibrary('libc.so.6')   # XXX might be needed under linux
libc.fdopen.argtypes = [c_int, c_char_p]
libc.fdopen.restype = c_void_p
libc.rewind.argtypes = [c_char_p]

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

# These describe the color_type field in png_info. 
# color type masks 
PNG_COLOR_MASK_PALETTE = 1
PNG_COLOR_MASK_COLOR = 2
PNG_COLOR_MASK_ALPHA = 4

# color types.  Note that not all combinations are legal 
PNG_COLOR_TYPE_GRAY = 0
PNG_COLOR_TYPE_PALETTE = (PNG_COLOR_MASK_COLOR | PNG_COLOR_MASK_PALETTE)
PNG_COLOR_TYPE_RGB = (PNG_COLOR_MASK_COLOR)
PNG_COLOR_TYPE_RGB_ALPHA = (PNG_COLOR_MASK_COLOR | PNG_COLOR_MASK_ALPHA)
PNG_COLOR_TYPE_GRAY_ALPHA = (PNG_COLOR_MASK_ALPHA)
# aliases 
PNG_COLOR_TYPE_RGBA = PNG_COLOR_TYPE_RGB_ALPHA
PNG_COLOR_TYPE_GA = PNG_COLOR_TYPE_GRAY_ALPHA

# This is for compression type. PNG 1.0-1.2 only define the single type. 
PNG_COMPRESSION_TYPE_BASE = 0 # Deflate method 8, 32K window 
PNG_COMPRESSION_TYPE_DEFAULT = PNG_COMPRESSION_TYPE_BASE

# This is for filter type. PNG 1.0-1.2 only define the single type. 
PNG_FILTER_TYPE_BASE = 0 # Single row per-byte filtering 
PNG_INTRAPIXEL_DIFFERENCING = 64 # Used only in MNG datastreams 
PNG_FILTER_TYPE_DEFAULT = PNG_FILTER_TYPE_BASE

# These are for the interlacing type.  These values should NOT be changed. 
PNG_INTERLACE_NONE = 0 # Non-interlaced image 
PNG_INTERLACE_ADAM7 = 1 # Adam7 interlacing 
PNG_INTERLACE_LAST = 2 # Not a valid value 

# These are for the oFFs chunk.  These values should NOT be changed. 
PNG_OFFSET_PIXEL = 0 # Offset in pixels 
PNG_OFFSET_MICROMETER = 1 # Offset in micrometers (1/10^6 meter) 
PNG_OFFSET_LAST = 2 # Not a valid value 

# These are for the pCAL chunk.  These values should NOT be changed. 
PNG_EQUATION_LINEAR = 0 # Linear transformation 
PNG_EQUATION_BASE_E = 1 # Exponential base e transform 
PNG_EQUATION_ARBITRARY = 2 # Arbitrary base exponential transform 
PNG_EQUATION_HYPERBOLIC = 3 # Hyperbolic sine transformation 
PNG_EQUATION_LAST = 4 # Not a valid value 

# These are for the sCAL chunk.  These values should NOT be changed. 
PNG_SCALE_UNKNOWN = 0 # unknown unit (image scale) 
PNG_SCALE_METER = 1 # meters per pixel 
PNG_SCALE_RADIAN = 2 # radians per pixel 
PNG_SCALE_LAST = 3 # Not a valid value 

# These are for the pHYs chunk.  These values should NOT be changed. 
PNG_RESOLUTION_UNKNOWN = 0 # pixels/unknown unit (aspect ratio) 
PNG_RESOLUTION_METER = 1 # pixels/meter 
PNG_RESOLUTION_LAST = 2 # Not a valid value 

# These are for the sRGB chunk.  These values should NOT be changed. 
PNG_sRGB_INTENT_PERCEPTUAL = 0
PNG_sRGB_INTENT_RELATIVE = 1
PNG_sRGB_INTENT_SATURATION = 2
PNG_sRGB_INTENT_ABSOLUTE = 3
PNG_sRGB_INTENT_LAST = 4 # Not a valid value 

# This is for text chunks 
PNG_KEYWORD_MAX_LENGTH = 79

# Maximum number of entries in PLTE/sPLT/tRNS arrays 
PNG_MAX_PALETTE_LENGTH = 256

# These determine if an ancillary chunk's data has been successfully read
# from the PNG header, or if the application has filled in the corresponding
# data in the info_struct to be written into the output file.  The values
# of the PNG_INFO_<chunk> defines should NOT be changed.
PNG_INFO_gAMA = 0x0001
PNG_INFO_sBIT = 0x0002
PNG_INFO_cHRM = 0x0004
PNG_INFO_PLTE = 0x0008
PNG_INFO_tRNS = 0x0010
PNG_INFO_bKGD = 0x0020
PNG_INFO_hIST = 0x0040
PNG_INFO_pHYs = 0x0080
PNG_INFO_oFFs = 0x0100
PNG_INFO_tIME = 0x0200
PNG_INFO_pCAL = 0x0400
PNG_INFO_sRGB = 0x0800   # GR-P, 0.96a 
PNG_INFO_iCCP = 0x1000   # ESR, 1.0.6 
PNG_INFO_sPLT = 0x2000   # ESR, 1.0.6 
PNG_INFO_sCAL = 0x4000   # ESR, 1.0.6 
PNG_INFO_IDAT = 0x8000L  # ESR, 1.0.6 

def ptr_add(ptr, offset):
    address = addressof(ptr.contents) + offset
    return pointer(type(ptr.contents).from_address(address))
     

def read(filename):
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

    # read the info struct and pull out the important info
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
        components = 4
    else:
        components = 3

    # Copy image data from row pointers (there is no guarantee that data
    # is already sequential).
    # XXX need to scale up to power-of-2 size
    image_data = create_string_buffer(width * height * components)
    image_data_ptr = cast(image_data, POINTER(c_char))
    row_pointers = libpng.png_get_rows(png_ptr, info_ptr)
    for y in xrange(height):
        row = ptr_add(image_data_ptr, width * components * y)
        memmove(row, row_pointers[height-y-1], width * components)

    # free up everything
    libpng.png_destroy_read_struct(byref(png_ptr), byref(info_ptr), None)

    # avoid potential circular import
    from pyglet.image import Image
    return Image(image_data, width, height, components)

