'''Wrapper for avcodec

Generated with:
../tools/wraptypes/wrap.py /usr/include/ffmpeg/avcodec.h -o lib_avcodec.py -lavcodec

.. Then hacked.  DO NOT REGENERATE.
'''

__docformat__ =  'restructuredtext'
__version__ = '$Id$'

import ctypes
from ctypes import *
from avcodec import get_library

_lib = get_library('avcodec')

_int_types = (c_int16, c_int32)
if hasattr(ctypes, 'c_int64'):
    # Some builds of ctypes apparently do not have c_int64
    # defined; it's a pretty good bet that these builds do not
    # have 64-bit pointers.
    _int_types += (ctypes.c_int64,)
for t in _int_types:
    if sizeof(t) == sizeof(c_size_t):
        c_ptrdiff_t = t

class c_void(Structure):
    # c_void_p is a buggy return type, converting to int, so
    # POINTER(None) == c_void_p is actually written as
    # POINTER(c_void), so it can be treated as a real pointer.
    _fields_ = [('dummy', c_int)]



FFMPEG_VERSION_INT = 1033 	# /usr/include/ffmpeg/avcodec.h:18
LIBAVCODEC_BUILD = 4743 	# /usr/include/ffmpeg/avcodec.h:20
LIBAVCODEC_VERSION_INT = 1033 	# /usr/include/ffmpeg/avcodec.h:22
AV_TIME_BASE = 1000000 	# /usr/include/ffmpeg/avcodec.h:30
CODEC_ID_MP3LAME = 0 	# /usr/include/ffmpeg/avcodec.h:176
AVCODEC_MAX_AUDIO_FRAME_SIZE = 131072 	# /usr/include/ffmpeg/avcodec.h:262
FF_INPUT_BUFFER_PADDING_SIZE = 8 	# /usr/include/ffmpeg/avcodec.h:271
FF_MIN_BUFFER_SIZE = 16384 	# /usr/include/ffmpeg/avcodec.h:277
class struct_RcOverride(Structure):
    __slots__ = [
        'start_frame',
        'end_frame',
        'qscale',
        'quality_factor',
    ]
struct_RcOverride._fields_ = [
    ('start_frame', c_int),
    ('end_frame', c_int),
    ('qscale', c_int),
    ('quality_factor', c_float),
]

RcOverride = struct_RcOverride 	# /usr/include/ffmpeg/avcodec.h:308
FF_MAX_B_FRAMES = 8 	# /usr/include/ffmpeg/avcodec.h:313
CODEC_FLAG_QSCALE = 2 	# /usr/include/ffmpeg/avcodec.h:320
CODEC_FLAG_4MV = 4 	# /usr/include/ffmpeg/avcodec.h:322
CODEC_FLAG_QPEL = 16 	# /usr/include/ffmpeg/avcodec.h:324
CODEC_FLAG_GMC = 32 	# /usr/include/ffmpeg/avcodec.h:326
CODEC_FLAG_MV0 = 64 	# /usr/include/ffmpeg/avcodec.h:328
CODEC_FLAG_PART = 128 	# /usr/include/ffmpeg/avcodec.h:330
CODEC_FLAG_INPUT_PRESERVED = 256 	# /usr/include/ffmpeg/avcodec.h:334
CODEC_FLAG_PASS1 = 512 	# /usr/include/ffmpeg/avcodec.h:335
CODEC_FLAG_PASS2 = 1024 	# /usr/include/ffmpeg/avcodec.h:337
CODEC_FLAG_EXTERN_HUFF = 4096 	# /usr/include/ffmpeg/avcodec.h:339
CODEC_FLAG_GRAY = 8192 	# /usr/include/ffmpeg/avcodec.h:341
CODEC_FLAG_EMU_EDGE = 16384 	# /usr/include/ffmpeg/avcodec.h:343
CODEC_FLAG_PSNR = 32768 	# /usr/include/ffmpeg/avcodec.h:345
CODEC_FLAG_TRUNCATED = 65536 	# /usr/include/ffmpeg/avcodec.h:347
CODEC_FLAG_NORMALIZE_AQP = 131072 	# /usr/include/ffmpeg/avcodec.h:349
CODEC_FLAG_INTERLACED_DCT = 262144 	# /usr/include/ffmpeg/avcodec.h:351
CODEC_FLAG_LOW_DELAY = 524288 	# /usr/include/ffmpeg/avcodec.h:353
CODEC_FLAG_ALT_SCAN = 1048576 	# /usr/include/ffmpeg/avcodec.h:355
CODEC_FLAG_TRELLIS_QUANT = 2097152 	# /usr/include/ffmpeg/avcodec.h:357
CODEC_FLAG_GLOBAL_HEADER = 4194304 	# /usr/include/ffmpeg/avcodec.h:359
CODEC_FLAG_BITEXACT = 8388608 	# /usr/include/ffmpeg/avcodec.h:361
CODEC_FLAG_H263P_AIC = 16777216 	# /usr/include/ffmpeg/avcodec.h:364
CODEC_FLAG_AC_PRED = 16777216 	# /usr/include/ffmpeg/avcodec.h:366
CODEC_FLAG_H263P_UMV = 33554432 	# /usr/include/ffmpeg/avcodec.h:368
CODEC_FLAG_CBP_RD = 67108864 	# /usr/include/ffmpeg/avcodec.h:370
CODEC_FLAG_QP_RD = 134217728 	# /usr/include/ffmpeg/avcodec.h:372
CODEC_FLAG_H263P_AIV = 8 	# /usr/include/ffmpeg/avcodec.h:374
CODEC_FLAG_OBMC = 1 	# /usr/include/ffmpeg/avcodec.h:376
CODEC_FLAG_LOOP_FILTER = 2048 	# /usr/include/ffmpeg/avcodec.h:378
CODEC_FLAG_H263P_SLICE_STRUCT = 268435456 	# /usr/include/ffmpeg/avcodec.h:380
CODEC_FLAG_INTERLACED_ME = 536870912 	# /usr/include/ffmpeg/avcodec.h:381
CODEC_FLAG_SVCD_SCAN_OFFSET = 1073741824 	# /usr/include/ffmpeg/avcodec.h:383
CODEC_FLAG_CLOSED_GOP = 2147483648 	# /usr/include/ffmpeg/avcodec.h:385
CODEC_FLAG2_FAST = 1 	# /usr/include/ffmpeg/avcodec.h:386
CODEC_FLAG2_STRICT_GOP = 2 	# /usr/include/ffmpeg/avcodec.h:388
CODEC_FLAG2_NO_OUTPUT = 4 	# /usr/include/ffmpeg/avcodec.h:390
CODEC_CAP_DRAW_HORIZ_BAND = 1 	# /usr/include/ffmpeg/avcodec.h:400
CODEC_CAP_DR1 = 2 	# /usr/include/ffmpeg/avcodec.h:406
CODEC_CAP_PARSE_ONLY = 4 	# /usr/include/ffmpeg/avcodec.h:409
CODEC_CAP_TRUNCATED = 8 	# /usr/include/ffmpeg/avcodec.h:410
CODEC_CAP_HWACCEL = 16 	# /usr/include/ffmpeg/avcodec.h:412
CODEC_CAP_DELAY = 32 	# /usr/include/ffmpeg/avcodec.h:417
MB_TYPE_INTRA4x4 = 1 	# /usr/include/ffmpeg/avcodec.h:421
MB_TYPE_INTRA16x16 = 2 	# /usr/include/ffmpeg/avcodec.h:422
MB_TYPE_INTRA_PCM = 4 	# /usr/include/ffmpeg/avcodec.h:424
MB_TYPE_16x16 = 8 	# /usr/include/ffmpeg/avcodec.h:426
MB_TYPE_16x8 = 16 	# /usr/include/ffmpeg/avcodec.h:427
MB_TYPE_8x16 = 32 	# /usr/include/ffmpeg/avcodec.h:428
MB_TYPE_8x8 = 64 	# /usr/include/ffmpeg/avcodec.h:429
MB_TYPE_INTERLACED = 128 	# /usr/include/ffmpeg/avcodec.h:430
MB_TYPE_DIRECT2 = 256 	# /usr/include/ffmpeg/avcodec.h:431
MB_TYPE_ACPRED = 512 	# /usr/include/ffmpeg/avcodec.h:433
MB_TYPE_GMC = 1024 	# /usr/include/ffmpeg/avcodec.h:434
MB_TYPE_SKIP = 2048 	# /usr/include/ffmpeg/avcodec.h:435
MB_TYPE_P0L0 = 4096 	# /usr/include/ffmpeg/avcodec.h:436
MB_TYPE_P1L0 = 8192 	# /usr/include/ffmpeg/avcodec.h:437
MB_TYPE_P0L1 = 16384 	# /usr/include/ffmpeg/avcodec.h:438
MB_TYPE_P1L1 = 32768 	# /usr/include/ffmpeg/avcodec.h:439
MB_TYPE_L0 = 12288 	# /usr/include/ffmpeg/avcodec.h:440
MB_TYPE_L1 = 49152 	# /usr/include/ffmpeg/avcodec.h:441
MB_TYPE_L0L1 = 61440 	# /usr/include/ffmpeg/avcodec.h:442
MB_TYPE_QUANT = 65536 	# /usr/include/ffmpeg/avcodec.h:443
MB_TYPE_CBP = 131072 	# /usr/include/ffmpeg/avcodec.h:444
class struct_AVPanScan(Structure):
    __slots__ = [
        'id',
        'width',
        'height',
        'position',
    ]
struct_AVPanScan._fields_ = [
    ('id', c_int),
    ('width', c_int),
    ('height', c_int),
    ('position', (c_int16 * 2) * 3),
]

AVPanScan = struct_AVPanScan 	# /usr/include/ffmpeg/avcodec.h:474
FF_QSCALE_TYPE_MPEG1 = 0 	# /usr/include/ffmpeg/avcodec.h:684
FF_QSCALE_TYPE_MPEG2 = 1 	# /usr/include/ffmpeg/avcodec.h:685
FF_BUFFER_TYPE_INTERNAL = 1 	# /usr/include/ffmpeg/avcodec.h:687
FF_BUFFER_TYPE_USER = 2 	# /usr/include/ffmpeg/avcodec.h:688
FF_BUFFER_TYPE_SHARED = 4 	# /usr/include/ffmpeg/avcodec.h:690
FF_BUFFER_TYPE_COPY = 8 	# /usr/include/ffmpeg/avcodec.h:692
FF_I_TYPE = 1 	# /usr/include/ffmpeg/avcodec.h:696
FF_P_TYPE = 2 	# /usr/include/ffmpeg/avcodec.h:698
FF_B_TYPE = 3 	# /usr/include/ffmpeg/avcodec.h:700
FF_S_TYPE = 4 	# /usr/include/ffmpeg/avcodec.h:702
FF_SI_TYPE = 5 	# /usr/include/ffmpeg/avcodec.h:704
FF_SP_TYPE = 6 	# /usr/include/ffmpeg/avcodec.h:705
FF_BUFFER_HINTS_VALID = 1 	# /usr/include/ffmpeg/avcodec.h:707
FF_BUFFER_HINTS_READABLE = 2 	# /usr/include/ffmpeg/avcodec.h:709
FF_BUFFER_HINTS_PRESERVE = 4 	# /usr/include/ffmpeg/avcodec.h:711
FF_BUFFER_HINTS_REUSABLE = 8 	# /usr/include/ffmpeg/avcodec.h:713
class struct_AVFrame(Structure):
    __slots__ = [
        'data',
        'linesize',
        'base',
        'key_frame',
        'pict_type',
        'pts',
        'coded_picture_number',
        'display_picture_number',
        'quality',
        'age',
        'reference',
        'qscale_table',
        'qstride',
        'mbskip_table',
        'motion_val',
        'mb_type',
        'motion_subsample_log2',
        'opaque',
        'error',
        'type',
        'repeat_pict',
        'qscale_type',
        'interlaced_frame',
        'top_field_first',
        'pan_scan',
        'palette_has_changed',
        'buffer_hints',
        'dct_coeff',
        'ref_index',
    ]
struct_AVFrame._fields_ = [
    ('data', POINTER(c_uint8) * 4),
    ('linesize', c_int * 4),
    ('base', POINTER(c_uint8) * 4),
    ('key_frame', c_int),
    ('pict_type', c_int),
    ('pts', c_int64),
    ('coded_picture_number', c_int),
    ('display_picture_number', c_int),
    ('quality', c_int),
    ('age', c_int),
    ('reference', c_int),
    ('qscale_table', POINTER(c_int8)),
    ('qstride', c_int),
    ('mbskip_table', POINTER(c_uint8)),
    ('motion_val', POINTER(c_int16 * 2) * 2),
    ('mb_type', POINTER(c_uint32)),
    ('motion_subsample_log2', c_uint8),
    ('opaque', POINTER(None)),
    ('error', c_uint64 * 4),
    ('type', c_int),
    ('repeat_pict', c_int),
    ('qscale_type', c_int),
    ('interlaced_frame', c_int),
    ('top_field_first', c_int),
    ('pan_scan', POINTER(AVPanScan)),
    ('palette_has_changed', c_int),
    ('buffer_hints', c_int),
    ('dct_coeff', POINTER(c_short)),
    ('ref_index', POINTER(c_int8) * 2),
]

AVFrame = struct_AVFrame 	# /usr/include/ffmpeg/avcodec.h:721
DEFAULT_FRAME_RATE_BASE = 1001000 	# /usr/include/ffmpeg/avcodec.h:723
class struct_AVCLASS(Structure):
    __slots__ = [
    ]
struct_AVCLASS._fields_ = [
    ('_opaque_struct', c_int)
]

class struct_AVCLASS(Structure):
    __slots__ = [
    ]
struct_AVCLASS._fields_ = [
    ('_opaque_struct', c_int)
]

AVClass = struct_AVCLASS 	# /usr/include/ffmpeg/avcodec.h:728
FF_ASPECT_EXTENDED = 15 	# /usr/include/ffmpeg/avcodec.h:814
FF_BUG_AUTODETECT = 1 	# /usr/include/ffmpeg/avcodec.h:1001
FF_BUG_OLD_MSMPEG4 = 2 	# /usr/include/ffmpeg/avcodec.h:1003
FF_BUG_XVID_ILACE = 4 	# /usr/include/ffmpeg/avcodec.h:1004
FF_BUG_UMP4 = 8 	# /usr/include/ffmpeg/avcodec.h:1005
FF_BUG_NO_PADDING = 16 	# /usr/include/ffmpeg/avcodec.h:1006
FF_BUG_AMV = 32 	# /usr/include/ffmpeg/avcodec.h:1007
FF_BUG_AC_VLC = 0 	# /usr/include/ffmpeg/avcodec.h:1008
FF_BUG_QPEL_CHROMA = 64 	# /usr/include/ffmpeg/avcodec.h:1010
FF_BUG_STD_QPEL = 128 	# /usr/include/ffmpeg/avcodec.h:1011
FF_BUG_QPEL_CHROMA2 = 256 	# /usr/include/ffmpeg/avcodec.h:1012
FF_BUG_DIRECT_BLOCKSIZE = 512 	# /usr/include/ffmpeg/avcodec.h:1013
FF_BUG_EDGE = 1024 	# /usr/include/ffmpeg/avcodec.h:1014
FF_BUG_HPEL_CHROMA = 2048 	# /usr/include/ffmpeg/avcodec.h:1015
FF_BUG_DC_CLIP = 4096 	# /usr/include/ffmpeg/avcodec.h:1016
FF_ER_CAREFULL = 1 	# /usr/include/ffmpeg/avcodec.h:1057
FF_ER_COMPLIANT = 2 	# /usr/include/ffmpeg/avcodec.h:1058
FF_ER_AGGRESSIVE = 3 	# /usr/include/ffmpeg/avcodec.h:1059
FF_ER_VERY_AGGRESSIVE = 4 	# /usr/include/ffmpeg/avcodec.h:1060
FF_DCT_AUTO = 0 	# /usr/include/ffmpeg/avcodec.h:1194
FF_DCT_FASTINT = 1 	# /usr/include/ffmpeg/avcodec.h:1195
FF_DCT_INT = 2 	# /usr/include/ffmpeg/avcodec.h:1196
FF_DCT_MMX = 3 	# /usr/include/ffmpeg/avcodec.h:1197
FF_DCT_MLIB = 4 	# /usr/include/ffmpeg/avcodec.h:1198
FF_DCT_ALTIVEC = 5 	# /usr/include/ffmpeg/avcodec.h:1199
FF_DCT_FAAN = 6 	# /usr/include/ffmpeg/avcodec.h:1200
FF_IDCT_AUTO = 0 	# /usr/include/ffmpeg/avcodec.h:1247
FF_IDCT_INT = 1 	# /usr/include/ffmpeg/avcodec.h:1248
FF_IDCT_SIMPLE = 2 	# /usr/include/ffmpeg/avcodec.h:1249
FF_IDCT_SIMPLEMMX = 3 	# /usr/include/ffmpeg/avcodec.h:1250
FF_IDCT_LIBMPEG2MMX = 4 	# /usr/include/ffmpeg/avcodec.h:1251
FF_IDCT_PS2 = 5 	# /usr/include/ffmpeg/avcodec.h:1252
FF_IDCT_MLIB = 6 	# /usr/include/ffmpeg/avcodec.h:1253
FF_IDCT_ARM = 7 	# /usr/include/ffmpeg/avcodec.h:1254
FF_IDCT_ALTIVEC = 8 	# /usr/include/ffmpeg/avcodec.h:1255
FF_IDCT_SH4 = 9 	# /usr/include/ffmpeg/avcodec.h:1256
FF_IDCT_SIMPLEARM = 10 	# /usr/include/ffmpeg/avcodec.h:1257
FF_IDCT_H264 = 11 	# /usr/include/ffmpeg/avcodec.h:1258
FF_EC_GUESS_MVS = 1 	# /usr/include/ffmpeg/avcodec.h:1279
FF_EC_DEBLOCK = 2 	# /usr/include/ffmpeg/avcodec.h:1280
FF_MM_FORCE = 2147483648 	# /usr/include/ffmpeg/avcodec.h:1291
FF_PRED_LEFT = 0 	# /usr/include/ffmpeg/avcodec.h:1315
FF_PRED_PLANE = 1 	# /usr/include/ffmpeg/avcodec.h:1316
FF_PRED_MEDIAN = 2 	# /usr/include/ffmpeg/avcodec.h:1317
FF_DEBUG_PICT_INFO = 1 	# /usr/include/ffmpeg/avcodec.h:1340
FF_DEBUG_RC = 2 	# /usr/include/ffmpeg/avcodec.h:1341
FF_DEBUG_BITSTREAM = 4 	# /usr/include/ffmpeg/avcodec.h:1342
FF_DEBUG_MB_TYPE = 8 	# /usr/include/ffmpeg/avcodec.h:1343
FF_DEBUG_QP = 16 	# /usr/include/ffmpeg/avcodec.h:1344
FF_DEBUG_MV = 32 	# /usr/include/ffmpeg/avcodec.h:1345
FF_DEBUG_DCT_COEFF = 64 	# /usr/include/ffmpeg/avcodec.h:1346
FF_DEBUG_SKIP = 128 	# /usr/include/ffmpeg/avcodec.h:1347
FF_DEBUG_STARTCODE = 256 	# /usr/include/ffmpeg/avcodec.h:1348
FF_DEBUG_PTS = 512 	# /usr/include/ffmpeg/avcodec.h:1349
FF_DEBUG_ER = 1024 	# /usr/include/ffmpeg/avcodec.h:1350
FF_DEBUG_MMCO = 2048 	# /usr/include/ffmpeg/avcodec.h:1351
FF_DEBUG_BUGS = 4096 	# /usr/include/ffmpeg/avcodec.h:1352
FF_DEBUG_VIS_QP = 8192 	# /usr/include/ffmpeg/avcodec.h:1353
FF_DEBUG_VIS_MB_TYPE = 16384 	# /usr/include/ffmpeg/avcodec.h:1354
FF_DEBUG_VIS_MV_P_FOR = 1 	# /usr/include/ffmpeg/avcodec.h:1362
FF_DEBUG_VIS_MV_B_FOR = 2 	# /usr/include/ffmpeg/avcodec.h:1364
FF_DEBUG_VIS_MV_B_BACK = 4 	# /usr/include/ffmpeg/avcodec.h:1366
FF_CMP_SAD = 0 	# /usr/include/ffmpeg/avcodec.h:1414
FF_CMP_SSE = 1 	# /usr/include/ffmpeg/avcodec.h:1415
FF_CMP_SATD = 2 	# /usr/include/ffmpeg/avcodec.h:1416
FF_CMP_DCT = 3 	# /usr/include/ffmpeg/avcodec.h:1417
FF_CMP_PSNR = 4 	# /usr/include/ffmpeg/avcodec.h:1418
FF_CMP_BIT = 5 	# /usr/include/ffmpeg/avcodec.h:1419
FF_CMP_RD = 6 	# /usr/include/ffmpeg/avcodec.h:1420
FF_CMP_ZERO = 7 	# /usr/include/ffmpeg/avcodec.h:1421
FF_CMP_VSAD = 8 	# /usr/include/ffmpeg/avcodec.h:1422
FF_CMP_VSSE = 9 	# /usr/include/ffmpeg/avcodec.h:1423
FF_CMP_NSSE = 10 	# /usr/include/ffmpeg/avcodec.h:1424
FF_CMP_W53 = 11 	# /usr/include/ffmpeg/avcodec.h:1425
FF_CMP_W97 = 12 	# /usr/include/ffmpeg/avcodec.h:1426
FF_CMP_DCTMAX = 13 	# /usr/include/ffmpeg/avcodec.h:1427
FF_CMP_CHROMA = 256 	# /usr/include/ffmpeg/avcodec.h:1428
FF_DTG_AFD_SAME = 8 	# /usr/include/ffmpeg/avcodec.h:1492
FF_DTG_AFD_4_3 = 9 	# /usr/include/ffmpeg/avcodec.h:1493
FF_DTG_AFD_16_9 = 10 	# /usr/include/ffmpeg/avcodec.h:1494
FF_DTG_AFD_14_9 = 11 	# /usr/include/ffmpeg/avcodec.h:1495
FF_DTG_AFD_4_3_SP_14_9 = 13 	# /usr/include/ffmpeg/avcodec.h:1496
FF_DTG_AFD_16_9_SP_14_9 = 14 	# /usr/include/ffmpeg/avcodec.h:1497
FF_DTG_AFD_SP_4_3 = 15 	# /usr/include/ffmpeg/avcodec.h:1498
FF_DEFAULT_QUANT_BIAS = 999999 	# /usr/include/ffmpeg/avcodec.h:1524
FF_LAMBDA_SHIFT = 7 	# /usr/include/ffmpeg/avcodec.h:1553
FF_LAMBDA_SCALE = 128 	# /usr/include/ffmpeg/avcodec.h:1554
FF_QP2LAMBDA = 118 	# /usr/include/ffmpeg/avcodec.h:1555
FF_LAMBDA_MAX = 32767 	# /usr/include/ffmpeg/avcodec.h:1557
FF_QUALITY_SCALE = 128 	# /usr/include/ffmpeg/avcodec.h:1559
FF_CODER_TYPE_VLC = 0 	# /usr/include/ffmpeg/avcodec.h:1569
FF_CODER_TYPE_AC = 1 	# /usr/include/ffmpeg/avcodec.h:1570
SLICE_FLAG_CODED_ORDER = 1 	# /usr/include/ffmpeg/avcodec.h:1591
SLICE_FLAG_ALLOW_FIELD = 2 	# /usr/include/ffmpeg/avcodec.h:1593
SLICE_FLAG_ALLOW_PLANE = 4 	# /usr/include/ffmpeg/avcodec.h:1595
FF_MB_DECISION_SIMPLE = 0 	# /usr/include/ffmpeg/avcodec.h:1611
FF_MB_DECISION_BITS = 1 	# /usr/include/ffmpeg/avcodec.h:1613
FF_MB_DECISION_RD = 2 	# /usr/include/ffmpeg/avcodec.h:1615
FF_AA_AUTO = 0 	# /usr/include/ffmpeg/avcodec.h:1721
FF_AA_FASTINT = 1 	# /usr/include/ffmpeg/avcodec.h:1722
FF_AA_INT = 2 	# /usr/include/ffmpeg/avcodec.h:1724
FF_AA_FLOAT = 3 	# /usr/include/ffmpeg/avcodec.h:1725
FF_PROFILE_UNKNOWN = -99 	# /usr/include/ffmpeg/avcodec.h:1809
FF_LEVEL_UNKNOWN = -99 	# /usr/include/ffmpeg/avcodec.h:1817
class struct_AVCodecContext(Structure):
    __slots__ = [
        'av_class',
        'bit_rate',
        'bit_rate_tolerance',
        'flags',
        'sub_id',
        'me_method',
        'extradata',
        'extradata_size',
        'frame_rate',
        'width',
        'height',
        'gop_size',
        'pix_fmt',
        'rate_emu',
        'draw_horiz_band',
        'sample_rate',
        'channels',
        'sample_fmt',
        'frame_size',
        'frame_number',
        'real_pict_num',
        'delay',
        'qcompress',
        'qblur',
        'qmin',
        'qmax',
        'max_qdiff',
        'max_b_frames',
        'b_quant_factor',
        'rc_strategy',
        'b_frame_strategy',
        'hurry_up',
        'codec',
        'priv_data',
        'rtp_mode',
        'rtp_payload_size',
        'rtp_callback',
        'mv_bits',
        'header_bits',
        'i_tex_bits',
        'p_tex_bits',
        'i_count',
        'p_count',
        'skip_count',
        'misc_bits',
        'frame_bits',
        'opaque',
        'codec_name',
        'codec_type',
        'codec_id',
        'codec_tag',
        'workaround_bugs',
        'luma_elim_threshold',
        'chroma_elim_threshold',
        'strict_std_compliance',
        'b_quant_offset',
        'error_resilience',
        'get_buffer',
        'release_buffer',
        'has_b_frames',
        'block_align',
        'parse_only',
        'mpeg_quant',
        'stats_out',
        'stats_in',
        'rc_qsquish',
        'rc_qmod_amp',
        'rc_qmod_freq',
        'rc_override',
        'rc_override_count',
        'rc_eq',
        'rc_max_rate',
        'rc_min_rate',
        'rc_buffer_size',
        'rc_buffer_aggressivity',
        'i_quant_factor',
        'i_quant_offset',
        'rc_initial_cplx',
        'dct_algo',
        'lumi_masking',
        'temporal_cplx_masking',
        'spatial_cplx_masking',
        'p_masking',
        'dark_masking',
        'unused',
        'idct_algo',
        'slice_count',
        'slice_offset',
        'error_concealment',
        'dsp_mask',
        'bits_per_sample',
        'prediction_method',
        'sample_aspect_ratio',
        'coded_frame',
        'debug',
        'debug_mv',
        'error',
        'mb_qmin',
        'mb_qmax',
        'me_cmp',
        'me_sub_cmp',
        'mb_cmp',
        'ildct_cmp',
        'dia_size',
        'last_predictor_count',
        'pre_me',
        'me_pre_cmp',
        'pre_dia_size',
        'me_subpel_quality',
        'get_format',
        'dtg_active_format',
        'me_range',
        'frame_rate_base',
        'intra_quant_bias',
        'inter_quant_bias',
        'color_table_id',
        'internal_buffer_count',
        'internal_buffer',
        'global_quality',
        'coder_type',
        'context_model',
        'slice_flags',
        'xvmc_acceleration',
        'mb_decision',
        'intra_matrix',
        'inter_matrix',
        'stream_codec_tag',
        'scenechange_threshold',
        'lmin',
        'lmax',
        'palctrl',
        'noise_reduction',
        'reget_buffer',
        'rc_initial_buffer_occupancy',
        'inter_threshold',
        'flags2',
        'error_rate',
        'antialias_algo',
        'quantizer_noise_shaping',
        'thread_count',
        'execute',
        'thread_opaque',
        'me_threshold',
        'mb_threshold',
        'intra_dc_precision',
        'nsse_weight',
        'skip_top',
        'skip_bottom',
        'profile',
        'level',
        'lowres',
        'coded_width',
        'coded_height',
        'frame_skip_threshold',
        'frame_skip_factor',
        'frame_skip_exp',
        'frame_skip_cmp',
        'border_masking',
        'mb_lmin',
        'mb_lmax',
    ]
enum_PixelFormat = c_int
enum_SampleFormat = c_int
class struct_AVCodec(Structure):
    __slots__ = [
    ]
struct_AVCodec._fields_ = [
    ('_opaque_struct', c_int)
]

enum_CodecType = c_int
enum_CodecID = c_int
class struct_AVRational(Structure):
    __slots__ = [
        'num',
        'den',
    ]
struct_AVRational._fields_ = [
    ('num', c_int),
    ('den', c_int),
]

AVRational = struct_AVRational 	# /usr/include/ffmpeg/rational.h:38
class struct_AVPaletteControl(Structure):
    __slots__ = [
    ]
struct_AVPaletteControl._fields_ = [
    ('_opaque_struct', c_int)
]

struct_AVCodecContext._fields_ = [
    ('av_class', POINTER(AVClass)),
    ('bit_rate', c_int),
    ('bit_rate_tolerance', c_int),
    ('flags', c_int),
    ('sub_id', c_int),
    ('me_method', c_int),
    ('extradata', POINTER(None)),
    ('extradata_size', c_int),
    ('frame_rate', c_int),
    ('width', c_int),
    ('height', c_int),
    ('gop_size', c_int),
    ('pix_fmt', enum_PixelFormat),
    ('rate_emu', c_int),
    ('draw_horiz_band', POINTER(CFUNCTYPE(None, POINTER(struct_AVCodecContext), POINTER(AVFrame), c_int * 4, c_int, c_int, c_int))),
    ('sample_rate', c_int),
    ('channels', c_int),
    ('sample_fmt', enum_SampleFormat),
    ('frame_size', c_int),
    ('frame_number', c_int),
    ('real_pict_num', c_int),
    ('delay', c_int),
    ('qcompress', c_float),
    ('qblur', c_float),
    ('qmin', c_int),
    ('qmax', c_int),
    ('max_qdiff', c_int),
    ('max_b_frames', c_int),
    ('b_quant_factor', c_float),
    ('rc_strategy', c_int),
    ('b_frame_strategy', c_int),
    ('hurry_up', c_int),
    ('codec', POINTER(struct_AVCodec)),
    ('priv_data', POINTER(None)),
    ('rtp_mode', c_int),
    ('rtp_payload_size', c_int),
    ('rtp_callback', POINTER(CFUNCTYPE(None, POINTER(struct_AVCodecContext), POINTER(None), c_int, c_int))),
    ('mv_bits', c_int),
    ('header_bits', c_int),
    ('i_tex_bits', c_int),
    ('p_tex_bits', c_int),
    ('i_count', c_int),
    ('p_count', c_int),
    ('skip_count', c_int),
    ('misc_bits', c_int),
    ('frame_bits', c_int),
    ('opaque', POINTER(None)),
    ('codec_name', c_char * 32),
    ('codec_type', enum_CodecType),
    ('codec_id', enum_CodecID),
    ('codec_tag', c_uint),
    ('workaround_bugs', c_int),
    ('luma_elim_threshold', c_int),
    ('chroma_elim_threshold', c_int),
    ('strict_std_compliance', c_int),
    ('b_quant_offset', c_float),
    ('error_resilience', c_int),
    ('get_buffer', POINTER(CFUNCTYPE(c_int, POINTER(struct_AVCodecContext), POINTER(AVFrame)))),
    ('release_buffer', POINTER(CFUNCTYPE(None, POINTER(struct_AVCodecContext), POINTER(AVFrame)))),
    ('has_b_frames', c_int),
    ('block_align', c_int),
    ('parse_only', c_int),
    ('mpeg_quant', c_int),
    ('stats_out', c_char_p),
    ('stats_in', c_char_p),
    ('rc_qsquish', c_float),
    ('rc_qmod_amp', c_float),
    ('rc_qmod_freq', c_int),
    ('rc_override', POINTER(RcOverride)),
    ('rc_override_count', c_int),
    ('rc_eq', c_char_p),
    ('rc_max_rate', c_int),
    ('rc_min_rate', c_int),
    ('rc_buffer_size', c_int),
    ('rc_buffer_aggressivity', c_float),
    ('i_quant_factor', c_float),
    ('i_quant_offset', c_float),
    ('rc_initial_cplx', c_float),
    ('dct_algo', c_int),
    ('lumi_masking', c_float),
    ('temporal_cplx_masking', c_float),
    ('spatial_cplx_masking', c_float),
    ('p_masking', c_float),
    ('dark_masking', c_float),
    ('unused', c_int),
    ('idct_algo', c_int),
    ('slice_count', c_int),
    ('slice_offset', POINTER(c_int)),
    ('error_concealment', c_int),
    ('dsp_mask', c_uint),
    ('bits_per_sample', c_int),
    ('prediction_method', c_int),
    ('sample_aspect_ratio', AVRational),
    ('coded_frame', POINTER(AVFrame)),
    ('debug', c_int),
    ('debug_mv', c_int),
    ('error', c_uint64 * 4),
    ('mb_qmin', c_int),
    ('mb_qmax', c_int),
    ('me_cmp', c_int),
    ('me_sub_cmp', c_int),
    ('mb_cmp', c_int),
    ('ildct_cmp', c_int),
    ('dia_size', c_int),
    ('last_predictor_count', c_int),
    ('pre_me', c_int),
    ('me_pre_cmp', c_int),
    ('pre_dia_size', c_int),
    ('me_subpel_quality', c_int),
    ('get_format', POINTER(CFUNCTYPE(enum_PixelFormat, POINTER(struct_AVCodecContext), POINTER(enum_PixelFormat)))),
    ('dtg_active_format', c_int),
    ('me_range', c_int),
    ('frame_rate_base', c_int),
    ('intra_quant_bias', c_int),
    ('inter_quant_bias', c_int),
    ('color_table_id', c_int),
    ('internal_buffer_count', c_int),
    ('internal_buffer', POINTER(None)),
    ('global_quality', c_int),
    ('coder_type', c_int),
    ('context_model', c_int),
    ('slice_flags', c_int),
    ('xvmc_acceleration', c_int),
    ('mb_decision', c_int),
    ('intra_matrix', POINTER(c_uint16)),
    ('inter_matrix', POINTER(c_uint16)),
    ('stream_codec_tag', c_uint),
    ('scenechange_threshold', c_int),
    ('lmin', c_int),
    ('lmax', c_int),
    ('palctrl', POINTER(struct_AVPaletteControl)),
    ('noise_reduction', c_int),
    ('reget_buffer', POINTER(CFUNCTYPE(c_int, POINTER(struct_AVCodecContext), POINTER(AVFrame)))),
    ('rc_initial_buffer_occupancy', c_int),
    ('inter_threshold', c_int),
    ('flags2', c_int),
    ('error_rate', c_int),
    ('antialias_algo', c_int),
    ('quantizer_noise_shaping', c_int),
    ('thread_count', c_int),
    ('execute', POINTER(CFUNCTYPE(c_int, POINTER(struct_AVCodecContext), CFUNCTYPE(c_int, POINTER(struct_AVCodecContext), POINTER(None)), POINTER(POINTER(None)), POINTER(c_int), c_int))),
    ('thread_opaque', POINTER(None)),
    ('me_threshold', c_int),
    ('mb_threshold', c_int),
    ('intra_dc_precision', c_int),
    ('nsse_weight', c_int),
    ('skip_top', c_int),
    ('skip_bottom', c_int),
    ('profile', c_int),
    ('level', c_int),
    ('lowres', c_int),
    ('coded_width', c_int),
    ('coded_height', c_int),
    ('frame_skip_threshold', c_int),
    ('frame_skip_factor', c_int),
    ('frame_skip_exp', c_int),
    ('frame_skip_cmp', c_int),
    ('border_masking', c_float),
    ('mb_lmin', c_int),
    ('mb_lmax', c_int),
]

AVCodecContext = struct_AVCodecContext 	# /usr/include/ffmpeg/avcodec.h:1883
FF_OPT_TYPE_BOOL = 1 	# /usr/include/ffmpeg/avcodec.h:1899
FF_OPT_TYPE_DOUBLE = 2 	# /usr/include/ffmpeg/avcodec.h:1901
FF_OPT_TYPE_INT = 3 	# /usr/include/ffmpeg/avcodec.h:1903
FF_OPT_TYPE_STRING = 4 	# /usr/include/ffmpeg/avcodec.h:1905
FF_OPT_TYPE_MASK = 31 	# /usr/include/ffmpeg/avcodec.h:1907
FF_OPT_TYPE_FLAG = 65 	# /usr/include/ffmpeg/avcodec.h:1911
FF_OPT_TYPE_RCOVERRIDE = 132 	# /usr/include/ffmpeg/avcodec.h:1912
FF_OPT_MAX_DEPTH = 10 	# /usr/include/ffmpeg/avcodec.h:1925
class struct_AVOption(Structure):
    __slots__ = [
        'name',
        'help',
        'offset',
        'type',
        'min',
        'max',
        'defval',
        'defstr',
    ]
struct_AVOption._fields_ = [
    ('name', c_char_p),
    ('help', c_char_p),
    ('offset', c_int),
    ('type', c_int),
    ('min', c_double),
    ('max', c_double),
    ('defval', c_double),
    ('defstr', c_char_p),
]

AVOption = struct_AVOption 	# /usr/include/ffmpeg/avcodec.h:1926
# /usr/include/ffmpeg/avcodec.h:1941
avoption_parse = _lib.avoption_parse
avoption_parse.restype = c_int
avoption_parse.argtypes = [POINTER(None), POINTER(AVOption), c_char_p]

class struct_AVCodec(Structure):
    __slots__ = [
        'name',
        'type',
        'id',
        'priv_data_size',
        'init',
        'encode',
        'close',
        'decode',
        'capabilities',
        'options',
        'next',
        'flush',
        'supported_framerates',
        'pix_fmts',
    ]
struct_AVCodec._fields_ = [
    ('name', c_char_p),
    ('type', enum_CodecType),
    ('id', enum_CodecID),
    ('priv_data_size', c_int),
    ('init', POINTER(CFUNCTYPE(c_int, POINTER(AVCodecContext)))),
    ('encode', POINTER(CFUNCTYPE(c_int, POINTER(AVCodecContext), POINTER(c_uint8), c_int, POINTER(None)))),
    ('close', POINTER(CFUNCTYPE(c_int, POINTER(AVCodecContext)))),
    ('decode', POINTER(CFUNCTYPE(c_int, POINTER(AVCodecContext), POINTER(None), POINTER(c_int), POINTER(c_uint8), c_int))),
    ('capabilities', c_int),
    ('options', POINTER(AVOption)),
    ('next', POINTER(struct_AVCodec)),
    ('flush', POINTER(CFUNCTYPE(None, POINTER(AVCodecContext)))),
    ('supported_framerates', POINTER(AVRational)),
    ('pix_fmts', POINTER(enum_PixelFormat)),
]

AVCodec = struct_AVCodec 	# /usr/include/ffmpeg/avcodec.h:1965
class struct_AVPicture(Structure):
    __slots__ = [
        'data',
        'linesize',
    ]
struct_AVPicture._fields_ = [
    ('data', POINTER(c_uint8) * 4),
    ('linesize', c_int * 4),
]

AVPicture = struct_AVPicture 	# /usr/include/ffmpeg/avcodec.h:1975
AVPALETTE_SIZE = 1024 	# /usr/include/ffmpeg/avcodec.h:1982
AVPALETTE_COUNT = 256 	# /usr/include/ffmpeg/avcodec.h:1983
class struct_AVPaletteControl(Structure):
    __slots__ = [
        'palette_changed',
        'palette',
    ]
struct_AVPaletteControl._fields_ = [
    ('palette_changed', c_int),
    ('palette', c_uint * 256),
]

AVPaletteControl = struct_AVPaletteControl 	# /usr/include/ffmpeg/avcodec.h:1996
class struct_ReSampleContext(Structure):
    __slots__ = [
    ]
struct_ReSampleContext._fields_ = [
    ('_opaque_struct', c_int)
]

class struct_ReSampleContext(Structure):
    __slots__ = [
    ]
struct_ReSampleContext._fields_ = [
    ('_opaque_struct', c_int)
]

ReSampleContext = struct_ReSampleContext 	# /usr/include/ffmpeg/avcodec.h:2179
# /usr/include/ffmpeg/avcodec.h:2181
audio_resample_init = _lib.audio_resample_init
audio_resample_init.restype = POINTER(ReSampleContext)
audio_resample_init.argtypes = [c_int, c_int, c_int, c_int]

# /usr/include/ffmpeg/avcodec.h:2183
audio_resample = _lib.audio_resample
audio_resample.restype = c_int
audio_resample.argtypes = [POINTER(ReSampleContext), POINTER(c_short), POINTER(c_short), c_int]

# /usr/include/ffmpeg/avcodec.h:2184
audio_resample_close = _lib.audio_resample_close
audio_resample_close.restype = None
audio_resample_close.argtypes = [POINTER(ReSampleContext)]

class struct_AVResampleContext(Structure):
    __slots__ = [
    ]
struct_AVResampleContext._fields_ = [
    ('_opaque_struct', c_int)
]

# /usr/include/ffmpeg/avcodec.h:2186
av_resample_init = _lib.av_resample_init
av_resample_init.restype = POINTER(struct_AVResampleContext)
av_resample_init.argtypes = [c_int, c_int, c_int, c_int, c_int, c_double]

class struct_AVResampleContext(Structure):
    __slots__ = [
    ]
struct_AVResampleContext._fields_ = [
    ('_opaque_struct', c_int)
]

# /usr/include/ffmpeg/avcodec.h:2187
av_resample = _lib.av_resample
av_resample.restype = c_int
av_resample.argtypes = [POINTER(struct_AVResampleContext), POINTER(c_short), POINTER(c_short), POINTER(c_int), c_int, c_int, c_int]

class struct_AVResampleContext(Structure):
    __slots__ = [
    ]
struct_AVResampleContext._fields_ = [
    ('_opaque_struct', c_int)
]

# /usr/include/ffmpeg/avcodec.h:2188
av_resample_compensate = _lib.av_resample_compensate
av_resample_compensate.restype = None
av_resample_compensate.argtypes = [POINTER(struct_AVResampleContext), c_int, c_int]

class struct_AVResampleContext(Structure):
    __slots__ = [
    ]
struct_AVResampleContext._fields_ = [
    ('_opaque_struct', c_int)
]

# /usr/include/ffmpeg/avcodec.h:2189
av_resample_close = _lib.av_resample_close
av_resample_close.restype = None
av_resample_close.argtypes = [POINTER(struct_AVResampleContext)]

class struct_ImgReSampleContext(Structure):
    __slots__ = [
    ]
struct_ImgReSampleContext._fields_ = [
    ('_opaque_struct', c_int)
]

class struct_ImgReSampleContext(Structure):
    __slots__ = [
    ]
struct_ImgReSampleContext._fields_ = [
    ('_opaque_struct', c_int)
]

ImgReSampleContext = struct_ImgReSampleContext 	# /usr/include/ffmpeg/avcodec.h:2195
# /usr/include/ffmpeg/avcodec.h:2197
img_resample_init = _lib.img_resample_init
img_resample_init.restype = POINTER(ImgReSampleContext)
img_resample_init.argtypes = [c_int, c_int, c_int, c_int]

# /usr/include/ffmpeg/avcodec.h:2200
img_resample_full_init = _lib.img_resample_full_init
img_resample_full_init.restype = POINTER(ImgReSampleContext)
img_resample_full_init.argtypes = [c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int]

# /usr/include/ffmpeg/avcodec.h:2208
img_resample = _lib.img_resample
img_resample.restype = None
img_resample.argtypes = [POINTER(ImgReSampleContext), POINTER(AVPicture), POINTER(AVPicture)]

# /usr/include/ffmpeg/avcodec.h:2211
img_resample_close = _lib.img_resample_close
img_resample_close.restype = None
img_resample_close.argtypes = [POINTER(ImgReSampleContext)]

# /usr/include/ffmpeg/avcodec.h:2222
avpicture_alloc = _lib.avpicture_alloc
avpicture_alloc.restype = c_int
avpicture_alloc.argtypes = [POINTER(AVPicture), c_int, c_int, c_int]

# /usr/include/ffmpeg/avcodec.h:2225
avpicture_free = _lib.avpicture_free
avpicture_free.restype = None
avpicture_free.argtypes = [POINTER(AVPicture)]

# /usr/include/ffmpeg/avcodec.h:2227
avpicture_fill = _lib.avpicture_fill
avpicture_fill.restype = c_int
avpicture_fill.argtypes = [POINTER(AVPicture), POINTER(c_uint8), c_int, c_int, c_int]

# /usr/include/ffmpeg/avcodec.h:2229
avpicture_layout = _lib.avpicture_layout
avpicture_layout.restype = c_int
avpicture_layout.argtypes = [POINTER(AVPicture), c_int, c_int, c_int, POINTER(c_ubyte), c_int]

# /usr/include/ffmpeg/avcodec.h:2231
avpicture_get_size = _lib.avpicture_get_size
avpicture_get_size.restype = c_int
avpicture_get_size.argtypes = [c_int, c_int, c_int]

# /usr/include/ffmpeg/avcodec.h:2232
avcodec_get_chroma_sub_sample = _lib.avcodec_get_chroma_sub_sample
avcodec_get_chroma_sub_sample.restype = None
avcodec_get_chroma_sub_sample.argtypes = [c_int, POINTER(c_int), POINTER(c_int)]

# /usr/include/ffmpeg/avcodec.h:2233
avcodec_get_pix_fmt_name = _lib.avcodec_get_pix_fmt_name
avcodec_get_pix_fmt_name.restype = c_char_p
avcodec_get_pix_fmt_name.argtypes = [c_int]

# /usr/include/ffmpeg/avcodec.h:2234
avcodec_set_dimensions = _lib.avcodec_set_dimensions
avcodec_set_dimensions.restype = None
avcodec_set_dimensions.argtypes = [POINTER(AVCodecContext), c_int, c_int]

# /usr/include/ffmpeg/avcodec.h:2235
avcodec_get_pix_fmt = _lib.avcodec_get_pix_fmt
avcodec_get_pix_fmt.restype = enum_PixelFormat
avcodec_get_pix_fmt.argtypes = [c_char_p]

# /usr/include/ffmpeg/avcodec.h:2236
avcodec_pix_fmt_to_codec_tag = _lib.avcodec_pix_fmt_to_codec_tag
avcodec_pix_fmt_to_codec_tag.restype = c_uint
avcodec_pix_fmt_to_codec_tag.argtypes = [enum_PixelFormat]

FF_LOSS_RESOLUTION = 1 	# /usr/include/ffmpeg/avcodec.h:2238
FF_LOSS_DEPTH = 2 	# /usr/include/ffmpeg/avcodec.h:2239
FF_LOSS_COLORSPACE = 4 	# /usr/include/ffmpeg/avcodec.h:2240
FF_LOSS_ALPHA = 8 	# /usr/include/ffmpeg/avcodec.h:2241
FF_LOSS_COLORQUANT = 16 	# /usr/include/ffmpeg/avcodec.h:2242
FF_LOSS_CHROMA = 32 	# /usr/include/ffmpeg/avcodec.h:2243
# /usr/include/ffmpeg/avcodec.h:2245
avcodec_get_pix_fmt_loss = _lib.avcodec_get_pix_fmt_loss
avcodec_get_pix_fmt_loss.restype = c_int
avcodec_get_pix_fmt_loss.argtypes = [c_int, c_int, c_int]

# /usr/include/ffmpeg/avcodec.h:2247
avcodec_find_best_pix_fmt = _lib.avcodec_find_best_pix_fmt
avcodec_find_best_pix_fmt.restype = c_int
avcodec_find_best_pix_fmt.argtypes = [c_int, c_int, c_int, POINTER(c_int)]

FF_ALPHA_TRANSP = 1 	# /usr/include/ffmpeg/avcodec.h:2250
FF_ALPHA_SEMI_TRANSP = 2 	# /usr/include/ffmpeg/avcodec.h:2251
# /usr/include/ffmpeg/avcodec.h:2252
img_get_alpha_info = _lib.img_get_alpha_info
img_get_alpha_info.restype = c_int
img_get_alpha_info.argtypes = [POINTER(AVPicture), c_int, c_int, c_int]

# /usr/include/ffmpeg/avcodec.h:2256
img_convert = _lib.img_convert
img_convert.restype = c_int
img_convert.argtypes = [POINTER(AVPicture), c_int, POINTER(AVPicture), c_int, c_int, c_int]

# /usr/include/ffmpeg/avcodec.h:2261
avpicture_deinterlace = _lib.avpicture_deinterlace
avpicture_deinterlace.restype = c_int
avpicture_deinterlace.argtypes = [POINTER(AVPicture), POINTER(AVPicture), c_int, c_int, c_int]

# /usr/include/ffmpeg/avcodec.h:2269
avcodec_version = _lib.avcodec_version
avcodec_version.restype = c_uint
avcodec_version.argtypes = []

# /usr/include/ffmpeg/avcodec.h:2271
avcodec_build = _lib.avcodec_build
avcodec_build.restype = c_uint
avcodec_build.argtypes = []

# /usr/include/ffmpeg/avcodec.h:2272
avcodec_init = _lib.avcodec_init
avcodec_init.restype = None
avcodec_init.argtypes = []

# /usr/include/ffmpeg/avcodec.h:2274
register_avcodec = _lib.register_avcodec
register_avcodec.restype = None
register_avcodec.argtypes = [POINTER(AVCodec)]

# /usr/include/ffmpeg/avcodec.h:2275
avcodec_find_encoder = _lib.avcodec_find_encoder
avcodec_find_encoder.restype = POINTER(AVCodec)
avcodec_find_encoder.argtypes = [enum_CodecID]

# /usr/include/ffmpeg/avcodec.h:2276
avcodec_find_encoder_by_name = _lib.avcodec_find_encoder_by_name
avcodec_find_encoder_by_name.restype = POINTER(AVCodec)
avcodec_find_encoder_by_name.argtypes = [c_char_p]

# /usr/include/ffmpeg/avcodec.h:2277
avcodec_find_decoder = _lib.avcodec_find_decoder
avcodec_find_decoder.restype = POINTER(AVCodec)
avcodec_find_decoder.argtypes = [enum_CodecID]

# /usr/include/ffmpeg/avcodec.h:2278
avcodec_find_decoder_by_name = _lib.avcodec_find_decoder_by_name
avcodec_find_decoder_by_name.restype = POINTER(AVCodec)
avcodec_find_decoder_by_name.argtypes = [c_char_p]

# /usr/include/ffmpeg/avcodec.h:2279
avcodec_string = _lib.avcodec_string
avcodec_string.restype = None
avcodec_string.argtypes = [c_char_p, c_int, POINTER(AVCodecContext), c_int]

# /usr/include/ffmpeg/avcodec.h:2281
avcodec_get_context_defaults = _lib.avcodec_get_context_defaults
avcodec_get_context_defaults.restype = None
avcodec_get_context_defaults.argtypes = [POINTER(AVCodecContext)]

# /usr/include/ffmpeg/avcodec.h:2282
avcodec_alloc_context = _lib.avcodec_alloc_context
avcodec_alloc_context.restype = POINTER(AVCodecContext)
avcodec_alloc_context.argtypes = []

# /usr/include/ffmpeg/avcodec.h:2283
avcodec_get_frame_defaults = _lib.avcodec_get_frame_defaults
avcodec_get_frame_defaults.restype = None
avcodec_get_frame_defaults.argtypes = [POINTER(AVFrame)]

# /usr/include/ffmpeg/avcodec.h:2284
avcodec_alloc_frame = _lib.avcodec_alloc_frame
avcodec_alloc_frame.restype = POINTER(AVFrame)
avcodec_alloc_frame.argtypes = []

# /usr/include/ffmpeg/avcodec.h:2286
avcodec_default_get_buffer = _lib.avcodec_default_get_buffer
avcodec_default_get_buffer.restype = c_int
avcodec_default_get_buffer.argtypes = [POINTER(AVCodecContext), POINTER(AVFrame)]

# /usr/include/ffmpeg/avcodec.h:2287
avcodec_default_release_buffer = _lib.avcodec_default_release_buffer
avcodec_default_release_buffer.restype = None
avcodec_default_release_buffer.argtypes = [POINTER(AVCodecContext), POINTER(AVFrame)]

# /usr/include/ffmpeg/avcodec.h:2288
avcodec_default_reget_buffer = _lib.avcodec_default_reget_buffer
avcodec_default_reget_buffer.restype = c_int
avcodec_default_reget_buffer.argtypes = [POINTER(AVCodecContext), POINTER(AVFrame)]

# /usr/include/ffmpeg/avcodec.h:2289
avcodec_align_dimensions = _lib.avcodec_align_dimensions
avcodec_align_dimensions.restype = None
avcodec_align_dimensions.argtypes = [POINTER(AVCodecContext), POINTER(c_int), POINTER(c_int)]

# /usr/include/ffmpeg/avcodec.h:2290
avcodec_check_dimensions = _lib.avcodec_check_dimensions
avcodec_check_dimensions.restype = c_int
avcodec_check_dimensions.argtypes = [POINTER(None), c_uint, c_uint]

# /usr/include/ffmpeg/avcodec.h:2291
avcodec_default_get_format = _lib.avcodec_default_get_format
avcodec_default_get_format.restype = enum_PixelFormat
avcodec_default_get_format.argtypes = [POINTER(struct_AVCodecContext), POINTER(enum_PixelFormat)]

# /usr/include/ffmpeg/avcodec.h:2293
avcodec_thread_init = _lib.avcodec_thread_init
avcodec_thread_init.restype = c_int
avcodec_thread_init.argtypes = [POINTER(AVCodecContext), c_int]

# /usr/include/ffmpeg/avcodec.h:2296
avcodec_default_execute = _lib.avcodec_default_execute
avcodec_default_execute.restype = c_int
avcodec_default_execute.argtypes = [POINTER(AVCodecContext), CFUNCTYPE(c_int, POINTER(AVCodecContext), POINTER(None)), POINTER(POINTER(None)), POINTER(c_int), c_int]

# /usr/include/ffmpeg/avcodec.h:2304
avcodec_open = _lib.avcodec_open
avcodec_open.restype = c_int
avcodec_open.argtypes = [POINTER(AVCodecContext), POINTER(AVCodec)]

# /usr/include/ffmpeg/avcodec.h:2306
avcodec_decode_audio = _lib.avcodec_decode_audio
avcodec_decode_audio.restype = c_int
avcodec_decode_audio.argtypes = [POINTER(AVCodecContext), POINTER(c_int16), POINTER(c_int), POINTER(c_uint8), c_int]

# /usr/include/ffmpeg/avcodec.h:2309
avcodec_decode_video = _lib.avcodec_decode_video
avcodec_decode_video.restype = c_int
avcodec_decode_video.argtypes = [POINTER(AVCodecContext), POINTER(AVFrame), POINTER(c_int), POINTER(c_uint8), c_int]

# /usr/include/ffmpeg/avcodec.h:2315
avcodec_encode_audio = _lib.avcodec_encode_audio
avcodec_encode_audio.restype = c_int
avcodec_encode_audio.argtypes = [POINTER(AVCodecContext), POINTER(c_uint8), c_int, POINTER(c_short)]

# /usr/include/ffmpeg/avcodec.h:2317
avcodec_encode_video = _lib.avcodec_encode_video
avcodec_encode_video.restype = c_int
avcodec_encode_video.argtypes = [POINTER(AVCodecContext), POINTER(c_uint8), c_int, POINTER(AVFrame)]

# /usr/include/ffmpeg/avcodec.h:2320
avcodec_close = _lib.avcodec_close
avcodec_close.restype = c_int
avcodec_close.argtypes = [POINTER(AVCodecContext)]

# /usr/include/ffmpeg/avcodec.h:2322
avcodec_register_all = _lib.avcodec_register_all
avcodec_register_all.restype = None
avcodec_register_all.argtypes = []

# /usr/include/ffmpeg/avcodec.h:2324
avcodec_flush_buffers = _lib.avcodec_flush_buffers
avcodec_flush_buffers.restype = None
avcodec_flush_buffers.argtypes = [POINTER(AVCodecContext)]

# /usr/include/ffmpeg/avcodec.h:2326
avcodec_default_free_buffers = _lib.avcodec_default_free_buffers
avcodec_default_free_buffers.restype = None
avcodec_default_free_buffers.argtypes = [POINTER(AVCodecContext)]

# /usr/include/ffmpeg/avcodec.h:2333
av_get_pict_type_char = _lib.av_get_pict_type_char
av_get_pict_type_char.restype = c_char
av_get_pict_type_char.argtypes = [c_int]

# /usr/include/ffmpeg/avcodec.h:2341
av_reduce = _lib.av_reduce
av_reduce.restype = c_int
av_reduce.argtypes = [POINTER(c_int), POINTER(c_int), c_int64, c_int64, c_int64]

# /usr/include/ffmpeg/avcodec.h:2347
av_rescale = _lib.av_rescale
av_rescale.restype = c_int64
av_rescale.argtypes = [c_int64, c_int64, c_int64]

enum_AVRounding = c_int
# /usr/include/ffmpeg/avcodec.h:2353
av_rescale_rnd = _lib.av_rescale_rnd
av_rescale_rnd.restype = c_int64
av_rescale_rnd.argtypes = [c_int64, c_int64, c_int64, enum_AVRounding]

AV_PARSER_PTS_NB = 4 	# /usr/include/ffmpeg/avcodec.h:2374
class struct_AVCodecParserContext(Structure):
    __slots__ = [
        'priv_data',
        'parser',
        'frame_offset',
        'cur_offset',
        'last_frame_offset',
        'pict_type',
        'repeat_pict',
        'pts',
        'dts',
        'last_pts',
        'last_dts',
        'fetch_timestamp',
        'cur_frame_start_index',
        'cur_frame_offset',
        'cur_frame_pts',
        'cur_frame_dts',
    ]
class struct_AVCodecParser(Structure):
    __slots__ = [
    ]
struct_AVCodecParser._fields_ = [
    ('_opaque_struct', c_int)
]

struct_AVCodecParserContext._fields_ = [
    ('priv_data', POINTER(None)),
    ('parser', POINTER(struct_AVCodecParser)),
    ('frame_offset', c_int64),
    ('cur_offset', c_int64),
    ('last_frame_offset', c_int64),
    ('pict_type', c_int),
    ('repeat_pict', c_int),
    ('pts', c_int64),
    ('dts', c_int64),
    ('last_pts', c_int64),
    ('last_dts', c_int64),
    ('fetch_timestamp', c_int),
    ('cur_frame_start_index', c_int),
    ('cur_frame_offset', c_int64 * 4),
    ('cur_frame_pts', c_int64 * 4),
    ('cur_frame_dts', c_int64 * 4),
]

AVCodecParserContext = struct_AVCodecParserContext 	# /usr/include/ffmpeg/avcodec.h:2379
class struct_AVCodecParser(Structure):
    __slots__ = [
        'codec_ids',
        'priv_data_size',
        'parser_init',
        'parser_parse',
        'parser_close',
        'next',
    ]
struct_AVCodecParser._fields_ = [
    ('codec_ids', c_int * 5),
    ('priv_data_size', c_int),
    ('parser_init', POINTER(CFUNCTYPE(c_int, POINTER(AVCodecParserContext)))),
    ('parser_parse', POINTER(CFUNCTYPE(c_int, POINTER(AVCodecParserContext), POINTER(AVCodecContext), POINTER(POINTER(c_uint8)), POINTER(c_int), POINTER(c_uint8), c_int))),
    ('parser_close', POINTER(CFUNCTYPE(None, POINTER(AVCodecParserContext)))),
    ('next', POINTER(struct_AVCodecParser)),
]

AVCodecParser = struct_AVCodecParser 	# /usr/include/ffmpeg/avcodec.h:2391
# /usr/include/ffmpeg/avcodec.h:2395
av_register_codec_parser = _lib.av_register_codec_parser
av_register_codec_parser.restype = None
av_register_codec_parser.argtypes = [POINTER(AVCodecParser)]

# /usr/include/ffmpeg/avcodec.h:2396
av_parser_init = _lib.av_parser_init
av_parser_init.restype = POINTER(AVCodecParserContext)
av_parser_init.argtypes = [c_int]

# /usr/include/ffmpeg/avcodec.h:2397
av_parser_parse = _lib.av_parser_parse
av_parser_parse.restype = c_int
av_parser_parse.argtypes = [POINTER(AVCodecParserContext), POINTER(AVCodecContext), POINTER(POINTER(c_uint8)), POINTER(c_int), POINTER(c_uint8), c_int, c_int64, c_int64]

# /usr/include/ffmpeg/avcodec.h:2402
av_parser_close = _lib.av_parser_close
av_parser_close.restype = None
av_parser_close.argtypes = [POINTER(AVCodecParserContext)]

# /usr/include/ffmpeg/avcodec.h:2415
av_malloc = _lib.av_malloc
av_malloc.restype = POINTER(c_void)
av_malloc.argtypes = [c_uint]

# /usr/include/ffmpeg/avcodec.h:2416
av_mallocz = _lib.av_mallocz
av_mallocz.restype = POINTER(c_void)
av_mallocz.argtypes = [c_uint]

# /usr/include/ffmpeg/avcodec.h:2417
av_realloc = _lib.av_realloc
av_realloc.restype = POINTER(c_void)
av_realloc.argtypes = [POINTER(None), c_uint]

# /usr/include/ffmpeg/avcodec.h:2418
av_free = _lib.av_free
av_free.restype = None
av_free.argtypes = [POINTER(None)]

# /usr/include/ffmpeg/avcodec.h:2419
av_strdup = _lib.av_strdup
av_strdup.restype = c_char_p
av_strdup.argtypes = [c_char_p]

# /usr/include/ffmpeg/avcodec.h:2420
av_freep = _lib.av_freep
av_freep.restype = None
av_freep.argtypes = [POINTER(None)]

# /usr/include/ffmpeg/avcodec.h:2421
av_fast_realloc = _lib.av_fast_realloc
av_fast_realloc.restype = POINTER(c_void)
av_fast_realloc.argtypes = [POINTER(None), POINTER(c_uint), c_uint]

# /usr/include/ffmpeg/avcodec.h:2424
av_free_static = _lib.av_free_static
av_free_static.restype = None
av_free_static.argtypes = []

# /usr/include/ffmpeg/avcodec.h:2425
av_mallocz_static = _lib.av_mallocz_static
av_mallocz_static.restype = POINTER(c_void)
av_mallocz_static.argtypes = [c_uint]

# /usr/include/ffmpeg/avcodec.h:2426
av_realloc_static = _lib.av_realloc_static
av_realloc_static.restype = POINTER(c_void)
av_realloc_static.argtypes = [POINTER(None), c_uint]

# /usr/include/ffmpeg/avcodec.h:2429
is_adx = _lib.is_adx
is_adx.restype = c_int
is_adx.argtypes = [POINTER(c_ubyte), c_size_t]

# /usr/include/ffmpeg/avcodec.h:2431
img_copy = _lib.img_copy
img_copy.restype = None
img_copy.argtypes = [POINTER(AVPicture), POINTER(AVPicture), c_int, c_int, c_int]

AV_LOG_QUIET = -1 	# /usr/include/ffmpeg/avcodec.h:2438
AV_LOG_ERROR = 0 	# /usr/include/ffmpeg/avcodec.h:2439
AV_LOG_INFO = 1 	# /usr/include/ffmpeg/avcodec.h:2440
AV_LOG_DEBUG = 2 	# /usr/include/ffmpeg/avcodec.h:2441
# /usr/include/ffmpeg/avcodec.h:2444
av_log = _lib.av_log
av_log.restype = None
av_log.argtypes = [POINTER(None), c_int, c_char_p]

# /usr/include/ffmpeg/avcodec.h:2450
av_log_get_level = _lib.av_log_get_level
av_log_get_level.restype = c_int
av_log_get_level.argtypes = []

# /usr/include/ffmpeg/avcodec.h:2451
av_log_set_level = _lib.av_log_set_level
av_log_set_level.restype = None
av_log_set_level.argtypes = [c_int]

__all__ = ['FFMPEG_VERSION_INT', 'LIBAVCODEC_BUILD', 'LIBAVCODEC_VERSION_INT',
'AV_TIME_BASE', 'CODEC_ID_MP3LAME', 'AVCODEC_MAX_AUDIO_FRAME_SIZE',
'FF_INPUT_BUFFER_PADDING_SIZE', 'FF_MIN_BUFFER_SIZE', 'RcOverride',
'FF_MAX_B_FRAMES', 'CODEC_FLAG_QSCALE', 'CODEC_FLAG_4MV', 'CODEC_FLAG_QPEL',
'CODEC_FLAG_GMC', 'CODEC_FLAG_MV0', 'CODEC_FLAG_PART',
'CODEC_FLAG_INPUT_PRESERVED', 'CODEC_FLAG_PASS1', 'CODEC_FLAG_PASS2',
'CODEC_FLAG_EXTERN_HUFF', 'CODEC_FLAG_GRAY', 'CODEC_FLAG_EMU_EDGE',
'CODEC_FLAG_PSNR', 'CODEC_FLAG_TRUNCATED', 'CODEC_FLAG_NORMALIZE_AQP',
'CODEC_FLAG_INTERLACED_DCT', 'CODEC_FLAG_LOW_DELAY', 'CODEC_FLAG_ALT_SCAN',
'CODEC_FLAG_TRELLIS_QUANT', 'CODEC_FLAG_GLOBAL_HEADER', 'CODEC_FLAG_BITEXACT',
'CODEC_FLAG_H263P_AIC', 'CODEC_FLAG_AC_PRED', 'CODEC_FLAG_H263P_UMV',
'CODEC_FLAG_CBP_RD', 'CODEC_FLAG_QP_RD', 'CODEC_FLAG_H263P_AIV',
'CODEC_FLAG_OBMC', 'CODEC_FLAG_LOOP_FILTER', 'CODEC_FLAG_H263P_SLICE_STRUCT',
'CODEC_FLAG_INTERLACED_ME', 'CODEC_FLAG_SVCD_SCAN_OFFSET',
'CODEC_FLAG_CLOSED_GOP', 'CODEC_FLAG2_FAST', 'CODEC_FLAG2_STRICT_GOP',
'CODEC_FLAG2_NO_OUTPUT', 'CODEC_CAP_DRAW_HORIZ_BAND', 'CODEC_CAP_DR1',
'CODEC_CAP_PARSE_ONLY', 'CODEC_CAP_TRUNCATED', 'CODEC_CAP_HWACCEL',
'CODEC_CAP_DELAY', 'MB_TYPE_INTRA4x4', 'MB_TYPE_INTRA16x16',
'MB_TYPE_INTRA_PCM', 'MB_TYPE_16x16', 'MB_TYPE_16x8', 'MB_TYPE_8x16',
'MB_TYPE_8x8', 'MB_TYPE_INTERLACED', 'MB_TYPE_DIRECT2', 'MB_TYPE_ACPRED',
'MB_TYPE_GMC', 'MB_TYPE_SKIP', 'MB_TYPE_P0L0', 'MB_TYPE_P1L0', 'MB_TYPE_P0L1',
'MB_TYPE_P1L1', 'MB_TYPE_L0', 'MB_TYPE_L1', 'MB_TYPE_L0L1', 'MB_TYPE_QUANT',
'MB_TYPE_CBP', 'AVPanScan', 'FF_QSCALE_TYPE_MPEG1', 'FF_QSCALE_TYPE_MPEG2',
'FF_BUFFER_TYPE_INTERNAL', 'FF_BUFFER_TYPE_USER', 'FF_BUFFER_TYPE_SHARED',
'FF_BUFFER_TYPE_COPY', 'FF_I_TYPE', 'FF_P_TYPE', 'FF_B_TYPE', 'FF_S_TYPE',
'FF_SI_TYPE', 'FF_SP_TYPE', 'FF_BUFFER_HINTS_VALID',
'FF_BUFFER_HINTS_READABLE', 'FF_BUFFER_HINTS_PRESERVE',
'FF_BUFFER_HINTS_REUSABLE', 'AVFrame', 'DEFAULT_FRAME_RATE_BASE', 'AVClass',
'FF_ASPECT_EXTENDED', 'FF_BUG_AUTODETECT', 'FF_BUG_OLD_MSMPEG4',
'FF_BUG_XVID_ILACE', 'FF_BUG_UMP4', 'FF_BUG_NO_PADDING', 'FF_BUG_AMV',
'FF_BUG_AC_VLC', 'FF_BUG_QPEL_CHROMA', 'FF_BUG_STD_QPEL',
'FF_BUG_QPEL_CHROMA2', 'FF_BUG_DIRECT_BLOCKSIZE', 'FF_BUG_EDGE',
'FF_BUG_HPEL_CHROMA', 'FF_BUG_DC_CLIP', 'FF_ER_CAREFULL', 'FF_ER_COMPLIANT',
'FF_ER_AGGRESSIVE', 'FF_ER_VERY_AGGRESSIVE', 'FF_DCT_AUTO', 'FF_DCT_FASTINT',
'FF_DCT_INT', 'FF_DCT_MMX', 'FF_DCT_MLIB', 'FF_DCT_ALTIVEC', 'FF_DCT_FAAN',
'FF_IDCT_AUTO', 'FF_IDCT_INT', 'FF_IDCT_SIMPLE', 'FF_IDCT_SIMPLEMMX',
'FF_IDCT_LIBMPEG2MMX', 'FF_IDCT_PS2', 'FF_IDCT_MLIB', 'FF_IDCT_ARM',
'FF_IDCT_ALTIVEC', 'FF_IDCT_SH4', 'FF_IDCT_SIMPLEARM', 'FF_IDCT_H264',
'FF_EC_GUESS_MVS', 'FF_EC_DEBLOCK', 'FF_MM_FORCE', 'FF_PRED_LEFT',
'FF_PRED_PLANE', 'FF_PRED_MEDIAN', 'FF_DEBUG_PICT_INFO', 'FF_DEBUG_RC',
'FF_DEBUG_BITSTREAM', 'FF_DEBUG_MB_TYPE', 'FF_DEBUG_QP', 'FF_DEBUG_MV',
'FF_DEBUG_DCT_COEFF', 'FF_DEBUG_SKIP', 'FF_DEBUG_STARTCODE', 'FF_DEBUG_PTS',
'FF_DEBUG_ER', 'FF_DEBUG_MMCO', 'FF_DEBUG_BUGS', 'FF_DEBUG_VIS_QP',
'FF_DEBUG_VIS_MB_TYPE', 'FF_DEBUG_VIS_MV_P_FOR', 'FF_DEBUG_VIS_MV_B_FOR',
'FF_DEBUG_VIS_MV_B_BACK', 'FF_CMP_SAD', 'FF_CMP_SSE', 'FF_CMP_SATD',
'FF_CMP_DCT', 'FF_CMP_PSNR', 'FF_CMP_BIT', 'FF_CMP_RD', 'FF_CMP_ZERO',
'FF_CMP_VSAD', 'FF_CMP_VSSE', 'FF_CMP_NSSE', 'FF_CMP_W53', 'FF_CMP_W97',
'FF_CMP_DCTMAX', 'FF_CMP_CHROMA', 'FF_DTG_AFD_SAME', 'FF_DTG_AFD_4_3',
'FF_DTG_AFD_16_9', 'FF_DTG_AFD_14_9', 'FF_DTG_AFD_4_3_SP_14_9',
'FF_DTG_AFD_16_9_SP_14_9', 'FF_DTG_AFD_SP_4_3', 'FF_DEFAULT_QUANT_BIAS',
'FF_LAMBDA_SHIFT', 'FF_LAMBDA_SCALE', 'FF_QP2LAMBDA', 'FF_LAMBDA_MAX',
'FF_QUALITY_SCALE', 'FF_CODER_TYPE_VLC', 'FF_CODER_TYPE_AC',
'SLICE_FLAG_CODED_ORDER', 'SLICE_FLAG_ALLOW_FIELD', 'SLICE_FLAG_ALLOW_PLANE',
'FF_MB_DECISION_SIMPLE', 'FF_MB_DECISION_BITS', 'FF_MB_DECISION_RD',
'FF_AA_AUTO', 'FF_AA_FASTINT', 'FF_AA_INT', 'FF_AA_FLOAT',
'FF_PROFILE_UNKNOWN', 'FF_LEVEL_UNKNOWN', 'AVCodecContext',
'FF_OPT_TYPE_BOOL', 'FF_OPT_TYPE_DOUBLE', 'FF_OPT_TYPE_INT',
'FF_OPT_TYPE_STRING', 'FF_OPT_TYPE_MASK', 'FF_OPT_TYPE_FLAG',
'FF_OPT_TYPE_RCOVERRIDE', 'FF_OPT_MAX_DEPTH', 'AVOption', 'avoption_parse',
'AVCodec', 'AVPicture', 'AVPALETTE_SIZE', 'AVPALETTE_COUNT',
'AVPaletteControl', 'ReSampleContext', 'audio_resample_init',
'audio_resample', 'audio_resample_close', 'av_resample_init', 'av_resample',
'av_resample_compensate', 'av_resample_close', 'ImgReSampleContext',
'img_resample_init', 'img_resample_full_init', 'img_resample',
'img_resample_close', 'avpicture_alloc', 'avpicture_free', 'avpicture_fill',
'avpicture_layout', 'avpicture_get_size', 'avcodec_get_chroma_sub_sample',
'avcodec_get_pix_fmt_name', 'avcodec_set_dimensions', 'avcodec_get_pix_fmt',
'avcodec_pix_fmt_to_codec_tag', 'FF_LOSS_RESOLUTION', 'FF_LOSS_DEPTH',
'FF_LOSS_COLORSPACE', 'FF_LOSS_ALPHA', 'FF_LOSS_COLORQUANT', 'FF_LOSS_CHROMA',
'avcodec_get_pix_fmt_loss', 'avcodec_find_best_pix_fmt', 'FF_ALPHA_TRANSP',
'FF_ALPHA_SEMI_TRANSP', 'img_get_alpha_info', 'img_convert',
'avpicture_deinterlace', 'avcodec_version', 'avcodec_build', 'avcodec_init',
'register_avcodec', 'avcodec_find_encoder', 'avcodec_find_encoder_by_name',
'avcodec_find_decoder', 'avcodec_find_decoder_by_name', 'avcodec_string',
'avcodec_get_context_defaults', 'avcodec_alloc_context',
'avcodec_get_frame_defaults', 'avcodec_alloc_frame',
'avcodec_default_get_buffer', 'avcodec_default_release_buffer',
'avcodec_default_reget_buffer', 'avcodec_align_dimensions',
'avcodec_check_dimensions', 'avcodec_default_get_format',
'avcodec_thread_init', 'avcodec_thread_free', 'avcodec_thread_execute',
'avcodec_default_execute', 'avcodec_open', 'avcodec_decode_audio',
'avcodec_decode_video', 'avcodec_parse_frame', 'avcodec_encode_audio',
'avcodec_encode_video', 'avcodec_close', 'avcodec_register_all',
'avcodec_flush_buffers', 'avcodec_default_free_buffers',
'av_get_pict_type_char', 'av_reduce', 'av_rescale', 'av_rescale_rnd',
'AV_PARSER_PTS_NB', 'AVCodecParserContext', 'AVCodecParser',
'av_register_codec_parser', 'av_parser_init', 'av_parser_parse',
'av_parser_close', 'av_malloc', 'av_mallocz', 'av_realloc', 'av_free',
'av_strdup', 'av_freep', 'av_fast_realloc', 'av_free_static',
'av_mallocz_static', 'av_realloc_static', 'is_adx', 'img_copy',
'AV_LOG_QUIET', 'AV_LOG_ERROR', 'AV_LOG_INFO', 'AV_LOG_DEBUG', 'av_log',
'av_vlog', 'av_log_get_level', 'av_log_set_level', 'av_log_set_callback']
