"""Wrapper for include/libavutil/avutil.h
"""
from ctypes import c_char_p, c_void_p, POINTER, Structure, c_double, c_char, Union
from ctypes import c_int, c_int64, c_uint64
from ctypes import c_uint8, c_int8, c_uint, c_size_t

import pyglet.lib
from pyglet.util import debug_print
from . import compat

_debug = debug_print('debug_media')

avutil = pyglet.lib.load_library(
    'avutil',
    win32=('avutil-60', 'avutil-59', 'avutil-58', 'avutil-57', 'avutil-56'),
    darwin=('avutil.60', 'avutil.59', 'avutil.58', 'avutil.57', 'avutil.56')
)

avutil.avutil_version.restype = c_int

avutil_version = avutil.avutil_version() >> 16

compat.set_version('avutil', avutil_version)

AVMEDIA_TYPE_UNKNOWN = -1
AVMEDIA_TYPE_VIDEO = 0
AVMEDIA_TYPE_AUDIO = 1
AVMEDIA_TYPE_DATA = 2
AVMEDIA_TYPE_SUBTITLE = 3
AVMEDIA_TYPE_ATTACHMENT = 4
AVMEDIA_TYPE_NB = 5

AV_SAMPLE_FMT_U8 = 0
AV_SAMPLE_FMT_S16 = 1
AV_SAMPLE_FMT_S32 = 2
AV_SAMPLE_FMT_FLT = 3
AV_SAMPLE_FORMAT_DOUBLE = 4
AV_SAMPLE_FMT_U8P = 5
AV_SAMPLE_FMT_S16P = 6
AV_SAMPLE_FMT_S32P = 7
AV_SAMPLE_FMT_FLTP = 8
AV_SAMPLE_FMT_DBLP = 9
AV_SAMPLE_FMT_S64 = 10
AV_SAMPLE_FMT_S64P = 11

AV_NUM_DATA_POINTERS = 8

AV_PIX_FMT_RGB24 = 2
AV_PIX_FMT_ARGB = 25
AV_PIX_FMT_RGBA = 26

AVChannel = c_int
AVChannelOrder = c_int

class AVChannelCustom(Structure):
    _fields_ = [
        ('id', AVChannel),
        ('name', c_char * 16),
        ('opaque', c_void_p)
    ]

class _AVChannelLayoutUnion(Union):
    _fields_ = [
        ('mask', c_uint64),
        ('map', POINTER(AVChannelCustom)),
    ]

class AVChannelLayout(Structure):
    _fields_ = [
        ('order', c_int),
        ('nb_channels', c_int),
        ('u', _AVChannelLayoutUnion),
        ('opaque', c_void_p)
    ]

    def __repr__(self):
        return f"{self.__class__.__name__}(order={self.order}, nb_channels={self.nb_channels})"

class AVBuffer(Structure):
    _fields_ = [
        ('data', POINTER(c_uint8)),
        ('size', c_int),
        # .. more
    ]


class AVBufferRef(Structure):
    _fields_ = [
        ('buffer', POINTER(AVBuffer)),
        ('data', POINTER(c_uint8)),
        ('size', c_int)
    ]


class AVDictionaryEntry(Structure):
    _fields_ = [
        ('key', c_char_p),
        ('value', c_char_p)
    ]


class AVDictionary(Structure):
    _fields_ = [
        ('count', c_int),
        ('elems', POINTER(AVDictionaryEntry))
    ]


class AVClass(Structure):
    pass


class AVRational(Structure):
    _fields_ = [
        ('num', c_int),
        ('den', c_int)
    ]

    def __repr__(self):
        return f"AVRational({self.num}/{self.den})"


class AVFrameSideData(Structure):
    pass


class AVFrame(Structure):
    pass

AVFrame_Fields = [
    ('data', POINTER(c_uint8) * AV_NUM_DATA_POINTERS),
    ('linesize', c_int * AV_NUM_DATA_POINTERS),
    ('extended_data', POINTER(POINTER(c_uint8))),
    ('width', c_int),
    ('height', c_int),
    ('nb_samples', c_int),
    ('format', c_int),
    ('key_frame', c_int),  # Deprecated in 59
    ('pict_type', c_int),
    ('sample_aspect_ratio', AVRational),
    ('pts', c_int64),
    ('pkt_pts', c_int64),  # Deprecated. Removed in 57.
    ('pkt_dts', c_int64),
    ('time_base', AVRational),  # Added (5.x)+
    ('coded_picture_number', c_int),  # removed in 59
    ('display_picture_number', c_int),  # removed in 59
    ('quality', c_int),
    ('opaque', c_void_p),
    ('error', c_uint64 * AV_NUM_DATA_POINTERS),  # Deprecated. Removed in 57.
    ('repeat_pict', c_int),
    ('interlaced_frame', c_int),  # deprecated in 59. Targeted for removal. Use AV_FRAME_FLAG_INTERLACED (removed in 60)
    ('top_field_first', c_int),  # deprecated in 59. Targeted for removal. Use AV_FRAME_FLAG_TOP_FIELD_FIRST (removed in 60)
    ('palette_has_changed', c_int),  # deprecated in 59. Targeted for removal. (removed in 60)
    ('reordered_opaque', c_int64),  # removed in 59.
    ('sample_rate', c_int),
    ('channel_layout', c_uint64),  # removed in 59.
    ('buf', POINTER(AVBufferRef) * AV_NUM_DATA_POINTERS),
    ('extended_buf', POINTER(POINTER(AVBufferRef))),
    ('nb_extended_buf', c_int),
    ('side_data', POINTER(POINTER(AVFrameSideData))),
    ('nb_side_data', c_int),
    ('flags', c_int),
    ('color_range', c_int),
    ('color_primaries', c_int),
    ('color_trc', c_int),
    ('colorspace', c_int),
    ('chroma_location', c_int),
    ('best_effort_timestamp', c_int64),
    ('pkt_pos', c_int64),  # deprecated in 59. Use AV_CODEC_FLAG_COPY_OPAQUE
    ('pkt_duration', c_int64),  # removed in 59?
    ('metadata', POINTER(AVDictionary)),
    ('decode_error_flags', c_int),
    ('channels', c_int),  # removed in 59.
    ('pkt_size', c_int),  # deprecated in 59.  use AV_CODEC_FLAG_COPY_OPAQUE to pass through arbitrary user data from packets to frames
    ('qscale_table', POINTER(c_int8)),  # Deprecated. Removed in 57.
    ('qstride', c_int),  # Deprecated. Removed in 57.
    ('qscale_type', c_int),  # Deprecated. Removed in 57.
    ('qp_table_buf', POINTER(AVBufferRef)),  # Deprecated. Removed in 57.
    ('hw_frames_ctx', POINTER(AVBufferRef)),
    ('opaque_ref', POINTER(AVBufferRef)),
    ('crop_top', c_size_t),  # video frames only
    ('crop_bottom', c_size_t),  # video frames only
    ('crop_left', c_size_t),  # video frames only
    ('crop_right', c_size_t),  # video frames only
    ('private_ref', POINTER(AVBufferRef)),
    ('ch_layout', AVChannelLayout),
    ('duration', c_int64)
]

compat.add_version_changes('avutil', 56, AVFrame, AVFrame_Fields,
                           removals=('time_base', 'ch_layout', 'duration'))

for compat_ver in (57, 58):
    compat.add_version_changes('avutil', compat_ver, AVFrame, AVFrame_Fields,
                               removals=('pkt_pts', 'error', 'qscale_table', 'qstride', 'qscale_type', 'qp_table_buf',
                                         'ch_layout', 'duration'))

compat.add_version_changes('avutil', 59, AVFrame, AVFrame_Fields,
                           removals=('pkt_pts', 'error', 'qscale_table', 'qstride', 'qscale_type', 'qp_table_buf',
                                     'channels', 'channel_layout',
                                     'coded_picture_number', 'display_picture_number', 'reordered_opaque',
                                     'pkt_duration',
                                     ))

compat.add_version_changes('avutil', 60, AVFrame, AVFrame_Fields,
                           removals=('pkt_pts', 'error', 'qscale_table', 'qstride', 'qscale_type', 'qp_table_buf',
                                     'channels', 'channel_layout',
                                     'coded_picture_number', 'display_picture_number', 'reordered_opaque',
                                     'pkt_duration',
                                     'interlaced_frame', 'top_field_first', 'palette_has_changed', 'pkt_pos',
                                     'pkt_size',
                                     ))

AV_NOPTS_VALUE = -0x8000000000000000
AV_TIME_BASE = 1000000
AV_TIME_BASE_Q = AVRational(1, AV_TIME_BASE)

avutil.av_version_info.restype = c_char_p
avutil.av_dict_get.restype = POINTER(AVDictionaryEntry)
avutil.av_dict_get.argtypes = [POINTER(AVDictionary),
                               c_char_p, POINTER(AVDictionaryEntry),
                               c_int]
avutil.av_rescale_q.restype = c_int64
avutil.av_rescale_q.argtypes = [c_int64, AVRational, AVRational]
avutil.av_samples_get_buffer_size.restype = c_int
avutil.av_samples_get_buffer_size.argtypes = [POINTER(c_int),
                                              c_int, c_int, c_int]
avutil.av_frame_alloc.restype = POINTER(AVFrame)
avutil.av_frame_free.argtypes = [POINTER(POINTER(AVFrame))]

AVSampleFormat = c_int

if avutil_version <= 57:
    # Removed in 7.x (avutil 58)
    avutil.av_get_default_channel_layout.restype = c_int64
    avutil.av_get_default_channel_layout.argtypes = [c_int]
else:
    # Available in 6.x  (avutil 58, 57)
    avutil.av_channel_layout_default.restype = None
    avutil.av_channel_layout_default.argtypes = [POINTER(AVChannelLayout), c_int]

    avutil.av_channel_layout_uninit.restype = None
    avutil.av_channel_layout_uninit.argtypes = [POINTER(AVChannelLayout)]

    avutil.av_opt_set.restype = c_int
    avutil.av_opt_set.argtypes = [c_void_p, c_char_p, c_char_p, c_int]

    avutil.av_opt_set_int.restype = c_int
    avutil.av_opt_set_int.argtypes = [c_void_p, c_char_p, c_int64, c_int]

    avutil.av_opt_set_double.restype = c_int
    avutil.av_opt_set_double.argtypes = [c_void_p, c_char_p, c_double, c_int]

    avutil.av_opt_set_sample_fmt.restype = c_int
    avutil.av_opt_set_sample_fmt.argtypes = [c_void_p, c_char_p, AVSampleFormat, c_int]

avutil.av_get_bytes_per_sample.restype = c_int
avutil.av_get_bytes_per_sample.argtypes = [c_int]
avutil.av_strerror.restype = c_int
avutil.av_strerror.argtypes = [c_int, c_char_p, c_size_t]

avutil.av_get_pix_fmt_name.restype = c_char_p
avutil.av_get_pix_fmt_name.argtypes = [c_int]

avutil.av_image_get_buffer_size.restype = c_int
avutil.av_image_get_buffer_size.argtypes = [c_int, c_int, c_int, c_int]

avutil.av_image_fill_arrays.restype = c_int
avutil.av_image_fill_arrays.argtypes = [POINTER(c_uint8) * 4, c_int * 4,
                                        POINTER(c_uint8), c_int, c_int, c_int, c_int]
avutil.av_dict_set.restype = c_int
avutil.av_dict_set.argtypes = [POINTER(POINTER(AVDictionary)),
                               c_char_p, c_char_p, c_int]
avutil.av_dict_free.argtypes = [POINTER(POINTER(AVDictionary))]
avutil.av_log_set_level.restype = c_int
avutil.av_log_set_level.argtypes = [c_uint]
avutil.av_malloc.restype = c_void_p
avutil.av_malloc.argtypes = [c_int]
avutil.av_freep.restype = c_void_p
avutil.av_freep.argtypes = [c_void_p]

__all__ = [
    'avutil',
    'AVMEDIA_TYPE_UNKNOWN',
    'AVMEDIA_TYPE_VIDEO',
    'AVMEDIA_TYPE_AUDIO',
    'AVMEDIA_TYPE_DATA',
    'AVMEDIA_TYPE_SUBTITLE',
    'AVMEDIA_TYPE_ATTACHMENT',
    'AVMEDIA_TYPE_NB',
    'AV_SAMPLE_FMT_U8',
    'AV_SAMPLE_FMT_S16',
    'AV_SAMPLE_FMT_S32',
    'AV_SAMPLE_FMT_FLT',
    'AV_SAMPLE_FORMAT_DOUBLE',
    'AV_SAMPLE_FMT_U8P',
    'AV_SAMPLE_FMT_S16P',
    'AV_SAMPLE_FMT_S32P',
    'AV_SAMPLE_FMT_FLTP',
    'AV_SAMPLE_FMT_DBLP',
    'AV_SAMPLE_FMT_S64',
    'AV_SAMPLE_FMT_S64P',
    'AV_NUM_DATA_POINTERS',
    'AV_PIX_FMT_RGB24',
    'AV_PIX_FMT_ARGB',
    'AV_PIX_FMT_RGBA',
    'AV_NOPTS_VALUE',
    'AV_TIME_BASE',
    'AV_TIME_BASE_Q',
    'AVFrame',
    'AVRational',
    'AVDictionary',
    'AVChannelLayout',
]
