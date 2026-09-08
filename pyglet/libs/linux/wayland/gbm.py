from ctypes import *

import pyglet.lib


_lib = pyglet.lib.load_library('gbm')


class c_void(Structure):
    # c_void_p is a buggy return type, converting to int, so
    # POINTER(None) == c_void_p is actually written as
    # POINTER(c_void), so it can be treated as a real pointer.
    _fields_ = [('dummy', c_int)]


class struct_gbm_bo(Structure):
    _fields_ = [('_opaque_struct', c_int)]


class struct_gbm_bo_handle(Union):
    _fields_ = [('_opaque_struct', c_int)]


class struct_gbm_device(Structure):
    _fields_ = [('_opaque_struct', c_int)]


class struct_gbm_surface(Structure):
    _fields_ = [('_opaque_struct', c_int)]


class struct_gbm_format_name_desc(Structure):
    _fields_ = [('_opaque_struct', c_int)]


__GBM__ = 1  # /usr/include/gbm.h:31

# enum
# GBM_BO_FORMAT_XRGB8888
# GBM_BO_FORMAT_ARGB8888

GBM_BO_USE_SCANOUT = (1 << 0)
GBM_BO_USE_CURSOR = (1 << 1)
GBM_BO_USE_CURSOR_64X64 = GBM_BO_USE_CURSOR
GBM_BO_USE_RENDERING = (1 << 2)

GBM_BO_USE_WRITE = (1 << 3)
GBM_BO_USE_LINEAR = (1 << 4)
GBM_BO_USE_PROTECTED = (1 << 5)

GBM_BO_TRANSFER_READ = (1 << 0)
GBM_BO_TRANSFER_WRITE = (1 << 1)
GBM_BO_TRANSFER_READ_WRITE = (GBM_BO_TRANSFER_READ | GBM_BO_TRANSFER_WRITE)


# TODO: pre-calculate all of the fourcc values
def __gbm_fourcc_code(a, b, c, d):
    a, b, c, d = ord(a), ord(b), ord(c), ord(d)
    return c_uint32(a).value | (c_uint32(b).value << 8) | (c_uint32(c).value << 16) | (c_uint32(d).value << 24)


GBM_FORMAT_BIG_ENDIAN = (1 << 31)
GBM_FORMAT_C8 = __gbm_fourcc_code('C', '8', ' ', ' ')
GBM_FORMAT_R8 = __gbm_fourcc_code('R', '8', ' ', ' ')
GBM_FORMAT_R16 = __gbm_fourcc_code('R', '1', '6', ' ')

GBM_FORMAT_GR88 = __gbm_fourcc_code('G', 'R', '8', '8')

GBM_FORMAT_RG1616 = __gbm_fourcc_code('R', 'G', '3', '2')
GBM_FORMAT_GR1616 = __gbm_fourcc_code('G', 'R', '3', '2')

GBM_FORMAT_RGB332 = __gbm_fourcc_code('R', 'G', 'B', '8')
GBM_FORMAT_BGR233 = __gbm_fourcc_code('B', 'G', 'R', '8')

GBM_FORMAT_XRGB4444 = __gbm_fourcc_code('X', 'R', '1', '2')
GBM_FORMAT_XBGR4444 = __gbm_fourcc_code('X', 'B', '1', '2')
GBM_FORMAT_RGBX4444 = __gbm_fourcc_code('R', 'X', '1', '2')
GBM_FORMAT_BGRX4444 = __gbm_fourcc_code('B', 'X', '1', '2')

GBM_FORMAT_ARGB4444 = __gbm_fourcc_code('A', 'R', '1', '2')
GBM_FORMAT_ABGR4444 = __gbm_fourcc_code('A', 'B', '1', '2')
GBM_FORMAT_RGBA4444 = __gbm_fourcc_code('R', 'A', '1', '2')
GBM_FORMAT_BGRA4444 = __gbm_fourcc_code('B', 'A', '1', '2')

GBM_FORMAT_XRGB1555 = __gbm_fourcc_code('X', 'R', '1', '5')
GBM_FORMAT_XBGR1555 = __gbm_fourcc_code('X', 'B', '1', '5')
GBM_FORMAT_RGBX5551 = __gbm_fourcc_code('R', 'X', '1', '5')
GBM_FORMAT_BGRX5551 = __gbm_fourcc_code('B', 'X', '1', '5')

GBM_FORMAT_ARGB1555 = __gbm_fourcc_code('A', 'R', '1', '5')
GBM_FORMAT_ABGR1555 = __gbm_fourcc_code('A', 'B', '1', '5')
GBM_FORMAT_RGBA5551 = __gbm_fourcc_code('R', 'A', '1', '5')
GBM_FORMAT_BGRA5551 = __gbm_fourcc_code('B', 'A', '1', '5')

GBM_FORMAT_RGB565 = __gbm_fourcc_code('R', 'G', '1', '6')
GBM_FORMAT_BGR565 = __gbm_fourcc_code('B', 'G', '1', '6')

GBM_FORMAT_RGB888 = __gbm_fourcc_code('R', 'G', '2', '4')
GBM_FORMAT_BGR888 = __gbm_fourcc_code('B', 'G', '2', '4')

GBM_FORMAT_XRGB8888 = __gbm_fourcc_code('X', 'R', '2', '4')
GBM_FORMAT_XBGR8888 = __gbm_fourcc_code('X', 'B', '2', '4')
GBM_FORMAT_RGBX8888 = __gbm_fourcc_code('R', 'X', '2', '4')
GBM_FORMAT_BGRX8888 = __gbm_fourcc_code('B', 'X', '2', '4')

GBM_FORMAT_ARGB8888 = __gbm_fourcc_code('A', 'R', '2', '4')
GBM_FORMAT_ABGR8888 = __gbm_fourcc_code('A', 'B', '2', '4')
GBM_FORMAT_RGBA8888 = __gbm_fourcc_code('R', 'A', '2', '4')
GBM_FORMAT_BGRA8888 = __gbm_fourcc_code('B', 'A', '2', '4')

GBM_FORMAT_XRGB2101010 = __gbm_fourcc_code('X', 'R', '3', '0')
GBM_FORMAT_XBGR2101010 = __gbm_fourcc_code('X', 'B', '3', '0')
GBM_FORMAT_RGBX1010102 = __gbm_fourcc_code('R', 'X', '3', '0')
GBM_FORMAT_BGRX1010102 = __gbm_fourcc_code('B', 'X', '3', '0')

GBM_FORMAT_ARGB2101010 = __gbm_fourcc_code('A', 'R', '3', '0')
GBM_FORMAT_ABGR2101010 = __gbm_fourcc_code('A', 'B', '3', '0')
GBM_FORMAT_RGBA1010102 = __gbm_fourcc_code('R', 'A', '3', '0')
GBM_FORMAT_BGRA1010102 = __gbm_fourcc_code('B', 'A', '3', '0')

GBM_FORMAT_XBGR16161616F = __gbm_fourcc_code('X', 'B', '4', 'H')
GBM_FORMAT_ABGR16161616F = __gbm_fourcc_code('A', 'B', '4', 'H')

GBM_FORMAT_YUYV = __gbm_fourcc_code('Y', 'U', 'Y', 'V')
GBM_FORMAT_YVYU = __gbm_fourcc_code('Y', 'V', 'Y', 'U')
GBM_FORMAT_UYVY = __gbm_fourcc_code('U', 'Y', 'V', 'Y')
GBM_FORMAT_VYUY = __gbm_fourcc_code('V', 'Y', 'U', 'Y')

GBM_FORMAT_AYUV = __gbm_fourcc_code('A', 'Y', 'U', 'V')
GBM_FORMAT_NV12 = __gbm_fourcc_code('N', 'V', '1', '2')
GBM_FORMAT_NV21 = __gbm_fourcc_code('N', 'V', '2', '1')
GBM_FORMAT_NV16 = __gbm_fourcc_code('N', 'V', '1', '6')
GBM_FORMAT_NV61 = __gbm_fourcc_code('N', 'V', '6', '1')

GBM_FORMAT_YUV410 = __gbm_fourcc_code('Y', 'U', 'V', '9')
GBM_FORMAT_YVU410 = __gbm_fourcc_code('Y', 'V', 'U', '9')
GBM_FORMAT_YUV411 = __gbm_fourcc_code('Y', 'U', '1', '1')
GBM_FORMAT_YVU411 = __gbm_fourcc_code('Y', 'V', '1', '1')
GBM_FORMAT_YUV420 = __gbm_fourcc_code('Y', 'U', '1', '2')
GBM_FORMAT_YVU420 = __gbm_fourcc_code('Y', 'V', '1', '2')
GBM_FORMAT_YUV422 = __gbm_fourcc_code('Y', 'U', '1', '6')
GBM_FORMAT_YVU422 = __gbm_fourcc_code('Y', 'V', '1', '6')
GBM_FORMAT_YUV444 = __gbm_fourcc_code('Y', 'U', '2', '4')
GBM_FORMAT_YVU444 = __gbm_fourcc_code('Y', 'V', '2', '4')


# /usr/include/gbm.h:257
gbm_device_get_fd = _lib.gbm_device_get_fd
gbm_device_get_fd.restype = c_int
gbm_device_get_fd.argtypes = [POINTER(struct_gbm_device)]

# /usr/include/gbm.h:259
gbm_device_get_backend_name = _lib.gbm_device_get_backend_name
gbm_device_get_backend_name.restype = c_char_p
gbm_device_get_backend_name.argtypes = [POINTER(struct_gbm_device)]

# /usr/include/gbm.h:263
gbm_device_is_format_supported = _lib.gbm_device_is_format_supported
gbm_device_is_format_supported.restype = c_int
gbm_device_is_format_supported.argtypes = [POINTER(struct_gbm_device), c_uint32, c_uint32]

# /usr/include/gbm.h:267
gbm_device_get_format_modifier_plane_count = _lib.gbm_device_get_format_modifier_plane_count
gbm_device_get_format_modifier_plane_count.restype = c_int
gbm_device_get_format_modifier_plane_count.argtypes = [POINTER(struct_gbm_device), c_uint32, c_uint64]

# /usr/include/gbm.h:272
gbm_device_destroy = _lib.gbm_device_destroy
gbm_device_destroy.restype = None
gbm_device_destroy.argtypes = [POINTER(struct_gbm_device)]

# /usr/include/gbm.h:274
gbm_create_device = _lib.gbm_create_device
gbm_create_device.restype = POINTER(struct_gbm_device)
gbm_create_device.argtypes = [c_int]


# /usr/include/gbm.h:277
gbm_bo_create = _lib.gbm_bo_create
gbm_bo_create.restype = POINTER(struct_gbm_bo)
gbm_bo_create.argtypes = [POINTER(struct_gbm_device), c_uint32, c_uint32, c_uint32, c_uint32]

# /usr/include/gbm.h:282
gbm_bo_create_with_modifiers = _lib.gbm_bo_create_with_modifiers
gbm_bo_create_with_modifiers.restype = POINTER(struct_gbm_bo)
gbm_bo_create_with_modifiers.argtypes = [POINTER(struct_gbm_device), c_uint32, c_uint32, c_uint32, POINTER(c_uint64),
                                         c_uint]

# /usr/include/gbm.h:289
gbm_bo_create_with_modifiers2 = _lib.gbm_bo_create_with_modifiers2
gbm_bo_create_with_modifiers2.restype = POINTER(struct_gbm_bo)
gbm_bo_create_with_modifiers2.argtypes = [POINTER(struct_gbm_device), c_uint32, c_uint32, c_uint32, POINTER(c_uint64),
                                          c_uint, c_uint32]

GBM_BO_IMPORT_WL_BUFFER = 21761  # /usr/include/gbm.h:297
GBM_BO_IMPORT_EGL_IMAGE = 21762  # /usr/include/gbm.h:298
GBM_BO_IMPORT_FD = 21763  # /usr/include/gbm.h:299
GBM_BO_IMPORT_FD_MODIFIER = 21764  # /usr/include/gbm.h:300
GBM_MAX_PLANES = 4  # /usr/include/gbm.h:310

# /usr/include/gbm.h:323
gbm_bo_import = _lib.gbm_bo_import
gbm_bo_import.restype = POINTER(struct_gbm_bo)
gbm_bo_import.argtypes = [POINTER(struct_gbm_device), c_uint32, POINTER(None), c_uint32]

# /usr/include/gbm.h:354
gbm_bo_map = _lib.gbm_bo_map
gbm_bo_map.restype = POINTER(c_void)
gbm_bo_map.argtypes = [POINTER(struct_gbm_bo), c_uint32, c_uint32, c_uint32, c_uint32, c_uint32, POINTER(c_uint32),
                       POINTER(POINTER(None))]

# /usr/include/gbm.h:360
gbm_bo_unmap = _lib.gbm_bo_unmap
gbm_bo_unmap.restype = None
gbm_bo_unmap.argtypes = [POINTER(struct_gbm_bo), POINTER(None)]

# /usr/include/gbm.h:363
gbm_bo_get_width = _lib.gbm_bo_get_width
gbm_bo_get_width.restype = c_uint32
gbm_bo_get_width.argtypes = [POINTER(struct_gbm_bo)]

# /usr/include/gbm.h:366
gbm_bo_get_height = _lib.gbm_bo_get_height
gbm_bo_get_height.restype = c_uint32
gbm_bo_get_height.argtypes = [POINTER(struct_gbm_bo)]

# /usr/include/gbm.h:369
gbm_bo_get_stride = _lib.gbm_bo_get_stride
gbm_bo_get_stride.restype = c_uint32
gbm_bo_get_stride.argtypes = [POINTER(struct_gbm_bo)]

# /usr/include/gbm.h:372
gbm_bo_get_stride_for_plane = _lib.gbm_bo_get_stride_for_plane
gbm_bo_get_stride_for_plane.restype = c_uint32
gbm_bo_get_stride_for_plane.argtypes = [POINTER(struct_gbm_bo), c_int]

# /usr/include/gbm.h:375
gbm_bo_get_format = _lib.gbm_bo_get_format
gbm_bo_get_format.restype = c_uint32
gbm_bo_get_format.argtypes = [POINTER(struct_gbm_bo)]

# /usr/include/gbm.h:378
gbm_bo_get_bpp = _lib.gbm_bo_get_bpp
gbm_bo_get_bpp.restype = c_uint32
gbm_bo_get_bpp.argtypes = [POINTER(struct_gbm_bo)]

# /usr/include/gbm.h:381
gbm_bo_get_offset = _lib.gbm_bo_get_offset
gbm_bo_get_offset.restype = c_uint32
gbm_bo_get_offset.argtypes = [POINTER(struct_gbm_bo), c_int]

# /usr/include/gbm.h:383
gbm_bo_get_device = _lib.gbm_bo_get_device
gbm_bo_get_device.restype = POINTER(struct_gbm_device)
gbm_bo_get_device.argtypes = [POINTER(struct_gbm_bo)]

# /usr/include/gbm.h:387
gbm_bo_get_handle = _lib.gbm_bo_get_handle
gbm_bo_get_handle.restype = struct_gbm_bo_handle
gbm_bo_get_handle.argtypes = [POINTER(struct_gbm_bo)]

# /usr/include/gbm.h:390
gbm_bo_get_fd = _lib.gbm_bo_get_fd
gbm_bo_get_fd.restype = c_int
gbm_bo_get_fd.argtypes = [POINTER(struct_gbm_bo)]

# /usr/include/gbm.h:393
gbm_bo_get_modifier = _lib.gbm_bo_get_modifier
gbm_bo_get_modifier.restype = c_uint64
gbm_bo_get_modifier.argtypes = [POINTER(struct_gbm_bo)]

# /usr/include/gbm.h:396
gbm_bo_get_plane_count = _lib.gbm_bo_get_plane_count
gbm_bo_get_plane_count.restype = c_int
gbm_bo_get_plane_count.argtypes = [POINTER(struct_gbm_bo)]

# /usr/include/gbm.h:399
gbm_bo_get_handle_for_plane = _lib.gbm_bo_get_handle_for_plane
gbm_bo_get_handle_for_plane.restype = struct_gbm_bo_handle
gbm_bo_get_handle_for_plane.argtypes = [POINTER(struct_gbm_bo), c_int]

# /usr/include/gbm.h:402
gbm_bo_get_fd_for_plane = _lib.gbm_bo_get_fd_for_plane
gbm_bo_get_fd_for_plane.restype = c_int
gbm_bo_get_fd_for_plane.argtypes = [POINTER(struct_gbm_bo), c_int]

# /usr/include/gbm.h:405
gbm_bo_write = _lib.gbm_bo_write
gbm_bo_write.restype = c_int
gbm_bo_write.argtypes = [POINTER(struct_gbm_bo), POINTER(None), c_size_t]

# /usr/include/gbm.h:408
gbm_bo_set_user_data = _lib.gbm_bo_set_user_data
gbm_bo_set_user_data.restype = None
gbm_bo_set_user_data.argtypes = [POINTER(struct_gbm_bo), POINTER(None),
                                 CFUNCTYPE(None, POINTER(struct_gbm_bo), POINTER(None))]

# /usr/include/gbm.h:411
gbm_bo_get_user_data = _lib.gbm_bo_get_user_data
gbm_bo_get_user_data.restype = POINTER(c_void)
gbm_bo_get_user_data.argtypes = [POINTER(struct_gbm_bo)]

# /usr/include/gbm.h:415
gbm_bo_destroy = _lib.gbm_bo_destroy
gbm_bo_destroy.restype = None
gbm_bo_destroy.argtypes = [POINTER(struct_gbm_bo)]

# /usr/include/gbm.h:417
gbm_surface_create = _lib.gbm_surface_create
gbm_surface_create.restype = POINTER(struct_gbm_surface)
gbm_surface_create.argtypes = [POINTER(struct_gbm_device), c_uint32, c_uint32, c_uint32, c_uint32]

# /usr/include/gbm.h:422
gbm_surface_create_with_modifiers = _lib.gbm_surface_create_with_modifiers
gbm_surface_create_with_modifiers.restype = POINTER(struct_gbm_surface)
gbm_surface_create_with_modifiers.argtypes = [POINTER(struct_gbm_device), c_uint32, c_uint32, c_uint32,
                                              POINTER(c_uint64), c_uint]

# /usr/include/gbm.h:429
gbm_surface_create_with_modifiers2 = _lib.gbm_surface_create_with_modifiers2
gbm_surface_create_with_modifiers2.restype = POINTER(struct_gbm_surface)
gbm_surface_create_with_modifiers2.argtypes = [POINTER(struct_gbm_device), c_uint32, c_uint32, c_uint32,
                                               POINTER(c_uint64), c_uint, c_uint32]

# /usr/include/gbm.h:437
gbm_surface_lock_front_buffer = _lib.gbm_surface_lock_front_buffer
gbm_surface_lock_front_buffer.restype = POINTER(struct_gbm_bo)
gbm_surface_lock_front_buffer.argtypes = [POINTER(struct_gbm_surface)]

# /usr/include/gbm.h:441
gbm_surface_release_buffer = _lib.gbm_surface_release_buffer
gbm_surface_release_buffer.restype = None
gbm_surface_release_buffer.argtypes = [POINTER(struct_gbm_surface), POINTER(struct_gbm_bo)]

# /usr/include/gbm.h:444
gbm_surface_has_free_buffers = _lib.gbm_surface_has_free_buffers
gbm_surface_has_free_buffers.restype = c_int
gbm_surface_has_free_buffers.argtypes = [POINTER(struct_gbm_surface)]

# /usr/include/gbm.h:447
gbm_surface_destroy = _lib.gbm_surface_destroy
gbm_surface_destroy.restype = None
gbm_surface_destroy.argtypes = [POINTER(struct_gbm_surface)]

# /usr/include/gbm.h:449
gbm_format_get_name = _lib.gbm_format_get_name
gbm_format_get_name.restype = c_char_p
gbm_format_get_name.argtypes = [c_uint32, POINTER(struct_gbm_format_name_desc)]
