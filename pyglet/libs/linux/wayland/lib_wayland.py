from __future__ import annotations

from ctypes import POINTER, Structure, _Pointer, addressof, c_char_p, c_int, c_size_t, c_uint32, c_void_p, cast, sizeof

import pyglet.lib

_lib_wl = pyglet.lib.load_library("libwayland-client.so")


class wl_proxy(Structure):
    pass


class wl_interface(Structure):

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name.decode()}, version={self.version}, methods={self.method_count}, events={self.event_count})"


class wl_message(Structure):
    _fields_ = [
        ("name", c_char_p),
        ("signature", c_char_p),
        ("types", c_void_p),  # POINTER(POINTER(wl_interface))),
    ]


wl_interface._fields_ = [
    ("name", c_char_p),
    ("version", c_int),
    ("method_count", c_int),
    ("methods", POINTER(wl_message)),  # not POINTER(c_void_p)!
    ("event_count", c_int),
    ("events", POINTER(wl_message)),
]


class wl_display(Structure): pass


class wl_registry(Structure): pass


class wl_compositor(Structure): pass


class wl_surface(Structure): pass


class wl_event_queue(Structure): pass


class wl_array(Structure):
    _fields_ = [
        ("size", c_size_t),
        ("alloc", c_size_t),
        ("data", c_void_p),
    ]


def as_proxy(ptr: c_void_p) -> _Pointer[wl_proxy]:
    return cast(ptr, POINTER(wl_proxy))


WL_DISPLAY_SYNC = 0
WL_DISPLAY_GET_REGISTRY = 1
WL_REGISTRY_BIND = 0

wl_proxy_get_id = _lib_wl.wl_proxy_get_id
wl_proxy_get_id.restype = c_uint32
wl_proxy_get_id.argtypes = [POINTER(wl_proxy)]

wl_proxy_destroy = _lib_wl.wl_proxy_destroy
wl_proxy_destroy.restype = None
wl_proxy_destroy.argtypes = [POINTER(wl_proxy)]

wl_proxy_add_listener = _lib_wl.wl_proxy_add_listener
wl_proxy_add_listener.restype = c_int
wl_proxy_add_listener.argtypes = [c_void_p, POINTER(c_void_p), c_void_p]

wl_display_get_fd = _lib_wl.wl_display_get_fd
wl_display_get_fd.restype = c_int
wl_display_get_fd.argtypes = [POINTER(wl_display)]

wl_display_flush = _lib_wl.wl_display_flush
wl_display_flush.restype = c_int
wl_display_flush.argtypes = [POINTER(wl_display)]

wl_display_dispatch = _lib_wl.wl_display_dispatch
wl_display_dispatch.restype = c_int
wl_display_dispatch.argtypes = [POINTER(wl_display)]

wl_display_dispatch_pending = _lib_wl.wl_display_dispatch_pending
wl_display_dispatch_pending.restype = c_int
wl_display_dispatch_pending.argtypes = [POINTER(wl_display)]

wl_display_prepare_read = _lib_wl.wl_display_prepare_read
wl_display_prepare_read.restype = c_int
wl_display_prepare_read.argtypes = [POINTER(wl_display)]

wl_display_cancel_read = _lib_wl.wl_display_cancel_read
wl_display_cancel_read.restype = None
wl_display_cancel_read.argtypes = [POINTER(wl_display)]

wl_display_read_events = _lib_wl.wl_display_read_events
wl_display_read_events.restype = c_int
wl_display_read_events.argtypes = [POINTER(wl_display)]

wl_display_roundtrip = _lib_wl.wl_display_roundtrip
wl_display_roundtrip.restype = c_int
wl_display_roundtrip.argtypes = [POINTER(wl_display)]

wl_display_disconnect = _lib_wl.wl_display_disconnect
wl_display_disconnect.restype = None
wl_display_disconnect.argtypes = [POINTER(wl_display)]

wl_display_connect = _lib_wl.wl_display_connect
wl_display_connect.restype = POINTER(wl_display)
wl_display_connect.argtypes = [c_char_p]

wl_display_connect_to_fd = _lib_wl.wl_display_connect_to_fd
wl_display_connect_to_fd.restype = POINTER(wl_display)
wl_display_connect_to_fd.argtypes = [c_int]

wl_display_create_queue = _lib_wl.wl_display_create_queue
wl_display_create_queue.restype = POINTER(wl_event_queue)
wl_display_create_queue.argtypes = [POINTER(wl_display)]

wl_display_get_error = _lib_wl.wl_display_get_error
wl_display_get_error.restype = c_int
wl_display_get_error.argtypes = [POINTER(wl_display)]

wl_display_get_protocol_error = _lib_wl.wl_display_get_protocol_error
wl_display_get_protocol_error.restype = c_uint32
wl_display_get_protocol_error.argtypes = [POINTER(wl_display), POINTER(POINTER(wl_interface)), POINTER(c_int)]

wl_display_dispatch_queue = _lib_wl.wl_display_dispatch_queue
wl_display_dispatch_queue.restype = c_int
wl_display_dispatch_queue.argtypes = [POINTER(wl_display),
                                      POINTER(wl_event_queue)]

wl_display_dispatch_queue_pending = _lib_wl.wl_display_dispatch_queue_pending
wl_display_dispatch_queue_pending.restype = c_int
wl_display_dispatch_queue_pending.argtypes = [POINTER(wl_display),
                                              POINTER(wl_event_queue)]

wl_display_prepare_read_queue = _lib_wl.wl_display_prepare_read_queue
wl_display_prepare_read_queue.restype = c_int
wl_display_prepare_read_queue.argtypes = [POINTER(wl_display),
                                          POINTER(wl_event_queue)]

wl_proxy_marshal_constructor = _lib_wl.wl_proxy_marshal_constructor
# Args are variadic, setting types may cause issues...
# wl_proxy_marshal_constructor.argtypes = [POINTER(wl_proxy), c_uint32, POINTER(wl_interface)]
wl_proxy_marshal_constructor.restype = POINTER(wl_proxy)

wl_proxy_marshal = _lib_wl.wl_proxy_marshal
wl_proxy_marshal.restype = None
# Args are variadic, setting types may cause issues...

wl_proxy_marshal_constructor_versioned = _lib_wl.wl_proxy_marshal_constructor_versioned
wl_proxy_marshal_constructor_versioned.restype = POINTER(wl_proxy)
# Args are variadic, setting types may cause issues...
# wl_proxy_marshal_constructor_versioned.argtypes = [POINTER(wl_proxy), c_uint32, POINTER(wl_interface), c_uint32]

wl_display_roundtrip = _lib_wl.wl_display_roundtrip
wl_display_roundtrip.argtypes = [c_void_p]
wl_display_roundtrip.restype = c_int


def wl_interface_object(name: str) -> wl_interface:
    return wl_interface.in_dll(_lib_wl, f"{name}_interface")


def wl_registry_bind(wl_registry_ptr, name, interface, interface_name, version):
    wl_registry_proxy = wl_registry_ptr
    return wl_proxy_marshal_constructor_versioned(
        wl_registry_proxy,
        c_uint32(WL_REGISTRY_BIND),
        interface,
        c_uint32(version),
        c_uint32(name),
        c_char_p(interface_name),
        c_uint32(version),
    )


def dump_iface(iface: wl_interface):
    """Debugging..."""
    print(f"--- {iface.name} ---")
    print("addr:", hex(addressof(iface)))
    print("sizeof:", sizeof(iface))
    print("name:", iface.name)
    print("version:", int(iface.version))
    print("method_count:", int(iface.method_count))
    print("methods ptr:", bool(iface.methods))
    print("event_count:", int(iface.event_count))
    print("events ptr:", bool(iface.events))
    if bool(iface.events):
        for i in range(iface.event_count):
            msg = iface.events[i]
            print(f"  event[{i}] name={msg.name} sig={msg.signature} types={msg.types}")
    if bool(iface.methods):
        for i in range(iface.method_count):
            msg = iface.methods[i]
            print(f"  method[{i}] name={msg.name} sig={msg.signature} types={msg.types}")
    print("----------------")
