from __future__ import annotations

import abc as _abc
import os as _os
import select as _select
import socket as _socket
import threading as _threading
import time
import weakref

from collections import defaultdict as _defaultdict
from collections import deque as _deque
from ctypes import CFUNCTYPE, POINTER, byref, c_char_p, c_int, c_int32, c_uint32, c_void_p, cast, pointer
from dataclasses import dataclass
from pathlib import Path
from struct import Struct as _Struct
from types import SimpleNamespace as _NameSpace
from typing import TYPE_CHECKING, Any, Callable
from xml.etree import ElementTree as _ElementTree
from xml.etree.ElementTree import Element, ParseError

if TYPE_CHECKING:
    from ctypes import _Pointer


from pyglet.libs.linux.wayland.lib_wayland import (
    as_proxy,
    wl_array,
    wl_display,
    wl_display_cancel_read,
    wl_display_connect,
    wl_display_connect_to_fd,
    wl_display_disconnect,
    wl_display_dispatch_pending,
    wl_display_flush,
    wl_display_prepare_read,
    wl_display_read_events,
    wl_interface,
    wl_message,
    wl_proxy,
    wl_proxy_add_listener,
    wl_proxy_destroy,
    wl_proxy_marshal,
    wl_proxy_marshal_constructor_versioned,
    wl_registry,
    wl_registry_bind,
    wl_display_get_fd,
)
from pyglet.util import debug_print


_debug_wayland = debug_print('debug_wayland')

USE_LIB_WAYLAND = True


class ObjectIDPool:
    def __init__(self, minimum: int, maximum: int) -> None:
        self._sequence = iter(range(minimum, maximum + 1))
        self._recycle_pool = _deque()

    def __next__(self) -> int:
        if self._recycle_pool:
            return self._recycle_pool.popleft()
        return next(self._sequence)

    def send(self, oid: int) -> None:
        self._recycle_pool.append(oid)


##################################
#          Exceptions
##################################


class WaylandException(BaseException):
    """Base Wayland Exception"""


class WaylandServerError(WaylandException):
    """A logical error from the Server."""


class WaylandSocketError(WaylandException, OSError):
    """Errors related to Socket IO."""


class WaylandProtocolError(WaylandException, FileNotFoundError):
    """A Protocol related error."""


##################################
#       Wayland data types
##################################


class WaylandType(_abc.ABC):
    struct: _Struct
    length: int
    value: int | float | str | bytes

    @_abc.abstractmethod
    def to_bytes(self) -> bytes:
        ...

    @classmethod
    @_abc.abstractmethod
    def from_bytes(cls, buffer: bytes) -> WaylandType:
        ...

    def __repr__(self):
        return f"{self.__class__.__name__}(length={self.length}, value={self.value})"


class Int(WaylandType):
    struct = _Struct('i')
    length = struct.size

    def __init__(self, value: int):
        self.value = value

    def to_bytes(self) -> bytes:
        return self.struct.pack(self.value)

    @classmethod
    def from_bytes(cls, buffer: bytes) -> Int:
        return cls(cls.struct.unpack(buffer[:cls.length])[0])


class UInt(WaylandType):
    struct = _Struct('I')
    length = struct.size

    def __init__(self, value: int):
        self.value = value

    def to_bytes(self) -> bytes:
        return self.struct.pack(self.value)

    @classmethod
    def from_bytes(cls, buffer: bytes) -> UInt:
        return cls(cls.struct.unpack(buffer[:cls.length])[0])


class Fixed(WaylandType):
    struct = _Struct('I')
    length = struct.size

    def __init__(self, value: int):
        self.value = value

    def to_bytes(self) -> bytes:
        return self.struct.pack((int(self.value) << 8) + int((self.value % 1.0) * 256))

    @classmethod
    def from_bytes(cls, buffer: bytes) -> Fixed:
        unpacked = cls.struct.unpack(buffer[:cls.length])[0]
        return cls((unpacked >> 8) + (unpacked & 0xFF) / 256.0)


class String(WaylandType):
    struct = _Struct('I')

    def __init__(self, text: str):
        # length uint + text length + 4byte rounding
        self.length = 4 + len(text) + (-len(text) % 4)
        self.value = text

    def to_bytes(self) -> bytes:
        string_length = len(self.value) + 1
        padding = self.length - self.struct.size
        encoded = self.value.encode()
        return self.struct.pack(string_length) + encoded.ljust(padding, b'\x00')

    @classmethod
    def from_bytes(cls, buffer: bytes) -> String:
        length = cls.struct.unpack(buffer[:4])[0]   # 32-bit integer ('I')
        text = buffer[4:4+length-1].decode()        # strip padding byte
        return cls(text)


class Array(WaylandType):
    struct = _Struct('I')

    def __init__(self, array: bytes):
        # length uint + text length + 4byte padding
        self.length = 4 + len(array) + (-len(array) % 4)
        self.value = array

    def to_bytes(self) -> bytes:
        length = len(self.value)
        padding_size = 4 - (length % 4)
        return self.struct.pack(length) + b'\x00' * padding_size

    @classmethod
    def from_bytes(cls, buffer: bytes) -> Array:
        length = cls.struct.unpack(buffer[:4])[0]      # 32-bit integer
        array = buffer[4:4+length]
        return cls(array)


class Header(WaylandType):
    struct = _Struct('IHH')
    length = struct.size

    def __init__(self, oid, opcode, size):
        self.oid = oid
        self.opcode = opcode
        self.size = size
        self.value = self.struct.pack(oid, opcode, size)

    def to_bytes(self) -> bytes:
        return self.value

    @classmethod
    def from_bytes(cls, buffer) -> Header:
        return cls(*cls.struct.unpack(buffer))

    def __repr__(self):
        return f"{self.__class__.__name__}(oid={self.oid}, opcode={self.opcode}, size={self.size})"


class Object(UInt):
    def __init__(self, value: int):
        # Optional 'allow-null' (None) as 0:
        super().__init__(value or 0)


class NewID(UInt):
    def to_bytes(self) -> bytes:
        # Special case for wl_registry.bind()
        if isinstance(self.value, bytes):
            return self.value
        return super().to_bytes()


class FD(Int):
    pass


class _ObjectSpace:
    pass


##################################
#      Wayland abstractions
##################################


class Argument:
    _type_map = {
        'int': Int,
        'uint': UInt,
        'fixed': Fixed,
        'string': String,
        'object': Object,
        'new_id': NewID,
        'array': Array,
        'fd': FD,
    }

    _ctype_map = {
        'int': c_int32,
        'uint': c_uint32,
        'fixed': c_int32,
        'string': c_char_p,
        'object': POINTER(wl_proxy),
        'new_id': POINTER(wl_proxy),
        'array': POINTER(wl_array),
        'fd': c_int,
    }

    def __init__(self, request, element):
        self._request = request
        self._element = element
        self.name = element.get('name')
        self.type_name = element.get('type')
        self.wl_type = self._type_map[self.type_name]
        self.c_type = self._ctype_map[self.type_name]

        self.summary = element.get('summary')
        self.allow_null = True if element.get('allow-null') else False

        self.interface = element.get('interface')
        self.returns_new_object = self.wl_type is NewID and self.interface

    def __call__(self, value) -> bytes:
        return self.wl_type(value).to_bytes()

    def from_bytes(self, buffer: bytes) -> WaylandType:
        return self.wl_type.from_bytes(buffer)

    def __repr__(self) -> str:
        return f"{self.name}: {self.wl_type.__name__}"


class Entry:
    def __init__(self, element):
        self.name = element.get('name')
        self.value = int(element.get('value'), 0)
        self.summary = element.get('summary')

    def __and__(self, other) -> bool:
        return self.value & other > 0

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, value={self.value})"


class Enum:
    def __init__(self, interface, element):
        self._interface = weakref.proxy(interface)
        self._element = element

        self.name = element.get('name')
        self.description = getattr(element.find('description'), 'text', "")
        self.summary = element.find('description').get('summary') if self.description else ""
        self.bitfield = True if element.get('bitfield') else False
        self.entries = [Entry(element) for element in self._element.findall('entry')]
        self.entries.sort(key=lambda e: e.value)

    def __getitem__(self, index):
        return self.entries[index]

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.name}', entries={len(self.entries)})"


class Event:
    def __init__(self, interface, element, opcode):
        self._interface = weakref.proxy(interface)
        self._element = element
        self.opcode = opcode

        self.name = element.get('name')
        self.description = getattr(element.find('description'), 'text', "")
        self.summary = element.find('description').get('summary') if self.description else ""

        self.arguments = [Argument(self, element) for element in element.findall('arg')]
        self.arg_ctypes = [arg.c_type for arg in self.arguments]
        self.arg_count = len(self.arguments)

    def __call__(self, payload: bytes, fds: bytes) -> None:
        if USE_LIB_WAYLAND:
            raise Exception("Not to be called.")
        decoded_values = []

        for arg in self.arguments:
            if arg.wl_type == FD:
                wl_type = arg.wl_type.from_bytes(fds)
                decoded_values.append(wl_type.value)
                fds = fds[wl_type.length:]
            else:
                wl_type = arg.wl_type.from_bytes(payload)
                decoded_values.append(wl_type.value)
                # trim, and continue loop:
                payload = payload[wl_type.length:]

        # signature = tuple(f"{arg.name}={value}" for arg, value in zip(self.arguments, decoded_values))
        # print(f"Event({self.name}), arguments={signature}")
        self._interface.dispatch_event(self.name, *decoded_values)

    def __repr__(self):
        args = ', '.join(f'{a.name}={a.type_name}' for a in self.arguments)
        return f"{self.__class__.__name__}(name={self.name}, opcode={self.opcode}, args=({args}))"


class Request:
    def __init__(self, interface, element, opcode):
        self._protocol = interface.protocol
        self._client = interface.protocol.client
        self.parent_oid = interface.oid
        self.opcode = opcode
        self.version = interface.version
        self._interface = weakref.proxy(interface)

        self.name = element.get('name')
        self.description = getattr(element.find('description'), 'text', "")
        self.summary = element.find('description').get('summary') if self.description else ""

        self.arguments = [Argument(self, arg) for arg in element.findall('arg')]
        self.is_constructor = any(a.get('type') == 'new_id' for a in element.findall('arg'))
        self.new_interface = next(
            (a.get('interface') for a in element.findall('arg') if a.get('type') == 'new_id'),
            None,
        )
        # TODO: attempt to update a custom signature/annotations for the __call__ method.

    def create_interface_proxy(self, name: str, *args: Any) -> None:
        interface_struct = self._protocol._interface_structures[name]
        _formated_args = []
        for arg in args:
            if isinstance(arg, int):
                _formated_args.append(c_uint32(arg))
            elif isinstance(arg, str):
                _formated_args.append(c_char_p(arg.encode()))
            elif hasattr(arg, "_proxy"):
                # It has an interface with a proxy, like wl_surface.
                _formated_args.append(cast(arg._proxy, c_void_p))
            else:
                msg = f"Unsupported arg type for {arg!r}"
                raise TypeError(msg)

        return wl_proxy_marshal_constructor_versioned(
            self._interface._proxy,
            c_uint32(self.opcode),
            byref(interface_struct),
            c_uint32(self.version),
            *_formated_args,
        )

    def _send(self, bytestring, fds) -> None:
        """Attach a Header to the payload, and send."""
        size = Header.length + len(bytestring)
        header = Header(self.parent_oid, self.opcode, size)
        # final request and file descriptor payloads:
        request = header.to_bytes() + bytestring
        self._client.socket_sendmsg(request, fds)

    def __call__(self, *args: Any) -> None | Interface:
        assert len(args) == len(self.arguments), f"expected {len(self.arguments)} arguments: {self.arguments}"

        if USE_LIB_WAYLAND:
            assert _debug_wayland(f"> request called: {self.name} : args={args}. all={self.arguments}")

            for argument, value in zip(self.arguments, args):
                if argument.returns_new_object:
                    assert _debug_wayland(
                        f"> requires new interface: {self.new_interface} value={value} : args={args}. {self.arguments}",
                    )
                    proxy = self.create_interface_proxy(self.new_interface, *args)
                    interface = self._protocol.create_interface(argument.interface, value, proxy=proxy)
                    assert _debug_wayland(f"> created interface: {interface}")
                    return interface

            assert _debug_wayland(f"> calling: {self.name} : args={args}")
            wl_proxy_marshal(self._interface._proxy, self.opcode, *args)
            return None

        # Pure socket call.
        interface = None
        bytestring = b''
        fds = b''

        for argument, value in zip(self.arguments, args):
            if argument.returns_new_object:
                interface = self._protocol.create_interface(argument.interface, value)
            if argument.wl_type is FD:
                fds += argument(value)
                continue
            bytestring += argument(value)

        self._send(bytestring, fds)
        return interface

    def __repr__(self) -> str:
        return f"{self.name}(opcode={self.opcode}, args=({', '.join(f'{a}' for a in self.arguments)}))"


class Interface:
    """Interface base class"""

    _element: Element
    protocol: Protocol
    opcode: int

    _handlers: dict

    def __init__(self, oid: int, proxy: wl_proxy | None = None) -> None:
        self.oid = oid
        self.name = self._element.get('name')
        self.version = int(self._element.get('version'), 0)

        self.description = getattr(self._element.find('description'), 'text', "")
        self.summary = self._element.find('description').get('summary') if self.description else ""

        self.enums = {element.get('name'): Enum(self, element) for element in self._element.findall('enum')}
        self.events = [Event(self, element, opc) for opc, element in enumerate(self._element.findall('event'))]
        self.event_types = [event.name for event in self.events]

        self.requests = [Request(self, elem, opcode) for opcode, elem in enumerate(self._element.findall('request'))]
        for request in self.requests:
            setattr(self, request.name, request)

        self._handlers = dict()
        for name in self.event_types:
            self._handlers[name] = []

        self._proxy = proxy

        # Keeps listener callbacks in memory when created, to prevent GC.
        self._listener_keepalive = None

    def _install_listeners(self) -> None:
        """Build and register the handlers as listeners."""
        if not USE_LIB_WAYLAND:
            return

        if not self._proxy:
            raise RuntimeError("No wl_proxy to attach listener to.")

        c_funcs = []
        wrappers = []

        for ev in self.events:
            if ev.name not in self._handlers:
                assert _debug_wayland(f"> Handler for {ev.name} not found. Using dummy function.")

                def _make_wrapper(event_name):
                    def _callback(data, proxy, *args): ...

                    return _callback
            else:
                # Wrap this since we don't use the user_data or wl_registry argument.
                def _make_wrapper(event_name):
                    handler = self._handlers[event_name]

                    def _callback(data, proxy, *args):
                        handler(*args)

                    return _callback

            # handler_func = self._handlers[ev.name]
            cb_type = CFUNCTYPE(None, c_void_p, POINTER(wl_registry), *ev.arg_ctypes)
            py_fn = _make_wrapper(ev.name)
            c_fn = cb_type(py_fn)
            # c_fn = cb_type(handler_func)
            assert _debug_wayland(
                f"> {self}: creating cb for: {ev.name} : {self._handlers.get(ev.name)} | ctype: {cb_type}",
            )
            wrappers.append(c_fn)
            c_funcs.append(cast(c_fn, c_void_p).value)

        # Pack into void* array in event order
        arr = (c_void_p * len(c_funcs))()
        for i, fn_ptr in enumerate(c_funcs):
            arr[i] = fn_ptr

        rc = wl_proxy_add_listener(self._proxy, arr, None)
        if rc != 0:
            msg = f"wl_proxy_add_listener failed for {self.name}, rc={rc}"
            raise RuntimeError(msg)

        self._listener_keepalive = (arr, wrappers)

    def dispatch_event(self, name: str, *args: Any) -> None:
        handler = self._handlers[name]
        handler(*args)

    def set_handler(self, name: str, handler: Callable) -> None:
        assert self._listener_keepalive is None, "You have already set a handler. For multiple types, use set_handlers."
        self._handlers[name] = handler
        self._install_listeners()

    def set_handlers(self, **handler_funcs: Callable) -> None:
        assert self._listener_keepalive is None, "You have already set handlers."
        self._handlers = handler_funcs
        self._install_listeners()

    def set_handlers_dict(self, handlers_dict: dict[str, Callable]) -> None:
        """Same as set_handlers but takes a dict.

        Used to prevent clashing of namespaces with kwargs, such as "global" for wl_registry.
        """
        self._handlers = handlers_dict
        self._install_listeners()

    def remove_handler(self, name: str) -> None:
        if name in self._handlers:
            del self._handlers[name]

    def delete(self) -> None:
        if self._proxy:
            wl_proxy_destroy(self._proxy)
            self._proxy = None
        if self._listener_keepalive:
            self._listener_keepalive = None

    def __del__(self) -> None:
        self.delete()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(oid={self.oid}, opcode={self.opcode})"


def _generate_wl_interface(interface_element: Element, all_interfaces: dict) -> wl_interface:
    """Convert <interface> XML element into ctypes structs."""

    name = interface_element.attrib["name"]
    version = int(interface_element.attrib.get("version", 1))

    # Converts requests and events elements to ctypes pointers
    def build_messages(elements: list[Element]) -> Array[wl_message]:
        messages = (wl_message * len(elements))()
        for i, elem in enumerate(elements):
            msg_name = elem.attrib["name"].encode("utf-8")
            since = elem.attrib.get("since")
            sig = str(since).encode("utf-8") if since else b""
            arg_elems = elem.findall("arg")
            for arg in arg_elems:
                wl_type = arg.attrib["type"]
                nullable = arg.attrib.get("allow-null") == "true"

                if wl_type == "new_id":
                    iface_name = arg.attrib.get("interface")
                    if iface_name:
                        # If it has an interface name, it behaves like normal object
                        sig += (b"?" if nullable else b"") + b"n"
                    else:
                        # No interface name for new_id?  Dynamic new_id expands to su before n
                        # For example wl_registry's XML shows only 2 args, but is 4 in official.
                        sig += (b"?" if nullable else b"") + b"sun"
                    continue

                sig += (b"?" if nullable else b"") + {
                    "int": b"i",
                    "uint": b"u",
                    "fixed": b"f",
                    "string": b"s",
                    "object": b"o",
                    "new_id": b"n",
                    "array": b"a",
                    "fd": b"h",
                }[wl_type]

            n_args = len(arg_elems)
            types_array = (POINTER(wl_interface) * n_args)()

            # fill any object/new_id args with pointers if known
            for j, arg in enumerate(arg_elems):
                wl_type = arg.attrib["type"]
                if wl_type in ("object", "new_id"):
                    iface_name = arg.attrib.get("interface")
                    if iface_name and iface_name in all_interfaces:
                        types_array[j] = cast(pointer(all_interfaces[iface_name]), POINTER(wl_interface))
                    else:
                        types_array[j] = POINTER(wl_interface)()
                else:
                    types_array[j] = POINTER(wl_interface)()

            # always non-NULL even if len==0
            types_ptr = cast(types_array, c_void_p) if n_args else c_void_p(0)
            msg = wl_message(msg_name, sig, types_ptr)
            msg._types_array = types_array  # pin lifetime
            messages[i] = msg

        return messages

    # Build requests and events
    requests = interface_element.findall("request")
    events = interface_element.findall("event")

    req_array = build_messages(requests)
    evt_array = build_messages(events)

    iface = wl_interface(
        name=name.encode(),
        version=version,
        method_count=len(requests),
        methods=req_array,
        event_count=len(events),
        events=evt_array,
    )

    # Cache into all_interfaces for lookups
    all_interfaces[name] = iface
    return iface


class ClientDisplay(Interface):
    def __init__(self, oid: int, proxy=None) -> None:
        super().__init__(oid, proxy)
        assert proxy is None, "Should not be created with proxy."
        self._display = None
        self._proxy = None

    def connect(self, path: str | Path | None = None, fd: int | None = None) -> None:
        if fd is not None:
            self._display = wl_display_connect_to_fd(fd)
            if not self._display:
                raise WaylandException("Could not connect to Wayland Display.")
        else:
            if isinstance(path, str):
                self._display = wl_display_connect(path.encode())
            else:
                # Should connect to default.
                self._display = wl_display_connect(None)
            if not self._display:
                raise WaylandException("Could not connect to Wayland Display.")
        self._proxy = as_proxy(self._display)

    @property
    def display(self) -> _Pointer[wl_display]:
        return self._display

    def disconnect(self) -> None:
        if self._display:
            wl_display_disconnect(self._display)
            self._display = None
            wl_proxy_destroy(self._proxy)
            self._proxy = None

    def _install_listeners(self) -> None:
        """The wl_display object is special and does not support listeners added through wl_proxy_add_listener()."""
        if USE_LIB_WAYLAND:
            raise WaylandException("Wayland Client Display does not support listeners. Use WAYLAND_DEBUG environment variable.")


_special_classes = {
    "wl_display": ClientDisplay,  # Creation differs than normal interfaces.
}


class Protocol:
    def __init__(self, client: Client, filename: str) -> None:
        """A Wayland Protocol

        Given a Wayland Protocol .xml file, this class will dynamically
        introspect and define custom classes for all Interfaces defined
        within. This class should not be instantiated directly. It will
        automatically be created as part of a :py:class:`~wayland.Client`
        instance.

        Args:
            client: The parent Client to which this Protocol belongs.
            filename: The .xml file that contains the Protocol definition.
        """
        try:
            self._root = _ElementTree.parse(filename).getroot()
        except (FileNotFoundError, ParseError) as e:
            raise WaylandProtocolError(e)

        self.client = client
        self.name = self._root.get('name')
        self.copyright = getattr(self._root.find('copyright'), 'text', "")
        assert _debug_wayland(f"> {self}: initializing...")

        self._interface_classes = {}
        self._interface_structures = {}

        # Iterate over all defined interfaces and dynamically create custom Interface
        # classes using the _InterfaceBase class. Opcodes are determined by enumeration order.
        for i, element in enumerate(self._root.findall('interface')):
            name = element.get('name')
            interface_base_class = _special_classes.get(name, Interface)
            interface_class = type(name, (interface_base_class,), {'protocol': self, '_element': element, 'opcode': i})
            self._interface_classes[name] = interface_class
            assert _debug_wayland(f"   * found interface: '{name}'")
            if USE_LIB_WAYLAND:
                iface_struct = _generate_wl_interface(element, self._interface_structures)
                assert _debug_wayland(f"    * generated: {name} -> {iface_struct}")

    def bind_interface(self, name: str, index: int = 0) -> Interface:
        """Create an Interface instance & bind it to a global object.

        In case there are multiple global objects with the same interface
        name, an ``index`` can be provided.

        Args:
            name: The interface name to bind.
            index: The index of the global to bind, if more than one.
        """
        # Find a global match, and create a local instance for it.
        interface_global = self.client.globals[name][index]
        iface_name = interface_global.interface.decode()
        # Inform the server of the new relationship:
        # Request...
        if USE_LIB_WAYLAND:
            proxy = interface_global.bind_proxy(self._interface_structures[iface_name])
        else:
            proxy = None

        interface_instance = self.create_interface(iface_name, proxy=proxy)

        # Will cause a leak if uncommented. Just keep your instance alive.
        # self.client.bound_globals[interface_global.name] = interface_instance

        if not USE_LIB_WAYLAND:
            _string = String(name).to_bytes()
            _version = UInt(interface_global.version).to_bytes()
            _new_id = NewID(interface_instance.oid).to_bytes()
            combined_new_id = _string + _version + _new_id
            self.client.wl_registry.bind(interface_global.name, combined_new_id)

        assert _debug_wayland(f"> {self}.bind_interface: global {name}")
        return interface_instance

    def create_interface(self, name: str, oid: int | None = None, proxy = None) -> Interface:
        """Create an Interface instance by name.

        Args:
            name: The Interface name.
            oid: If not provided, an oid will be generated by the Client.
            proxy:
        """
        if name not in self._interface_classes:
            raise WaylandProtocolError(f"The '{self.name}' Protocol does not define an interface named '{name}'")

        oid = oid or next(self.client.oid_pool)
        interface = self._interface_classes[name](oid=oid, proxy=proxy)
        assert _debug_wayland(f"> {self}.create_interface: {interface}")
        #self.client._oid_interface_map[oid] = interface
        return interface

    # def delete_interface(self, oid: int) -> None:
    #     """Delete an Interface, by its oid.
    #
    #     Args:
    #         oid: The object ID (oid) of the interface.
    #     """
    #     interface = self.client._oid_interface_map.pop(oid)
    #     self.client.oid_pool.send(oid)  # to reuse later
    #     assert _debug_wayland(f"> {self}.delete_interface: {interface}")

    @property
    def interface_names(self) -> list[str]:
        return list(self._interface_classes)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.name}')"


@dataclass
class GlobalObject:
    registry: _Pointer[wl_registry]
    name: int
    interface: bytes
    version: int

    def bind_proxy(self, wl_interface_struct: wl_interface) -> _Pointer[wl_proxy]:
        return wl_registry_bind(self.registry, self.name, byref(wl_interface_struct), self.interface, self.version)


##################################
#           User API
##################################


class Client:
    """Wayland Client

    The Client class establishes a connection to the Wayland domain socket.
    As per the Wayland specification, the `WAYLAND_DISPLAY` environmental
    variable is queried for the endpoint name. If this is an absolute path,
    it is used as-is. If not, the final socket path will be made by joining
    the ``XDG_RUNTIME_DIR`` + ``WAYLAND_DISPLAY`` environmental variables.

    To create an instance of this class, at least one Wayland Protocol file
    must be provided. Protocol files are XML, and are generally found under
    the ``/usr/share/wayland*`` directories. At a minimum, the base Wayland
    protocol file (``wayland.xml``) is required.

    When instantiated, the Client automatically connects to the socket and
    creates the main Display (``wl_display``) interface, which is available
    as ``Client.wl_display``.
    """
    _sock: _socket.socket | None

    def __init__(self, *protocols: str) -> None:
        """Create a Wayland Client connection.

        Args:
            *protocols: The file path(s) to one or more <protocol>.xml files.
        """
        assert protocols, (
            "At a minimum you must provide at least a wayland.xml "
            "protocol file, commonly '/usr/share/wayland/wayland.xml'."
        )
        self._sock = None
        self._recv_buffer = b""

        self._endpoint = Path(_os.environ.get('WAYLAND_DISPLAY', default='wayland-0'))

        if self._endpoint.is_absolute():
            path = self._endpoint
        else:
            _runtime_dir = Path(_os.environ.get('XDG_RUNTIME_DIR', default='/run/user/1000'))
            path = _runtime_dir / self._endpoint

        assert _debug_wayland(f"endpoint: {path}")

        if not path.exists():
            msg = f"Wayland endpoint not found: {path}"
            raise WaylandSocketError(msg)

        # Client side object ID generation:
        self.oid_pool = ObjectIDPool(minimum=1, maximum=0xFEFFFFFF)

        self._oid_interface_map: dict[int, Interface] = {}  # oid: Interface

        self.globals: dict[str, list[GlobalObject]] = _defaultdict(list)  # interface_name: [GlobalObject]
        self.global_interface_map: dict[int, str] = {}  # global_name: interface_name
        # self.bound_globals: dict[int, Interface] = {}  # global_name: interface_instance

        self.protocol_dict = {p.name: p for p in [Protocol(self, filename) for filename in protocols]}
        self.protocols = _NameSpace(**self.protocol_dict)

        assert 'wayland' in self.protocol_dict, "You must provide at minimum a wayland.xml protocol file."

        # Create global display interface:
        self.wl_display: ClientDisplay = self.protocols.wayland.create_interface(name='wl_display')

        if USE_LIB_WAYLAND:
            # Can use an opened socket if you want to read from it too, but you CANNOT write to it.
            # self._sock = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM, 0)
            # self._sock.connect(path)
            # self.wl_display.connect(fd=self._sock.fileno())

            self.wl_display.connect(self._endpoint)
            self.wl_display_p = cast(self.wl_display._display, c_void_p)
        else:
            self._sock = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM, 0)
            self._sock.connect(path.as_posix())
            assert _debug_wayland(f"connected to: {self._sock.getpeername()}")
            # !!! Not supported with lib Wayland.
            self.wl_display.set_handlers(error=self._wl_display_error_handler,
                                         delete_id=self._wl_display_delete_id_handler)

        # Create global registry:
        self.wl_registry: Interface = self.wl_display.get_registry(next(self.oid_pool))
        self.wl_registry.set_handlers_dict(
            {"global": self._wl_registry_global, "global_remove": self._wl_registry_global_remove},
        )

        self._sync_done = _threading.Event()
        self._thread_running = _threading.Event()

        self._receive_loop_method = self._receive_loop if USE_LIB_WAYLAND else self._receive_loop_socket
        self._receive_thread = _threading.Thread(target=self._receive_loop_method, daemon=True)
        self._receive_thread.start()
        self._thread_running.wait()

    def _receive_loop(self) -> None:
        """A threaded method for continuously reading Server messages."""
        self._thread_running.set()
        dpy = self.wl_display._display
        fd = wl_display_get_fd(dpy)
        while self._thread_running.is_set():
            # Prepare to read. if it returns -1, just dispatch pending
            if wl_display_prepare_read(dpy) != 0:
                wl_display_dispatch_pending(dpy)
                continue

            # Flush any queued requests
            wl_display_flush(dpy)

            # Wake immediately if fd is readable, otherwise poll once per 0.005 seconds.
            _, _, _ = _select.select([fd], [], [], 0.005)

            if wl_display_read_events(dpy) != 0:
                wl_display_cancel_read(dpy)  # errors
            wl_display_dispatch_pending(dpy)

    def sync(self) -> None:
        """Helper shortcut for wl_display.sync calls.

        This method calls ``wl_display.sync``, and obtains a new ``wl_callback``
        object. It then blocks until the ``wl_callback.done`` event is received
        from the server, ensuring that all prior events are received as well.
        """
        def _wl_display_sync_handler(serial):
            self._sync_done.set()

        wl_callback = self.wl_display.sync(next(self.oid_pool))
        wl_callback.set_handler('done', _wl_display_sync_handler)

        if self._sync_done.wait(5.0) is False:
            raise WaylandSocketError("wl_display.sync timed out")
        self._sync_done.clear()

    def socket_sendmsg(self, request: bytes, fds: bytes) -> None:
        """Send prepared requests and (optional) file descriptors to the server.

        This method expects the data to be pre-packed into bytestrings. This usually
        means preparing the appropriate Header and payload (WaylandTypes), and using
        their ``to_bytes`` methods to pack them into their raw byte representations.
        If a request is also passing file descriptors, they should be separately packed
        into the ``fds`` bytestring as file descriptors are sent as ancillary data.

        Args:
            request: a raw bytestring representing a concatenated Header & Request.
            fds: a raw bytestring representing file descriptors.
        """
        self._sock.sendmsg([request], [(_socket.SOL_SOCKET, _socket.SCM_RIGHTS, fds)])

    def _receive_loop_socket(self) -> None:
        """A threaded method for continuously reading Server messages."""
        self._thread_running.set()
        while self._thread_running.is_set():
            self._receive_socket()

    def _receive_socket(self) -> None:
        """Receive and process Wayland Events (messages) from the server."""
        _header_len = Header.length

        try:
            new_data, ancdata, msg_flags, _ = self._sock.recvmsg(4096, _socket.CMSG_SPACE(64))
        except ConnectionError:
            raise WaylandSocketError("Socket is closed")

        if new_data == b"":
            raise WaylandSocketError("Socket is dead")

        # Include any leftover partial data:
        data = self._recv_buffer + new_data
        fds = b"".join([fds for _, _, fds in ancdata])

        # Parse the events in chunks:
        while len(data) > _header_len:
            # The first part of the data is the header:
            header = Header.from_bytes(data[:_header_len])

            # Do we have enough data for the full message?
            if len(data) < header.size:
                print("WARNING! Pending FDS!", fds)
                break

            # - find the matching object (interface) from the header.oid
            # - find the matching event by its header.opcode
            # - pass the raw payload into the event, which will decode it
            # TODO: handle "dead" interfaces:
            interface = self._oid_interface_map[header.oid]
            event = interface.events[header.opcode]
            event(data[_header_len:header.size], fds)

            # trim, and continue loop
            data = data[header.size:]

        # Keep leftover for next time:
        self._recv_buffer = data

    def __del__(self) -> None:
        self._thread_running.clear()
        if hasattr(self, '_sock') and self._sock:
            self._sock.close()
            self._sock = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(socket='{self._sock.getpeername() if self._sock else self._endpoint}')"

    # Event handlers

    def _wl_display_delete_id_handler(self, oid):
        self.protocols.wayland.delete_interface(oid)

    def _wl_display_error_handler(self, oid: int, code: int, message: str):
        try:
            error_enum = self._oid_interface_map[oid].enums['error']
            error_entry = error_enum.entries[code]
            raise WaylandServerError(f"'{error_entry.name}': {error_entry.summary}; {message}.")
        except (IndexError, KeyError):
            raise WaylandServerError(f"oid={oid}, code={code}, message={message}")

    def _wl_registry_global(self, global_name_id, interface_name: str | bytes, version):
        # wayland lib sends as bytes, socket reader sends as string.
        fmt_interface_name = interface_name.decode()
        assert _debug_wayland(f"wl_registry global: {global_name_id}, {fmt_interface_name}, {version}")
        self.globals[fmt_interface_name].append(GlobalObject(self.wl_registry._proxy, global_name_id, interface_name, version))
        self.global_interface_map[global_name_id] = fmt_interface_name

    def _wl_registry_global_remove(self, global_name):
        assert _debug_wayland(f"wl_registry global_remove: {global_name}")
        interface = self.global_interface_map.pop(global_name)
        self.globals[interface] = [g for g in self.globals[interface] if g.name != global_name]

        if instance := self.bound_globals.pop(global_name, None):
            # TODO:
            pass
