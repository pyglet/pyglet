"""Bindings to PipeWire and SPA.

These are hand-written ctypes bindings (mirroring the generated bindings
of the other backends), plus a small pure-Python reimplementation of the
SPA POD builder needed to advertise the supported audio formats.

All PipeWire calls must be made with the main-loop lock held unless the
documented function is explicitly thread-safe ("RT safe").
"""

from __future__ import annotations

import struct
from ctypes import (
    CFUNCTYPE, POINTER, Structure, byref, c_bool, c_char_p, c_double, c_int,
    c_int32, c_int64, c_size_t, c_ubyte, c_uint32, c_uint64, c_void_p,
    cast, create_string_buffer)
from typing import Any, Callable, Optional

import pyglet.lib


_lib = pyglet.lib.load_library('pipewire-0.3')


class c_void(Structure):
    # c_void_p is a buggy return type, converting to int, so
    # POINTER(None) == c_void_p is actually written as
    # POINTER(c_void), so it can be treated as a real pointer.
    _fields_ = [('dummy', c_int)]


# Opaque types:
class struct_pw_loop(Structure):
    _fields_ = [('_opaque_struct', c_int)]


class struct_pw_context(Structure):
    _fields_ = [('_opaque_struct', c_int)]


class struct_pw_core(Structure):
    _fields_ = [('_opaque_struct', c_int)]


class struct_pw_stream(Structure):
    _fields_ = [('_opaque_struct', c_int)]


class struct_pw_thread_loop(Structure):
    _fields_ = [('_opaque_struct', c_int)]


class struct_pw_properties(Structure):
    _fields_ = [('_opaque_struct', c_int)]


class struct_spa_handle(Structure):
    _fields_ = [('_opaque_struct', c_int)]


class struct_spa_hook(Structure):
    # Fill the full size, as it is opaque and written to by the library.
    _fields_ = [('_opaque_struct', c_ubyte * 64)]


# Real types:
class struct_spa_pod(Structure):
    """Header of a SPA POD. The body follows the two 32-bit fields."""
    _fields_ = [('size', c_uint32), ('type', c_uint32)]


class struct_spa_dict_item(Structure):
    _fields_ = [('key', c_char_p), ('value', c_char_p)]


class struct_spa_dict(Structure):
    _fields_ = [('flags', c_uint32), ('n_items', c_uint32),
                ('items', POINTER(struct_spa_dict_item))]


class struct_spa_chunk(Structure):
    _fields_ = [('offset', c_uint32), ('size', c_uint32),
                ('stride', c_int32), ('flags', c_int32)]


class struct_spa_data(Structure):
    _fields_ = [('type', c_uint32), ('flags', c_uint32), ('fd', c_int64),
                ('mapoffset', c_uint32), ('maxsize', c_uint32),
                ('data', c_void_p), ('chunk', POINTER(struct_spa_chunk))]


class struct_spa_buffer(Structure):
    _fields_ = [('n_metas', c_uint32), ('n_datas', c_uint32),
                ('metas', c_void_p), ('datas', POINTER(struct_spa_data))]


class struct_pw_buffer(Structure):
    _fields_ = [('buffer', POINTER(struct_spa_buffer)),
                ('user_data', c_void_p), ('size', c_uint64),
                ('requested', c_uint64), ('time', c_uint64)]


class struct_spa_fraction(Structure):
    _fields_ = [('num', c_uint32), ('denom', c_uint32)]


class struct_pw_time(Structure):
    _fields_ = [('now', c_int64),
                ('rate', struct_spa_fraction),
                ('ticks', c_uint64),
                ('delay', c_int64),
                ('queued', c_uint64),
                ('buffered', c_uint64),
                ('queued_buffers', c_uint32),
                ('avail_buffers', c_uint32),
                ('size', c_uint64)]


# Functions:
pw_init = _lib.pw_init
pw_init.restype = None
pw_init.argtypes = [POINTER(c_int), POINTER(POINTER(c_char_p))]

pw_deinit = _lib.pw_deinit
pw_deinit.restype = None
pw_deinit.argtypes = []

pw_get_library_version = _lib.pw_get_library_version
pw_get_library_version.restype = c_char_p
pw_get_library_version.argtypes = []


# Thread loop:
pw_thread_loop_new = _lib.pw_thread_loop_new
pw_thread_loop_new.restype = POINTER(struct_pw_thread_loop)
pw_thread_loop_new.argtypes = [c_char_p, POINTER(struct_spa_dict)]

pw_thread_loop_destroy = _lib.pw_thread_loop_destroy
pw_thread_loop_destroy.restype = None
pw_thread_loop_destroy.argtypes = [POINTER(struct_pw_thread_loop)]

pw_thread_loop_get_loop = _lib.pw_thread_loop_get_loop
pw_thread_loop_get_loop.restype = POINTER(struct_pw_loop)
pw_thread_loop_get_loop.argtypes = [POINTER(struct_pw_thread_loop)]

pw_thread_loop_start = _lib.pw_thread_loop_start
pw_thread_loop_start.restype = c_int
pw_thread_loop_start.argtypes = [POINTER(struct_pw_thread_loop)]

pw_thread_loop_stop = _lib.pw_thread_loop_stop
pw_thread_loop_stop.restype = None
pw_thread_loop_stop.argtypes = [POINTER(struct_pw_thread_loop)]

pw_thread_loop_lock = _lib.pw_thread_loop_lock
pw_thread_loop_lock.restype = None
pw_thread_loop_lock.argtypes = [POINTER(struct_pw_thread_loop)]

pw_thread_loop_unlock = _lib.pw_thread_loop_unlock
pw_thread_loop_unlock.restype = None
pw_thread_loop_unlock.argtypes = [POINTER(struct_pw_thread_loop)]

pw_thread_loop_wait = _lib.pw_thread_loop_wait
pw_thread_loop_wait.restype = None
pw_thread_loop_wait.argtypes = [POINTER(struct_pw_thread_loop)]

pw_thread_loop_timed_wait = _lib.pw_thread_loop_timed_wait
pw_thread_loop_timed_wait.restype = c_int
pw_thread_loop_timed_wait.argtypes = [POINTER(struct_pw_thread_loop), c_int]

pw_thread_loop_signal = _lib.pw_thread_loop_signal
pw_thread_loop_signal.restype = None
pw_thread_loop_signal.argtypes = [POINTER(struct_pw_thread_loop), c_bool]

pw_thread_loop_in_thread = _lib.pw_thread_loop_in_thread
pw_thread_loop_in_thread.restype = c_bool
pw_thread_loop_in_thread.argtypes = [POINTER(struct_pw_thread_loop)]


# Context and core:
pw_context_new = _lib.pw_context_new
pw_context_new.restype = POINTER(struct_pw_context)
pw_context_new.argtypes = [POINTER(struct_pw_loop), POINTER(struct_pw_properties),
                           c_size_t]

pw_context_destroy = _lib.pw_context_destroy
pw_context_destroy.restype = None
pw_context_destroy.argtypes = [POINTER(struct_pw_context)]

pw_context_connect = _lib.pw_context_connect
pw_context_connect.restype = POINTER(struct_pw_core)
pw_context_connect.argtypes = [POINTER(struct_pw_context), POINTER(struct_pw_properties),
                               c_size_t]

pw_core_disconnect = _lib.pw_core_disconnect
pw_core_disconnect.restype = c_int
pw_core_disconnect.argtypes = [POINTER(struct_pw_core)]


# Properties:
pw_properties_new_dict = _lib.pw_properties_new_dict
pw_properties_new_dict.restype = POINTER(struct_pw_properties)
pw_properties_new_dict.argtypes = [POINTER(struct_spa_dict)]

pw_properties_set = _lib.pw_properties_set
pw_properties_set.restype = c_int
pw_properties_set.argtypes = [POINTER(struct_pw_properties), c_char_p, c_char_p]

pw_properties_get = _lib.pw_properties_get
pw_properties_get.restype = c_char_p
pw_properties_get.argtypes = [POINTER(struct_pw_properties), c_char_p]

pw_properties_free = _lib.pw_properties_free
pw_properties_free.restype = None
pw_properties_free.argtypes = [POINTER(struct_pw_properties)]


# Stream events:
_pw_stream_events_destroy_t = CFUNCTYPE(None, c_void_p)
_pw_stream_events_state_changed_t = CFUNCTYPE(None, c_void_p, c_int, c_int, c_char_p)
_pw_stream_events_control_info_t = CFUNCTYPE(None, c_void_p, c_uint32, c_void_p)
_pw_stream_events_io_changed_t = CFUNCTYPE(None, c_void_p, c_uint32, c_void_p, c_size_t)
_pw_stream_events_param_changed_t = CFUNCTYPE(None, c_void_p, c_uint32, c_void_p)
_pw_stream_events_add_buffer_t = CFUNCTYPE(None, c_void_p, c_void_p)
_pw_stream_events_remove_buffer_t = CFUNCTYPE(None, c_void_p, c_void_p)
_pw_stream_events_process_t = CFUNCTYPE(None, c_void_p)
_pw_stream_events_drained_t = CFUNCTYPE(None, c_void_p)
_pw_stream_events_command_t = CFUNCTYPE(None, c_void_p, c_void_p)
_pw_stream_events_trigger_done_t = CFUNCTYPE(None, c_void_p)


class struct_pw_stream_events(Structure):
    _fields_ = [
        ('version', c_uint32),
        ('destroy', _pw_stream_events_destroy_t),
        ('state_changed', _pw_stream_events_state_changed_t),
        ('control_info', _pw_stream_events_control_info_t),
        ('io_changed', _pw_stream_events_io_changed_t),
        ('param_changed', _pw_stream_events_param_changed_t),
        ('add_buffer', _pw_stream_events_add_buffer_t),
        ('remove_buffer', _pw_stream_events_remove_buffer_t),
        ('process', _pw_stream_events_process_t),
        ('drained', _pw_stream_events_drained_t),
        ('command', _pw_stream_events_command_t),
        ('trigger_done', _pw_stream_events_trigger_done_t),
    ]


def make_stream_events(**handlers: Callable[..., Any]) -> struct_pw_stream_events:
    """Build a pw_stream_events struct wired to the given handlers.

    Callback trampolines are attached to the returned object so they stay
    alive as long as it does; retain it for the lifetime of the stream.
    """
    events = struct_pw_stream_events()
    events.version = PW_VERSION_STREAM_EVENTS
    for name, handler in handlers.items():
        callback = globals()[f'_pw_stream_events_{name}_t'](handler)
        setattr(events, name, callback)
        setattr(events, f'{name}_callback', callback)
    return events


# Stream:
pw_stream_new = _lib.pw_stream_new
pw_stream_new.restype = POINTER(struct_pw_stream)
pw_stream_new.argtypes = [POINTER(struct_pw_core), c_char_p,
                          POINTER(struct_pw_properties)]

pw_stream_destroy = _lib.pw_stream_destroy
pw_stream_destroy.restype = None
pw_stream_destroy.argtypes = [POINTER(struct_pw_stream)]

pw_stream_add_listener = _lib.pw_stream_add_listener
pw_stream_add_listener.restype = None
pw_stream_add_listener.argtypes = [POINTER(struct_pw_stream),
                                   POINTER(struct_spa_hook),
                                   POINTER(struct_pw_stream_events),
                                   c_void_p]

pw_stream_connect = _lib.pw_stream_connect
pw_stream_connect.restype = c_int
pw_stream_connect.argtypes = [POINTER(struct_pw_stream), c_int, c_uint32,
                              c_uint32, POINTER(POINTER(struct_spa_pod)),
                              c_uint32]

pw_stream_disconnect = _lib.pw_stream_disconnect
pw_stream_disconnect.restype = c_int
pw_stream_disconnect.argtypes = [POINTER(struct_pw_stream)]

pw_stream_get_state = _lib.pw_stream_get_state
pw_stream_get_state.restype = c_int
pw_stream_get_state.argtypes = [POINTER(struct_pw_stream), POINTER(c_char_p)]

pw_stream_get_node_id = _lib.pw_stream_get_node_id
pw_stream_get_node_id.restype = c_uint32
pw_stream_get_node_id.argtypes = [POINTER(struct_pw_stream)]

pw_stream_get_time_n = _lib.pw_stream_get_time_n
pw_stream_get_time_n.restype = c_int
pw_stream_get_time_n.argtypes = [POINTER(struct_pw_stream),
                                 POINTER(struct_pw_time), c_size_t]

pw_stream_get_nsec = _lib.pw_stream_get_nsec
pw_stream_get_nsec.restype = c_int64
pw_stream_get_nsec.argtypes = [POINTER(struct_pw_stream)]

pw_stream_dequeue_buffer = _lib.pw_stream_dequeue_buffer
pw_stream_dequeue_buffer.restype = POINTER(struct_pw_buffer)
pw_stream_dequeue_buffer.argtypes = [POINTER(struct_pw_stream)]

pw_stream_queue_buffer = _lib.pw_stream_queue_buffer
pw_stream_queue_buffer.restype = c_int
pw_stream_queue_buffer.argtypes = [POINTER(struct_pw_stream),
                                   POINTER(struct_pw_buffer)]

pw_stream_return_buffer = _lib.pw_stream_return_buffer
pw_stream_return_buffer.restype = c_int
pw_stream_return_buffer.argtypes = [POINTER(struct_pw_stream),
                                    POINTER(struct_pw_buffer)]

pw_stream_set_active = _lib.pw_stream_set_active
pw_stream_set_active.restype = c_int
pw_stream_set_active.argtypes = [POINTER(struct_pw_stream), c_bool]

pw_stream_flush = _lib.pw_stream_flush
pw_stream_flush.restype = c_int
pw_stream_flush.argtypes = [POINTER(struct_pw_stream), c_bool]

pw_stream_set_rate = _lib.pw_stream_set_rate
pw_stream_set_rate.restype = c_int
pw_stream_set_rate.argtypes = [POINTER(struct_pw_stream), c_double]


# Constants:
PW_DIRECTION_INPUT = 0
PW_DIRECTION_OUTPUT = 1

PW_ID_ANY = 0xFFFFFFFF

PW_STREAM_STATE_ERROR = -1
PW_STREAM_STATE_UNCONNECTED = 0
PW_STREAM_STATE_CONNECTING = 1
PW_STREAM_STATE_PAUSED = 2
PW_STREAM_STATE_STREAMING = 3

PW_STREAM_FLAG_NONE = 0
PW_STREAM_FLAG_AUTOCONNECT = 1 << 0
PW_STREAM_FLAG_INACTIVE = 1 << 1
PW_STREAM_FLAG_MAP_BUFFERS = 1 << 2
PW_STREAM_FLAG_DRIVER = 1 << 3
PW_STREAM_FLAG_RT_PROCESS = 1 << 4
PW_STREAM_FLAG_NO_CONVERT = 1 << 5
PW_STREAM_FLAG_EXCLUSIVE = 1 << 6
PW_STREAM_FLAG_DONT_RECONNECT = 1 << 7
PW_STREAM_FLAG_ALLOC_BUFFERS = 1 << 8
PW_STREAM_FLAG_TRIGGER = 1 << 9

PW_VERSION_STREAM_EVENTS = 2

# SPA types:
SPA_TYPE_None = 1
SPA_TYPE_Bool = 2
SPA_TYPE_Id = 3
SPA_TYPE_Int = 4
SPA_TYPE_Long = 5
SPA_TYPE_Float = 6
SPA_TYPE_Double = 7
SPA_TYPE_String = 8
SPA_TYPE_Bytes = 9
SPA_TYPE_Rectangle = 10
SPA_TYPE_Fraction = 11
SPA_TYPE_Bitmap = 12
SPA_TYPE_Array = 13
SPA_TYPE_Struct = 14
SPA_TYPE_Object = 15
SPA_TYPE_Sequence = 16
SPA_TYPE_Pointer = 17
SPA_TYPE_Fd = 18
SPA_TYPE_Choice = 19
SPA_TYPE_Pod = 20

SPA_TYPE_OBJECT_START = 0x40000
SPA_TYPE_OBJECT_Format = SPA_TYPE_OBJECT_START + 3

SPA_PARAM_EnumFormat = 3
SPA_PARAM_Format = 4

SPA_FORMAT_mediaType = 1
SPA_FORMAT_mediaSubtype = 2
SPA_FORMAT_START_Audio = 0x10000
SPA_FORMAT_AUDIO_format = SPA_FORMAT_START_Audio + 1
SPA_FORMAT_AUDIO_flags = SPA_FORMAT_START_Audio + 2
SPA_FORMAT_AUDIO_rate = SPA_FORMAT_START_Audio + 3
SPA_FORMAT_AUDIO_channels = SPA_FORMAT_START_Audio + 4
SPA_FORMAT_AUDIO_position = SPA_FORMAT_START_Audio + 5

SPA_MEDIA_TYPE_unknown = 0
SPA_MEDIA_TYPE_audio = 1

SPA_MEDIA_SUBTYPE_unknown = 0
SPA_MEDIA_SUBTYPE_raw = 1

SPA_AUDIO_FORMAT_UNKNOWN = 0
SPA_AUDIO_FORMAT_U8 = 0x102
SPA_AUDIO_FORMAT_S16_LE = 0x103
SPA_AUDIO_FORMAT_S16_BE = 0x104
SPA_AUDIO_FORMAT_S32_LE = 0x10B
SPA_AUDIO_FORMAT_S32_BE = 0x10C
SPA_AUDIO_FORMAT_S24_LE = 0x10F
SPA_AUDIO_FORMAT_S24_BE = 0x110
SPA_AUDIO_FORMAT_F32_LE = 0x11B
SPA_AUDIO_FORMAT_F32_BE = 0x11C

SPA_AUDIO_CHANNEL_UNKNOWN = 0
SPA_AUDIO_CHANNEL_MONO = 2
SPA_AUDIO_CHANNEL_FL = 3
SPA_AUDIO_CHANNEL_FR = 4
SPA_AUDIO_CHANNEL_FC = 5
SPA_AUDIO_CHANNEL_LFE = 6
SPA_AUDIO_CHANNEL_SL = 7
SPA_AUDIO_CHANNEL_SR = 8

SPA_AUDIO_MAX_CHANNELS = 64

SPA_POD_ALIGN = 8
SPA_POD_MAX_SIZE = 1 << 20

SPA_POD_PROP_FLAG_NONE = 0
SPA_POD_PROP_FLAG_MANDATORY = 1 << 3

# SPA data types:
SPA_DATA_MemPtr = 1

# Property keys:
PW_KEY_MEDIA_TYPE = b'media.type'
PW_KEY_MEDIA_CATEGORY = b'media.category'
PW_KEY_MEDIA_ROLE = b'media.role'
PW_KEY_NODE_NAME = b'node.name'


def make_properties(properties: Optional[dict] = None):
    """Create a new pw_properties from a dict of string pairs."""
    items = list((properties or {}).items())
    spa_items = (struct_spa_dict_item * max(len(items), 1))()
    for i, (key, value) in enumerate(items):
        spa_items[i].key = key.encode('utf-8') if isinstance(key, str) else key
        spa_items[i].value = value.encode('utf-8') if isinstance(value, str) else value

    spa_dict = struct_spa_dict(0, len(items), cast(spa_items, POINTER(struct_spa_dict_item)))
    return pw_properties_new_dict(byref(spa_dict))


def _make_enum_format_pod_bytes(media_subtype: int, audio_format: int, rate: int, channels: int) -> bytes:
    """Build the SPA POD for an EnumFormat object (audio/raw).

    This reimplements ``spa_format_audio_raw_ext_build`` from
    raw-utils.h (which itself uses ``spa_pod_builder_add`` with no
    prop flags), producing a byte-identical POD to the C builder.
    """
    if channels > SPA_AUDIO_MAX_CHANNELS:
        channels = SPA_AUDIO_MAX_CHANNELS

    def pad(buf: bytearray) -> None:
        pad_len = (-len(buf)) % SPA_POD_ALIGN
        if pad_len:
            buf.extend(b'\x00' * pad_len)

    def append_id(buf: bytearray, value: int) -> None:
        buf += struct.pack('<II I', 4, SPA_TYPE_Id, value)
        pad(buf)

    def append_int(buf: bytearray, value: int) -> None:
        buf += struct.pack('<II i', 4, SPA_TYPE_Int, value)
        pad(buf)

    buf = bytearray()
    object_start = len(buf)
    # struct spa_pod_object: pod { size, SPA_TYPE_Object }, body { type, id }
    buf += struct.pack('<IIII', 8, SPA_TYPE_Object, SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat)

    # media type + subtype as ids
    buf += struct.pack('<II', SPA_FORMAT_mediaType, SPA_POD_PROP_FLAG_NONE)
    append_id(buf, SPA_MEDIA_TYPE_audio)
    buf += struct.pack('<II', SPA_FORMAT_mediaSubtype, SPA_POD_PROP_FLAG_NONE)
    append_id(buf, media_subtype)

    # payload format
    buf += struct.pack('<II', SPA_FORMAT_AUDIO_format, SPA_POD_PROP_FLAG_NONE)
    append_id(buf, audio_format)

    # sample rate
    buf += struct.pack('<II', SPA_FORMAT_AUDIO_rate, SPA_POD_PROP_FLAG_NONE)
    append_int(buf, rate)

    # channels
    buf += struct.pack('<II', SPA_FORMAT_AUDIO_channels, SPA_POD_PROP_FLAG_NONE)
    append_int(buf, channels)

    # channel positions as an array of ids
    if channels >= 1:
        positions = _channel_positions(channels)
        buf += struct.pack('<II', SPA_FORMAT_AUDIO_position, SPA_POD_PROP_FLAG_NONE)
        n = len(positions)
        buf += struct.pack('<IIII', 8 + 4 * n, SPA_TYPE_Array, 4, SPA_TYPE_Id)
        buf += struct.pack(f'<{n}I', *positions)
        pad(buf)

    # Write back the final size of the object pod. pod.size counts only the
    # body (type + id + props), not the 8-byte pod header.
    object_size = len(buf) - object_start - 8
    struct.pack_into('<I', buf, object_start, object_size)
    return bytes(buf)


def _channel_positions(channels: int) -> list:
    """Return the standard SPA channel positions for a channel count."""
    if channels == 1:
        return [SPA_AUDIO_CHANNEL_MONO]
    if channels == 2:
        return [SPA_AUDIO_CHANNEL_FL, SPA_AUDIO_CHANNEL_FR]

    standard = [SPA_AUDIO_CHANNEL_FL, SPA_AUDIO_CHANNEL_FR, SPA_AUDIO_CHANNEL_FC,
                SPA_AUDIO_CHANNEL_LFE, SPA_AUDIO_CHANNEL_SL, SPA_AUDIO_CHANNEL_SR]
    positions = []
    while len(positions) < channels:
        positions.extend(standard)
    return positions[:channels]


def make_enum_format_pod(media_subtype: int, audio_format: int, rate: int,
                         channels: int) -> tuple:
    """Create a format POD ready to be passed to ``pw_stream_connect``.

    Returns a tuple of ``(buffer, pod_pointer)``. The caller must keep the
    buffer alive for as long as the POD is in use.
    """
    pod_bytes = _make_enum_format_pod_bytes(media_subtype, audio_format, rate, channels)
    buffer = create_string_buffer(pod_bytes)
    pod = cast(buffer, POINTER(struct_spa_pod))
    return buffer, pod
