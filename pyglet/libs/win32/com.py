"""Minimal Windows COM interface.

Allows pyglet to use COM interfaces on Windows without comtypes.  Unlike
comtypes, this module does not provide property interfaces, read typelibs,
nice-ify return values.  We don't need anything that sophisticated to work with COM's.

Interfaces should derive from pIUnknown if their implementation is returned by the COM.
The Python COM interfaces are actually pointers to the implementation (take note
when translating methods that take an interface as argument).
(example: A Double Pointer is simply POINTER(MyInterface) as pInterface is already a POINTER.)

Interfaces can define methods::

    class IDirectSound8(com.pIUnknown):
        _methods_ = [
            ('CreateSoundBuffer', com.STDMETHOD()),
            ('GetCaps', com.STDMETHOD(LPDSCAPS)),
            ...
        ]

Only use METHOD, STDMETHOD or VOIDMETHOD for the method types (not ordinary ctypes
function types).  The 'this' pointer is bound automatically... e.g., call::

    device = IDirectSound8()
    DirectSoundCreate8(None, ctypes.byref(device), None)

    caps = DSCAPS()
    device.GetCaps(caps)

Because STDMETHODs use HRESULT as the return type, there is no need to check
the return value.

Don't forget to manually manage memory... call Release() when you're done with
an interface.
"""

import sys
import ctypes

from pyglet.util import debug_print

_debug_com = debug_print('debug_com')

if sys.platform != 'win32':
    raise ImportError('pyglet.libs.win32.com requires a Windows build of Python')


class GUID(ctypes.Structure):
    _fields_ = [
        ('Data1', ctypes.c_ulong),
        ('Data2', ctypes.c_ushort),
        ('Data3', ctypes.c_ushort),
        ('Data4', ctypes.c_ubyte * 8),
    ]

    def __init__(self, l, w1, w2, b1, b2, b3, b4, b5, b6, b7, b8):
        self.Data1 = l
        self.Data2 = w1
        self.Data3 = w2
        self.Data4[:] = (b1, b2, b3, b4, b5, b6, b7, b8)

    def __repr__(self):
        b1, b2, b3, b4, b5, b6, b7, b8 = self.Data4
        return 'GUID(%x, %x, %x, %x, %x, %x, %x, %x, %x, %x, %x)' % (
            self.Data1, self.Data2, self.Data3, b1, b2, b3, b4, b5, b6, b7, b8)

    def __eq__(self, other):
        return isinstance(other, GUID) and bytes(self) == bytes(other)

    def __hash__(self):
        return hash(bytes(self))


LPGUID = ctypes.POINTER(GUID)
IID = GUID
REFIID = ctypes.POINTER(IID)

S_OK = 0x00000000
E_NOTIMPL = 0x80004001
E_NOINTERFACE = 0x80004002


class METHOD:
    """COM method."""

    def __init__(self, restype, *args):
        self.restype = restype
        self.argtypes = args

        self.prototype = ctypes.WINFUNCTYPE(self.restype, *self.argtypes)
        self.direct_prototype = ctypes.WINFUNCTYPE(self.restype, ctypes.c_void_p, *self.argtypes)

    def get_com_proxy(self, i, name):
        return self.prototype(i, name)


class STDMETHOD(METHOD):
    """COM method with HRESULT return value."""

    def __init__(self, *args):
        super().__init__(ctypes.HRESULT, *args)


class VOIDMETHOD(METHOD):
    """COM method with no return value."""

    def __init__(self, *args):
        super().__init__(None, *args)


_DummyPointerType = ctypes.POINTER(ctypes.c_int)
_PointerMeta = type(_DummyPointerType)
_StructMeta = type(ctypes.Structure)


class _InterfaceMeta(_StructMeta):
    def __new__(cls, name, bases, dct, /, create_pointer_type=True):
        if len(bases) > 1:
            assert _debug_com(f"Ignoring {len(bases) - 1} bases on {name}")
            bases = (bases[0],)

        if not '_methods_' in dct:
            dct['_methods_'] = ()

        inh_methods = []
        if bases[0] is not ctypes.Structure:  # Method does not exist for first definition below
            for interface_type in (bases[0].get_interface_inheritance()):
                inh_methods.extend(interface_type.__dict__['_methods_'])

        inh_methods = tuple(inh_methods)
        new_methods = tuple(dct['_methods_'])

        vtbl_own_offset = len(inh_methods)

        all_methods = tuple(inh_methods) + new_methods
        for i, (method_name, mt) in enumerate(all_methods):
            assert _debug_com(f"{name}[{i}]: {method_name}: "
                              f"{(', '.join(t.__name__ for t in mt.argtypes) or 'void')} -> "
                              f"{'void' if mt.restype is None else mt.restype.__name__}")

        vtbl_struct_type = _StructMeta(f"Vtable_{name}",
                                       (ctypes.Structure,),
                                       {'_fields_': [(n, x.direct_prototype) for n, x in all_methods]})
        dct['_vtbl_struct_type'] = vtbl_struct_type
        dct['vtbl_own_offset'] = vtbl_own_offset

        dct['_fields_'] = (('vtbl_ptr', ctypes.POINTER(vtbl_struct_type)),)

        return super().__new__(cls, name, bases, dct)

    def __init__(self, name, bases, dct, /, create_pointer_type=True):
        super().__init__(name, bases, dct)

        if create_pointer_type:
            # Unless this is the construction of `Interface` or we're already being created
            # from a pInterface subclass as a helper interface, create a special
            # _pInterfaceMeta-based subclass so a link is created in the ctypes pointer cache
            _pInterfaceMeta(f"p{name}", (ctypes.POINTER(bases[0]),), {'_type_': self})


class _pInterfaceMeta(_PointerMeta):
    def __new__(cls, name, bases, dct):
        # Interfaces can also be declared by inheritance of pInterface subclasses.
        # If this happens, create the interface and then become pointer to its struct.

        target = dct.get('_type_', None)
        # If we weren't created due to an Interface subclass definition (don't have a _type_),
        # just define that Interface subclass from our base's _type_
        if target is None:
            interface_base = bases[0]._type_

            # Create corresponding interface type and then set it as target
            target = _InterfaceMeta(f"_{name}_HelperInterface",
                                    (interface_base,),
                                    {'_methods_': dct.get('_methods_', ())},
                                    create_pointer_type=False)
            dct['_type_'] = target

        # Create method proxies that will forward ourselves into the interface's methods
        for i, (method_name, method) in enumerate(target._methods_):
            m = method.get_com_proxy(i + target.vtbl_own_offset, method_name)
            def pinterface_method_forward(self, *args, _m=m, _i=i):
                assert _debug_com(f'Calling COM {_i} of {target.__name__} ({_m})[{method_name}] through '
                                  f'pointer: ({", ".join(map(repr, (self, *args)))})')
                return _m(self, *args)
            dct[method_name] = pinterface_method_forward

        pointer_type = super().__new__(cls, name, bases, dct)

        # Hack selves into the ctypes pointer cache so all uses of `ctypes.POINTER` on the
        # interface type will yield it instead of the inflexible standard pointer type.
        # NOTE: This is done pretty much exclusively to help convert COMObjects.
        # Some additional work from callers like
        # RegisterCallback(callback_obj.as_interface(ICallback))
        # instead of
        # RegisterCallback(callback_obj)
        # could make it obsolete.
        from ctypes import _pointer_type_cache
        _pointer_type_cache[target] = pointer_type

        return pointer_type


class Interface(ctypes.Structure, metaclass=_InterfaceMeta, create_pointer_type=False):
    @classmethod
    def get_interface_inheritance(cls):
        """Returns the types of all interfaces implemented by this interface, up to but not
        including the base `Interface`.
        `Interface` does not represent an actual interface, but merely the base concept of
        them, so viewing it as part of an interface's inheritance chain is meaningless.
        """
        return cls.__mro__[:cls.__mro__.index(Interface)]


class pInterface(_DummyPointerType, metaclass=_pInterfaceMeta):
    _type_ = Interface

    @classmethod
    def from_param(cls, obj):
        """When dealing with a COMObject, pry a fitting interface out of it"""

        if not isinstance(obj, COMObject):
            return obj

        return obj.as_interface(cls._type_)


class IUnknown(Interface):
    _methods_ = [
        ('QueryInterface', STDMETHOD(REFIID, ctypes.c_void_p)),
        ('AddRef', METHOD(ctypes.c_int)),
        ('Release', METHOD(ctypes.c_int)),
    ]


class pIUnknown(pInterface):
    _methods_ = [
        ('QueryInterface', STDMETHOD(REFIID, ctypes.c_void_p)),
        ('AddRef', METHOD(ctypes.c_int)),
        ('Release', METHOD(ctypes.c_int)),
    ]


def _missing_impl(interface_name, method_name):
    """Create a callback returning E_NOTIMPL for methods not present on a COMObject."""

    def missing_cb_func(*_):
        assert _debug_com(f"Non-implemented method {method_name} called in {interface_name}")
        return E_NOTIMPL

    return missing_cb_func


def _found_impl(interface_name, method_name, method_func, self_distance):
    """If a method was found in class, create a callback extracting self from the struct
    pointer.
    """

    def self_extracting_cb_func(p, *args):
        assert _debug_com(f"COMObject method {method_name} called through interface {interface_name}")
        self = ctypes.cast(p + self_distance, ctypes.POINTER(ctypes.py_object)).contents.value
        result = method_func(self, *args)
        # Assume no return statement translates to success
        return S_OK if result is None else result

    return self_extracting_cb_func


def _adjust_impl(interface_name, method_name, original_method, offset):
    """A method implemented in a previous interface modifies the COMOboject pointer so it
    corresponds to an earlier interface and passes it on to the actual implementation.
    """

    def adjustor_cb_func(p, *args):
        assert _debug_com(f"COMObject method {method_name} called through interface "
                          f"{interface_name}, adjusting pointer by {offset}")
        return original_method(p + offset, *args)

    return adjustor_cb_func


class COMObject:
    """A COMObject for implementing C callbacks in Python.
    Specify the interface types it supports in `_interfaces_`, and any methods to be implemented
    by those interfaces as standard python methods. If the names match, they will be run as
    callbacks with all arguments supplied as the types specified in the corresponding interface,
    and `self` available as usual.
    Remember to call `super().__init__()`.

    COMObjects can be passed to ctypes functions directly as long as the corresponding argtype is
    an `Interface` pointer, or a `pInterface` subclass.

    IUnknown's methods will be autogenerated in case IUnknown is implemented.
    """

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)

        implemented_leaf_interfaces = cls.__dict__.get('_interfaces_', ())
        if not implemented_leaf_interfaces:
            raise TypeError("At least one interface must be defined to use a COMObject")

        for interface_type in implemented_leaf_interfaces:
            for other in implemented_leaf_interfaces:
                if interface_type is other:
                    continue
                if issubclass(interface_type, other):
                    raise TypeError("Only specify the leaf interfaces")

        # Sanity check done

        _ptr_size = ctypes.sizeof(ctypes.c_void_p)

        _vtbl_pointers = []
        implemented_methods = {}

        # Map all leaf and inherited interfaces to the offset of the vtable containing
        # their implementations
        _interface_to_vtbl_offset = {}
        for i, interface_type in enumerate(implemented_leaf_interfaces):
            bases = interface_type.get_interface_inheritance()
            for base in bases:
                if base not in _interface_to_vtbl_offset:
                    _interface_to_vtbl_offset[base] = i * _ptr_size

        if IUnknown in _interface_to_vtbl_offset:
            def QueryInterface(self, iid_ptr, res_ptr):
                ctypes.cast(res_ptr, ctypes.POINTER(ctypes.c_void_p))[0] = 0
                return E_NOINTERFACE

            def AddRef(self):
                self._vrefcount += 1
                return self._vrefcount

            def Release(self):
                if self._vrefcount <= 0:
                    assert _debug_com(
                        f"COMObject {self}: Release while refcount was {self._vrefcount}"
                    )
                self._vrefcount -= 1
                return self._vrefcount

            cls.QueryInterface = QueryInterface
            cls.AddRef = AddRef
            cls.Release = Release

        for i, interface_type in enumerate(implemented_leaf_interfaces):
            wrappers = []

            for method_name, method_type in interface_type._vtbl_struct_type._fields_:
                if method_name in implemented_methods:
                    # Method is already implemented on a previous interface; redirect to it
                    # See https://devblogs.microsoft.com/oldnewthing/20040206-00/?p=40723
                    # NOTE: Never tested, might be totally wrong
                    func, implementing_vtbl_idx = implemented_methods[method_name]
                    mth = _adjust_impl(interface_type.__name__,
                                       method_name,
                                       func,
                                       (implementing_vtbl_idx - i) * _ptr_size)

                else:
                    if (found_method := getattr(cls, method_name, None)) is None:
                        mth = _missing_impl(interface_type.__name__, method_name)
                    else:
                        mth = _found_impl(interface_type.__name__,
                                          method_name,
                                          found_method,
                                          (len(implemented_leaf_interfaces) - i) * _ptr_size)

                    implemented_methods[method_name] = (mth, i)

                wrappers.append(method_type(mth))

            vtbl = interface_type._vtbl_struct_type(*wrappers)
            _vtbl_pointers.append(ctypes.pointer(vtbl))

        fields = []
        for i, itf in enumerate(implemented_leaf_interfaces):
            fields.append((f'vtbl_ptr_{i}', ctypes.POINTER(itf._vtbl_struct_type)))
        fields.append(('self_', ctypes.py_object))

        cls._interface_to_vtbl_offset = _interface_to_vtbl_offset
        cls._vtbl_pointers = _vtbl_pointers
        cls._struct_type = _StructMeta(f"{cls.__name__}_Struct", (ctypes.Structure,), {'_fields_': fields})

    def __init__(self):
        self._vrefcount = 1
        self._struct = self._struct_type(*self._vtbl_pointers, ctypes.py_object(self))

    def as_interface(self, interface_type):
        # This method ignores the QueryInterface mechanism completely; no GUIDs are
        # associated with Interfaces on the python side, it can't be supported.
        # Still works, as so far none of the python-made COMObjects are expected to
        # support it by any C code.
        # (Also no need to always implement it, some COMObjects do not inherit from IUnknown.)
        if (offset := self._interface_to_vtbl_offset.get(interface_type, None)) is None:
            raise TypeError(f"Does not implement {interface_type}")

        return ctypes.byref(self._struct, offset)
