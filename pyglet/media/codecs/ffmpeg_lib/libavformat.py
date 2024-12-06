"""Wrapper for include/libavformat/avformat.h
"""
from ctypes import c_int, c_int64
from ctypes import c_uint8, c_uint, c_double, c_ubyte, c_size_t, c_char, c_char_p
from ctypes import c_void_p, POINTER, CFUNCTYPE, Structure, Union

import pyglet.lib
from pyglet.util import debug_print
from . import compat
from . import libavcodec
from . import libavutil

_debug = debug_print('debug_media')

avformat = pyglet.lib.load_library(
    'avformat',
    win32=('avformat-61', 'avformat-60', 'avformat-59', 'avformat-58'),
    darwin=('avformat.61', 'avformat.60', 'avformat.59', 'avformat.58')
)

avformat.avformat_version.restype = c_int

avformat_version = avformat.avformat_version() >> 16

compat.set_version('avformat', avformat_version)

AVSEEK_FLAG_BACKWARD = 1  # ///< seek backward
AVSEEK_FLAG_BYTE = 2  # ///< seeking based on position in bytes
AVSEEK_FLAG_ANY = 4  # ///< seek to any frame, even non-keyframes
AVSEEK_FLAG_FRAME = 8  # ///< seeking based on frame number
AVSEEK_SIZE = 0x10000
AVFMT_FLAG_CUSTOM_IO = 0x0080

MAX_REORDER_DELAY = 16


class AVPacketList(Structure):
    pass


class AVInputFormat(Structure):
    _fields_ = [
        ('name', c_char_p)
    ]


class AVOutputFormat(Structure):
    pass


class AVIOContext(Structure):
    pass


class AVIndexEntry(Structure):
    pass


class AVStreamInfo(Structure):
    _fields_ = [
        ('last_dts', c_int64),
        ('duration_gcd', c_int64),
        ('duration_count', c_int),
        ('rfps_duration_sum', c_int64),
        ('duration_error', POINTER(c_double * 2 * (30 * 12 + 30 + 3 + 6))),
        ('codec_info_duration', c_int64),
        ('codec_info_duration_fields', c_int64),
        ('frame_delay_evidence', c_int),
        ('found_decoder', c_int),
        ('last_duration', c_int64),
        ('fps_first_dts', c_int64),
        ('fps_first_dts_idx', c_int),
        ('fps_last_dts', c_int64),
        ('fps_last_dts_idx', c_int),
    ]


class AVProbeData(Structure):
    _fields_ = [
        ('filename', c_char_p),
        ('buf', POINTER(c_ubyte)),
        ('buf_size', c_int),
        ('mime_type', c_char_p)
    ]


class FFFrac(Structure):
    pass


class AVStreamInternal(Structure):
    pass


class AVFrac(Structure):
    _fields_ = [
        ('val', c_int64),
        ('num', c_int64),
        ('den', c_int64),
    ]


AVCodecContext = libavcodec.AVCodecContext
AVPacketSideData = libavcodec.AVPacketSideData
AVPacket = libavcodec.AVPacket
AVCodecParserContext = libavcodec.AVCodecParserContext
AVCodecParameters = libavcodec.AVCodecParameters
AVRational = libavutil.AVRational
AVDictionary = libavutil.AVDictionary
AVFrame = libavutil.AVFrame
AVClass = libavutil.AVClass
AVCodec = libavcodec.AVCodec



class AVStream(Structure):
    pass

AVStream_Fields = [
        ('av_class', POINTER(AVClass)),
        ('index', c_int),
        ('id', c_int),
        ('codec', POINTER(AVCodecContext)),  # Deprecated. Removed in 59.
        ('priv_data', c_void_p),
        ('time_base', AVRational),
        ('start_time', c_int64),
        ('duration', c_int64),
        ('nb_frames', c_int64),
        ('disposition', c_int),
        ('discard', c_int),
        ('sample_aspect_ratio', AVRational),
        ('metadata', POINTER(AVDictionary)),
        ('avg_frame_rate', AVRational),
        ('attached_pic', AVPacket),
        ('side_data', POINTER(AVPacketSideData)),
        ('nb_side_data', c_int),
        ('event_flags', c_int),
        ('r_frame_rate', AVRational),
        ('recommended_encoder_configuration', c_char_p),  # Deprecated. Removed in 59.
        ('codecpar', POINTER(AVCodecParameters)),
        ('info', POINTER(AVStreamInfo)),  # Deprecated. Removed in 59.
        ('pts_wrap_bits', c_int),
    ]

compat.add_version_changes('avformat', 58, AVStream, AVStream_Fields, removals=('av_class',))

compat.add_version_changes('avformat', 59, AVStream, AVStream_Fields,
                           removals=('av_class', 'codec', 'recommended_encoder_configuration', 'info'))

for compat_ver in (60, 61):
    compat.add_version_changes('avformat', compat_ver, AVStream, AVStream_Fields,
                               removals=('codec', 'recommended_encoder_configuration', 'info'),
                               repositions=(compat.Reposition("codecpar", "id"),))


class AVProgram(Structure):
    pass


class AVChapter(Structure):
    pass


class AVFormatInternal(Structure):
    pass


class AVIOInterruptCB(Structure):
    _fields_ = [
        ('callback', CFUNCTYPE(c_int, c_void_p)),
        ('opaque', c_void_p)
    ]

class AVIAMFAudioElement(Structure):
    ...

class AVIAMFMixPresentation(Structure):
    ...

class _AvStreamGroupTileGridOffsets(Structure):
    _fields_ = [
        ('idx', c_uint),
        ('horizontal', c_int),
        ('vertical', c_int),
    ]

class AVStreamGroupTileGrid(Structure):
    _fields_ = [
        ('av_class', POINTER(AVClass)),
        ('nb_tiles', c_uint),
        ('coded_width', c_int),
        ('coded_height', c_int),
        ('offsets', POINTER(_AvStreamGroupTileGridOffsets)),
        ('background', c_uint8 * 4),
        ('horizontal_offset', c_int),
        ('vertical_offset', c_int),
        ('width', c_int),
        ('height', c_int),
    ]

class AVStreamGroupLCEVC(Structure):
    _fields_ = [
        ('av_class', POINTER(AVClass)),
        ('lcevc_index', c_int),
        ('width', c_int),
        ('height', c_int)
    ]

class _AVStreamGroupParams(Union):
    _fields_ = [
        ('iamf_audio_element', POINTER(AVIAMFAudioElement)),
        ('iamf_mix_presentation', POINTER(AVIAMFMixPresentation)),
        ('tile_grid', POINTER(AVStreamGroupTileGrid)),
        ('lcevc', POINTER(AVStreamGroupLCEVC))
    ]

class AVStreamGroup(Structure):
    _fields_ = [
        ('av_class', POINTER(AVClass)),
        ('priv_data', c_void_p),
        ('index', c_uint),
        ('id', c_int64),
        ('type', c_int),
        ('params', _AVStreamGroupParams),
        ('metadata', POINTER(AVDictionary)),
        ('nb_streams', c_uint),
        ('streams', POINTER(POINTER(AVStream))),
        ('disposition', c_int),
    ]


class AVFormatContext(Structure):
    pass


if avformat_version >= 61:
    AVFormatContext_Fields = [
        ('av_class', POINTER(AVClass)),
        ('iformat', POINTER(AVInputFormat)),
        ('oformat', POINTER(AVOutputFormat)),
        ('priv_data', c_void_p),
        ('pb', POINTER(AVIOContext)),
        ('ctx_flags', c_int),
        ('nb_streams', c_uint),
        ('streams', POINTER(POINTER(AVStream))),
        ('nb_stream_groups', c_uint),
        ('stream_groups', POINTER(POINTER(AVStreamGroup))),
        ('nb_chapters', c_uint),  # Moved after streams in 7.x
        ('chapters', POINTER(POINTER(AVChapter))),  # Moved after streams in 7.x
        ('url', c_char_p),
        ('start_time', c_int64),
        ('duration', c_int64),
        ('bit_rate', c_int64),
        ('packet_size', c_uint),
        ('max_delay', c_int),
        ('flags', c_int),
        ('probesize', c_int64),
        ('max_analyze_duration', c_int64),
        ('key', POINTER(c_uint8)),
        ('keylen', c_int),
        ('nb_programs', c_uint),
        ('programs', POINTER(POINTER(AVProgram))),
        ('video_codec_id', c_int),
        ('audio_codec_id', c_int),
        ('subtitle_codec_id', c_int),
        ('data_codec_id', c_int),
        ('metadata', POINTER(AVDictionary)),
        ('start_time_realtime', c_int64),
        ('fps_probe_size', c_int),
        ('error_recognition', c_int),
        ('interrupt_callback', AVIOInterruptCB),
        ('debug', c_int),
        ('max_streams', c_int),
        ('max_index_size', c_uint),
        ('max_picture_buffer', c_uint),
        ('max_interleave_delta', c_int64),
        ('max_ts_probe', c_int),
        ('max_chunk_duration', c_int),
        ('max_chunk_size', c_int),
        ('max_probe_packets', c_int),
        ('strict_std_compliance', c_int),
        ('event_flags', c_int),
        ('avoid_negative_ts', c_int),
        ('audio_preload', c_int),
        ('use_wallclock_as_timestamps', c_int),
        ('skip_estimate_duration_from_pts', c_int),  # Added in 59.
        ('avio_flags', c_int),
        ('duration_estimation_method', c_uint),
        ('skip_initial_bytes', c_int64),
        ('correct_ts_overflow', c_uint),
        ('seek2any', c_int),
        ('flush_packets', c_int),
        ('probe_score', c_int),
        ('format_probesize', c_int),
        ('codec_whitelist', c_char_p),
        ('format_whitelist', c_char_p),
        ('protocol_whitelist', c_char_p),
        ('protocol_blacklist', c_char_p),
        ('io_repositioned', c_int),
        ('video_codec', POINTER(AVCodec)),
        ('audio_codec', POINTER(AVCodec)),
        ('subtitle_codec', POINTER(AVCodec)),
        ('data_codec', POINTER(AVCodec)),
        ('metadata_header_padding', c_int),
        ('opaque', c_void_p),
        ('control_message_cb', CFUNCTYPE(c_int,
                                         POINTER(AVFormatContext), c_int, c_void_p,
                                         c_size_t)),
        ('output_ts_offset', c_int64),
        ('dump_separator', POINTER(c_uint8)),

        ('io_open', CFUNCTYPE(c_int,
                              POINTER(AVFormatContext),
                              POINTER(POINTER(AVIOContext)),
                              c_char_p, c_int,
                              POINTER(POINTER(AVDictionary)))),

        ('io_close2', CFUNCTYPE(c_int, POINTER(AVFormatContext), POINTER(AVIOContext)))  # Added in 59.
    ]

    compat.add_version_changes('avformat', 61, AVFormatContext, AVFormatContext_Fields, removals=None)


else:
    AVFormatContext_Fields = [
        ('av_class', POINTER(AVClass)),
        ('iformat', POINTER(AVInputFormat)),
        ('oformat', POINTER(AVOutputFormat)),
        ('priv_data', c_void_p),
        ('pb', POINTER(AVIOContext)),
        ('ctx_flags', c_int),
        ('nb_streams', c_uint),
        ('streams', POINTER(POINTER(AVStream))),
        ('filename', c_char * 1024),  # Deprecated. Removed in 59
        ('url', c_char_p),
        ('start_time', c_int64),
        ('duration', c_int64),
        ('bit_rate', c_int64),
        ('packet_size', c_uint),
        ('max_delay', c_int),
        ('flags', c_int),
        ('probesize', c_int64),
        ('max_analyze_duration', c_int64),
        ('key', POINTER(c_uint8)),
        ('keylen', c_int),
        ('nb_programs', c_uint),
        ('programs', POINTER(POINTER(AVProgram))),
        ('video_codec_id', c_int),
        ('audio_codec_id', c_int),
        ('subtitle_codec_id', c_int),
        ('max_index_size', c_uint),
        ('max_picture_buffer', c_uint),
        ('nb_chapters', c_uint),  # Moved after streams in 7.x
        ('chapters', POINTER(POINTER(AVChapter))),  # Moved after streams in 7.x
        ('metadata', POINTER(AVDictionary)),
        ('start_time_realtime', c_int64),
        ('fps_probe_size', c_int),
        ('error_recognition', c_int),
        ('interrupt_callback', AVIOInterruptCB),
        ('debug', c_int),
        ('max_interleave_delta', c_int64),
        ('strict_std_compliance', c_int),
        ('event_flags', c_int),
        ('max_ts_probe', c_int),
        ('avoid_negative_ts', c_int),
        ('ts_id', c_int),
        ('audio_preload', c_int),
        ('max_chunk_duration', c_int),
        ('max_chunk_size', c_int),
        ('use_wallclock_as_timestamps', c_int),
        ('avio_flags', c_int),
        ('duration_estimation_method', c_uint),
        ('skip_initial_bytes', c_int64),
        ('correct_ts_overflow', c_uint),
        ('seek2any', c_int),
        ('flush_packets', c_int),
        ('probe_score', c_int),
        ('format_probesize', c_int),
        ('codec_whitelist', c_char_p),
        ('format_whitelist', c_char_p),
        ('internal', POINTER(AVFormatInternal)),  # Deprecated. Removed in 59
        ('io_repositioned', c_int),
        ('video_codec', POINTER(AVCodec)),
        ('audio_codec', POINTER(AVCodec)),
        ('subtitle_codec', POINTER(AVCodec)),
        ('data_codec', POINTER(AVCodec)),
        ('metadata_header_padding', c_int),
        ('opaque', c_void_p),
        ('control_message_cb', CFUNCTYPE(c_int,
                                         POINTER(AVFormatContext), c_int, c_void_p,
                                         c_size_t)),
        ('output_ts_offset', c_int64),
        ('dump_separator', POINTER(c_uint8)),
        ('data_codec_id', c_int),
        ('protocol_whitelist', c_char_p),
        ('io_open', CFUNCTYPE(c_int,
                              POINTER(AVFormatContext),
                              POINTER(POINTER(AVIOContext)),
                              c_char_p, c_int,
                              POINTER(POINTER(AVDictionary)))),
        ('io_close', CFUNCTYPE(None,
                               POINTER(AVFormatContext), POINTER(AVIOContext))),
        ('protocol_blacklist', c_char_p),
        ('max_streams', c_int),
        ('skip_estimate_duration_from_pts', c_int),  # Added in 59.
        ('max_probe_packets', c_int), # Added in 59.
        ('io_close2', CFUNCTYPE(c_int, POINTER(AVFormatContext), POINTER(AVIOContext))) # Added in 59.
    ]

    compat.add_version_changes('avformat', 58, AVFormatContext, AVFormatContext_Fields,
                               removals=('skip_estimate_duration_from_pts', 'max_probe_packets', 'io_close2'))

    for compat_ver in (59, 60):
        compat.add_version_changes('avformat', compat_ver, AVFormatContext, AVFormatContext_Fields,
                                   removals=('filename', 'internal'))

avformat.av_find_input_format.restype = c_int
avformat.av_find_input_format.argtypes = [c_int]
avformat.avformat_open_input.restype = c_int
avformat.avformat_open_input.argtypes = [
    POINTER(POINTER(AVFormatContext)),
    c_char_p,
    POINTER(AVInputFormat),
    POINTER(POINTER(AVDictionary))]
avformat.avformat_find_stream_info.restype = c_int
avformat.avformat_find_stream_info.argtypes = [
    POINTER(AVFormatContext),
    POINTER(POINTER(AVDictionary))]
avformat.avformat_close_input.restype = None
avformat.avformat_close_input.argtypes = [
    POINTER(POINTER(AVFormatContext))]
avformat.av_read_frame.restype = c_int
avformat.av_read_frame.argtypes = [POINTER(AVFormatContext),
                                   POINTER(AVPacket)]
avformat.av_seek_frame.restype = c_int
avformat.av_seek_frame.argtypes = [POINTER(AVFormatContext),
                                   c_int, c_int64, c_int]
avformat.avformat_seek_file.restype = c_int
avformat.avformat_seek_file.argtypes = [POINTER(AVFormatContext),
                                        c_int, c_int64, c_int64, c_int64, c_int]
avformat.av_guess_frame_rate.restype = AVRational
avformat.av_guess_frame_rate.argtypes = [POINTER(AVFormatContext),
                                         POINTER(AVStream), POINTER(AVFrame)]

ffmpeg_read_func = CFUNCTYPE(c_int, c_void_p, POINTER(c_char), c_int)
ffmpeg_write_func = CFUNCTYPE(c_int, c_void_p, POINTER(c_char), c_int)
ffmpeg_seek_func = CFUNCTYPE(c_int64, c_void_p, c_int64, c_int)

avformat.avio_alloc_context.restype = POINTER(AVIOContext)
avformat.avio_alloc_context.argtypes = [c_char_p, c_int, c_int, c_void_p, ffmpeg_read_func, c_void_p, ffmpeg_seek_func]

avformat.avformat_alloc_context.restype = POINTER(AVFormatContext)
avformat.avformat_alloc_context.argtypes = []

avformat.avformat_free_context.restype = c_void_p
avformat.avformat_free_context.argtypes = [POINTER(AVFormatContext)]

__all__ = [
    'avformat',
    'AVSEEK_FLAG_BACKWARD',
    'AVSEEK_FLAG_BYTE',
    'AVSEEK_FLAG_ANY',
    'AVSEEK_FLAG_FRAME',
    'AVFormatContext',
    'AVCodecContext',
    'avformat_version',
]
