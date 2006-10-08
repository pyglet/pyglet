'''

OMG

This library uses setmp/longjmp for error "handling" too! See comments in
pyglet.image.png


'''

import sys

from ctypes import *

path = util.find_library('c')
_libc = cdll.LoadLibrary(path)
_libc.fopen.argtypes = [c_char_p, c_char_p]
_libc.fopen.restype = c_void_p
_libc.fclose.argtypes = [c_void_p]
_libc.fclose.restype = None

path = util.find_library('jpeg')
_libjpeg = cdll.LoadLibrary(path)
def _get_function(name, argtypes, rtype):
    try:
        func = getattr(_libjpeg, name)
        func.argtypes = argtypes
        func.restype = rtype
        return func
    except AttributeError, e:
            raise ImportError(e)

JPEG_LIB_VERSION = 62
boolean = c_int
JDIMENSION = c_uint
J_COLOR_SPACE = c_int
J_DCT_METHOD = c_int
J_DITHER_MODE = c_int
JSAMPARRAY = c_void_p
DCTSIZE2 = 64
COEF_BITS = POINTER(c_int) * DCTSIZE2
JQUANT_TBL = c_void_p
NUM_QUANT_TBLS = 4
QUANT_TBLS = JQUANT_TBL * NUM_QUANT_TBLS
JHUFF_TBL = c_void_p
NUM_HUFF_TBLS = 4
HUFF_TBLS = JHUFF_TBL * NUM_HUFF_TBLS
NUM_ARITH_TBLS = 16
ARITH_TBL = c_ubyte * NUM_ARITH_TBLS
jpeg_saved_marker_ptr = c_void_p
JSAMPLE = c_void_p
MAX_COMPS_IN_SCAN = 4
cur_comp_info = c_void_p * MAX_COMPS_IN_SCAN
D_MAX_BLOCKS_IN_MCU = 10
MCU_membership = c_int * D_MAX_BLOCKS_IN_MCU

JMSG_STR_PARM_MAX = 80
class MSG_PARM(Union):
    _fields_ = [
        ('i', c_int * 8),
        ('s', c_char * JMSG_STR_PARM_MAX),
    ]
class jpeg_error_mgr(Structure):
    _fields_ = [
        ('error_exit', c_void_p),
        ('emit_message', c_void_p),
        ('output_message', c_void_p),
        ('format_message', c_void_p),
        ('reset_error_mgr', c_void_p),
        ('msg_code', c_int),
        ('msg_parm', MSG_PARM),
        ('trace_level', c_int),
        ('num_warnings', c_long),
        ('jpeg_message_table', c_void_p),
        ('last_jpeg_message', c_int),
        ('addon_message_table', c_void_p),
        ('first_addon_message', c_int),
        ('last_addon_message', c_int),
    ]

class jpeg_decompress_struct(Structure):
    _fields_ = [
        ('err', POINTER(jpeg_error_mgr)),
        ('mem', c_void_p),
        ('progress', c_void_p),
        ('client_data', c_void_p),
        ('is_decompressor', boolean),
        ('global_state', c_int),

        ('src', c_void_p),
        ('image_width', JDIMENSION),
        ('image_height', JDIMENSION),
        ('num_components', c_int),
        ('jpeg_color_space', J_COLOR_SPACE),

        ('out_color_space', J_COLOR_SPACE),
        ('scale_num', c_uint),
        ('scale_denom', c_uint),
        ('output_gamma', c_double),
        ('buffered_image', boolean),
        ('raw_data_out', boolean),
        ('dct_method', J_DCT_METHOD),
        ('do_fancy_upsampling', boolean),
        ('do_block_smoothing', boolean),

        ('quantize_colors', boolean),
        ('dither_mode', J_DITHER_MODE),
        ('two_pass_quantize', boolean),
        ('desired_number_of_colors', c_int),
        ('enable_1pass_quant', boolean),
        ('enable_external_quant', boolean),
        ('enable_2pass_quant', boolean),

        ('output_width', JDIMENSION),
        ('output_height', JDIMENSION),
        ('out_color_components', c_int),
        ('output_components', c_int),

        ('rec_outbuf_height', c_int),
        ('actual_number_of_colors', c_int),
        ('colormap', JSAMPARRAY),

        ('output_scanline', JDIMENSION),
        ('input_scan_number', c_int),
        ('input_iMCU_row', JDIMENSION),
        ('output_scan_number', c_int),

        ('output_iMCU_row', JDIMENSION),

        # XXX odd, having this here causes the structure size to be waaay
        # too big - hence now c_void_p
        ('coef_bits', c_void_p), #COEF_BITS),

        ('quant_tbl_ptrs', QUANT_TBLS),
        ('dc_huff_tbl_ptrs', HUFF_TBLS),
        ('ac_huff_tbl_ptrs', HUFF_TBLS),
        ('data_precision', c_int),
        ('comp_info', c_void_p),
        ('progressive_mode', c_int),
        ('arith_code', c_int),
        ('arith_dc_L', ARITH_TBL),
        ('arith_dc_U', ARITH_TBL),
        ('arith_ac_K', ARITH_TBL),
        ('restart_interval', c_uint),
        ('saw_JFIF_marker', c_int),
        ('JFIF_major_version', c_ubyte),
        ('JFIF_minor_version', c_ubyte),
        ('density_unit', c_ubyte),
        ('X_density_1', c_ubyte),       # X_density and Y_density are
        ('X_density_2', c_ubyte),       # actually UINT16 but ctypes
        ('Y_density_1', c_ubyte),       # doesn't give us a 16-bit data
        ('Y_density_2', c_ubyte),       # type
        ('saw_Adobe_marker', c_int),
        ('Adobe_transform', c_ubyte),
        ('CCIR601_sampling', c_int),
        ('marker_list', jpeg_saved_marker_ptr),
        ('max_h_samp_factor', c_int),
        ('max_v_samp_factor', c_int),
        ('min_DCT_scaled_size', c_int),
        ('total_iMCU_rows', JDIMENSION),
        ('sample_range_limit', JSAMPLE),
        ('comps_in_scan', c_int),
        ('cur_comp_info', cur_comp_info),
        ('MCUs_per_row', JDIMENSION),
        ('MCU_rows_in_scan', JDIMENSION),
        ('blocks_in_MCU', c_int),
        ('MCU_membership', MCU_membership),
        ('Ss', c_int),
        ('Se', c_int),
        ('Ah', c_int),
        ('Al', c_int),
        ('unread_marker', c_int),
        ('master', c_void_p),
        ('main', c_void_p),
        ('coef', c_void_p),
        ('post', c_void_p),
        ('inputctl', c_void_p),
        ('marker', c_void_p),
        ('entropy', c_void_p),
        ('idct', c_void_p),
        ('upsample', c_void_p),
        ('cconvert', c_void_p),
        ('cquantize', c_void_p),
    ]

jpeg_std_error = _get_function('jpeg_std_error',
    [POINTER(jpeg_error_mgr)], POINTER(jpeg_error_mgr))
jpeg_CreateDecompress = _get_function('jpeg_CreateDecompress',
    [POINTER(jpeg_decompress_struct), c_int, c_int], None)
jpeg_stdio_src = _get_function('jpeg_stdio_src',
    [POINTER(jpeg_decompress_struct), c_void_p], None)
jpeg_read_header = _get_function('jpeg_read_header',
    [POINTER(jpeg_decompress_struct), boolean], c_int)
jpeg_start_decompress = _get_function('jpeg_start_decompress',
    [POINTER(jpeg_decompress_struct)], boolean)
jpeg_read_scanlines = _get_function('jpeg_read_scanlines',
    [POINTER(jpeg_decompress_struct), JSAMPARRAY, JDIMENSION], JDIMENSION)
jpeg_finish_decompress = _get_function('jpeg_finish_decompress',
    [POINTER(jpeg_decompress_struct)], boolean)
jpeg_destroy_decompress = _get_function('jpeg_destroy_decompress',
    [POINTER(jpeg_decompress_struct)], None)

def ptr_add(ptr, offset):
    address = addressof(ptr.contents) + offset
    return pointer(type(ptr.contents).from_address(address))

def is_jpeg(filename):
    ''' Determine whether "filename" is a PNG file '''
    image = open(filename)
    header = image.read(10)
    image.close()
    return header.startswith('\xFF\xD8\xFF\xE0') and header.endswith('JFIF')

def read(filename):
    if not is_jpeg(filename):
        raise ValueError, '%r is not a JPEG'%(filename,)

    infile = _libc.fopen(filename, "rb")
    if not infile:
        # this shouldn't happen - is_jpeg has already opened it, but there
        # is the chance of a race condition
        raise ValueError, 'Cannot open %r'

    cinfo = jpeg_decompress_struct()
    print sizeof(cinfo)

    jerr = jpeg_error_mgr()
    cinfo.err = jpeg_std_error(byref(jerr))

    # Step 1: allocate and initialize JPEG decompression object
    jpeg_CreateDecompress(byref(cinfo), JPEG_LIB_VERSION, sizeof(cinfo))

    # Step 2: specify data source (eg, a file)
    jpeg_stdio_src(byref(cinfo), infile)

    # Step 3: read file parameters with jpeg_read_header()
    jpeg_read_header(byref(cinfo), True)

    # XXX Step 4: set parameters for decompression
    # In this example, we don't need to change any of the defaults set by
    # jpeg_read_header(), so we do nothing here.

    # Step 5: Start decompressor
    jpeg_start_decompress(byref(cinfo))

    # JSAMPLEs per row in output buffer
    width = cinfo.output_width
    height = cinfo.output_height
    bpp = cinfo.output_components

    # Make a one-row-high sample array that will go away when done with image
    image_data = create_string_buffer(width * height * bpp)
    image_data_ptr = cast(image_data, POINTER(c_char))
    y = 0
    while cinfo.output_scanline < height:
        row = ptr_add(image_data_ptr, width * bpp * y)
        jpeg_read_scanlines(byref(cinfo), byref(row), 1)
        y += 1

    jpeg_finish_decompress(byref(cinfo))

    # Step 8: Release JPEG decompression object

    jpeg_destroy_decompress(byref(cinfo))

    _libc.fclose(infile)

    # avoid potential circular import
    from pyglet.image import Image
    return Image(image_data, width, height, bpp)

