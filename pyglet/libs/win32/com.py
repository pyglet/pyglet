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

Only use STDMETHOD or METHOD for the method types (not ordinary ctypes
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
from typing import Any

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


class _COMInterfaceDummy(ctypes.Structure):
    """Dummy struct to serve as the type of all interfaces."""
    _fields_ = []

    @classmethod
    def get_interface_inheritance(cls):
        return cls.__mro__[:cls.__mro__.index(_COMInterfaceDummy)]


_COMInterfaceDummyPointer = ctypes.POINTER(_COMInterfaceDummy)
_PointerType = type(_COMInterfaceDummyPointer)
_StructType = type(ctypes.Structure)


class _InterfaceMeta(_StructType):
    def __new__(cls, name, bases, dct, /, pointer_type_dict=None):
        if len(bases) > 1:
            assert _debug_com(f"Ignoring {len(bases) - 1} bases on {name}")
            bases = (bases[0],)

        if not '_methods_' in dct:
            dct['_methods_'] = ()

        inh_methods = []
        for interface_type in (bases[0].get_interface_inheritance()):
            inh_methods.extend(interface_type.__dict__['_methods_'])

        inh_methods = tuple(inh_methods)
        new_methods = tuple(dct['_methods_'])

        vtbl_own_offset = len(inh_methods)

        all_methods = tuple(inh_methods) + new_methods
        for i, (method_name, mt) in enumerate(all_methods):
            assert _debug_com(f"{name}[{i}]: {method_name}: "
                              f"{(', '.join(t.__name__ for t in mt.argtypes) or '()')} -> "
                              f"{mt.restype.__name__}")

        vtbl_struct_type = _StructType(f"Vtable_{name}",
                                       (ctypes.Structure,),
                                       {'_fields_': [(n, x.direct_prototype) for n, x in all_methods]})
        dct['_vtbl_struct_type'] = vtbl_struct_type
        dct['vtbl_own_offset'] = vtbl_own_offset

        dct['_fields_'] = (('vtbl_ptr', ctypes.POINTER(vtbl_struct_type)),)

        res_interface_struct = super().__new__(cls, name, bases, dct)

        # Create special pInterface pointer subclass
        b = _COMInterfaceDummyPointer if bases[0] is _COMInterfaceDummy else ctypes.POINTER(bases[0])
        if pointer_type_dict is None:
            pointer_type_dict = {}
        pointer_type_dict['_type_'] = res_interface_struct
        own_pointer_type = _pInterfaceMeta(f"p{name}", (b,), pointer_type_dict)

        # Hack it into the ctypes pointer cache so all uses of `ctypes.POINTER` on this interface
        # type will yield it instead of the extremely inflexible standard pointer
        from ctypes import _pointer_type_cache
        _pointer_type_cache[res_interface_struct] = own_pointer_type

        return res_interface_struct


@classmethod
def _pInterface_from_param(cls, obj):
    """When dealing with a COMObject, pry a fitting interface out of it
    via a GUID-less version of the QueryInterface mechanism
    """

    if not isinstance(obj, COMObject):
        return obj

    if (i := obj._interface_to_vtbl_idx.get(cls._type_, None)) is None:
        raise TypeError(f"COMObject {obj} does not implement {cls._type_}")

    return ctypes.byref(obj._struct, i * (ctypes.sizeof(ctypes.c_void_p)))


# Unfortunately, ctypes' pointer factory only checks the immediate typedict for `_type_`,
# making meaningful propagation of the _type_ attribute impossible via simple subclassing
class _pInterfaceMeta(_PointerType):
    def __new__(cls, name, bases, dct):
        # Interfaces can be declared by inheritance of pInterface subclasses
        # If this happens, create the interface and then become pointer to its struct.

        target = dct.get('_type_', None)
        # If we weren't created due to an Interface subclass definition (don't have a _type_),
        # just define that Interface subclass, which will then actually create the pointer type
        if target is None:
            interface_base = bases[0]._type_

            # Create corresponding interface type and then retrieve own new type through cache
            it = _InterfaceMeta(f"_{name}_HelperInterface",
                                (interface_base,),
                                {'_methods_': dct.get('_methods_', ())},
                                pointer_type_dict=dct)
            return ctypes.POINTER(it)

        # Create method proxies that will forward ourselves into the interface's methods
        for i, (method_name, method) in enumerate(target._methods_):
            m = method.get_com_proxy(i + target.vtbl_own_offset, method_name)
            def pinterface_method_forward(self, *args, _m=m, _i=i):
                # assert _debug_com(f'Calling COM {_i} of {target.__name__} ({_m}) through pointer: ({", ".join(map(repr, (self, *args)))})')
                return _m(self, *args)
            dct[method_name] = pinterface_method_forward

        dct['from_param'] = _pInterface_from_param

        return super().__new__(cls, name, bases, dct)


class Interface(_COMInterfaceDummy, metaclass=_InterfaceMeta):
    pass
    # def __init__(self):
    #     raise RuntimeError("Cannot instantiate interfaces")


class pInterface(_COMInterfaceDummyPointer, metaclass=_pInterfaceMeta):
    pass


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
        ('Release', METHOD(ctypes.c_int))
    ]


class COMInterfaceMeta(type):
    """This differs in the original as an implemented interface object, not a POINTER object.
    Used when the user must implement their own functions within an interface rather than
    having interfaces be created and generated by other COM objects.
    The types are automatically inserted in the ctypes type cache so it can recognize the
    type arguments.
    """

    def __new__(mcs, name, bases, dct):
        methods = dct.pop("_methods_", None)
        cls = type.__new__(mcs, name, bases, dct)

        if methods is not None:
            cls._methods_ = methods

        if not bases: # only for class Interface(...) below
            _ptr_bases = (COMPointer,)
        else:
            _ptr_bases = (ctypes.POINTER(bases[0]),)

        # Class type is dynamically created inside __new__ based on metaclass inheritence; update ctypes cache manually.
        from ctypes import _pointer_type_cache
        _pointer_type_cache[cls] = type(COMPointer)("POINTER({})".format(cls.__name__),
                                                    _ptr_bases,
                                                    {"__interface__": cls})
        # pointer registry is tainted here; each pointer to an Interface subtype is actually just
        # a c_void_p lookalike with an unofficial dunder attribute
        # TODO: hope this is irrelevant outside of the module, then work around it

        return cls

    def __get_subclassed_methodcount(self):
        """Returns the amount of COM methods in all subclasses to determine offset of methods.
           Order must be exact from the source when calling COM methods.
        """
        try:
            result = 0
            for itf in self.mro()[1:-1]:
                result += len(itf.__dict__["_methods_"])
            return result
        except KeyError as err:
            (name,) = err.args
            if name == "_methods_":
                raise TypeError("Interface '{}' requires a _methods_ attribute.".format(itf.__name__))
            raise


class COMPointerMeta(type(ctypes.c_void_p), COMInterfaceMeta):
    """Required to prevent metaclass conflicts with inheritance."""

class COMPointer(ctypes.c_void_p, metaclass=COMPointerMeta):
    """COM Pointer base, could use c_void_p but need to override from_param ."""

    @classmethod
    def from_param(cls, obj):
        """Allows obj to return ctypes pointers, even if its base is not a ctype.
           In this case, all we simply want is a ctypes pointer matching the cls interface from the obj.
        """
        if obj is None:
            return

        try:
            ptr_dct = obj._pointers
        except AttributeError:
            raise TypeError("Interface method argument specified incorrectly, or passed wrong argument.", cls)
        else:
            try:
                return ptr_dct[cls.__interface__]
            except KeyError:
                raise TypeError("Interface {} doesn't have a pointer in this class.".format(cls.__name__))


class Interface(metaclass=COMInterfaceMeta):
    _methods_ = []


class IUnknown(Interface):
    """These methods are not implemented by default yet. Strictly for COM method ordering."""
    _methods_ = [
        ('QueryInterface', STDMETHOD(ctypes.c_void_p, REFIID, ctypes.c_void_p)),
        ('AddRef', METHOD(ctypes.c_int, ctypes.c_void_p)),
        ('Release', METHOD(ctypes.c_int, ctypes.c_void_p))
    ]


def _missing_impl(interface_name, method_name):
    """Functions that are not implemented use this to prevent errors when called."""

    def missing_cb_func(*_):
        """Return E_NOTIMPL because the method is not implemented."""
        assert _debug_com(f"Undefined method {method_name} called in interface {interface_name}")
        return 0x80004001

    return missing_cb_func


def _found_impl(interface_name, method_name, method_func, self_distance):
    """If a method was found in class, we can set it as a callback."""

    def self_extracting_cb_func(p, *args):
        self = ctypes.cast(
            p + self_distance * ctypes.sizeof(ctypes.c_void_p),
            ctypes.POINTER(ctypes.py_object)
        ).contents.value
        result = method_func(self, *args)

        if not result:  # QOL so callbacks don't need to specify a return for assumed OK's.
            return 0

        return result

    return self_extracting_cb_func


def _adjust_impl(interface_name, method_name, original_method, offset):
    def adjustor(p, *args):
        return original_method(p + offset * ctypes.sizeof(ctypes.c_void_p), *args)

    return adjustor


class COMObject:
    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)

        implemented_interfaces = cls.__dict__.get('_interfaces_', ())
        for interface_type in implemented_interfaces:
            for other in implemented_interfaces:
                if interface_type is other:
                    continue
                if issubclass(interface_type, other):
                    raise TypeError("Only specify the leaf interfaces")

        # Done with sanity checks

        _vtbl_pointers = []
        _interface_to_vtbl_idx = {}
        implemented_methods = {}

        for i, interface_type in enumerate(implemented_interfaces):
            wrappers = []

            for method_name, method_type in interface_type._vtbl_struct_type._fields_:
                if method_name in implemented_methods:
                    # Method is already implemented on a previous interface; redirect to it
                    # See https://devblogs.microsoft.com/oldnewthing/20040206-00/?p=40723
                    # NOTE: Never tested, might be totally wrong
                    func, implementing_vtbl_idx = implemented_methods[method_name]
                    wrapped = method_type(_adjust_impl(interface_type.__name__,
                                                       method_name,
                                                       func,
                                                       implementing_vtbl_idx - i))

                else:
                    if (found_method := getattr(cls, method_name, None)) is None:
                        mth = _missing_impl(interface_type.__name__, method_name)
                    else:
                        mth = _found_impl(interface_type.__name__,
                                          method_name,
                                          found_method,
                                          len(implemented_interfaces) - i)

                    implemented_methods[method_name] = (mth, i)
                    wrapped = method_type(mth)

                wrappers.append(wrapped)

            vtbl = interface_type._vtbl_struct_type(*wrappers)
            _vtbl_pointers.append(ctypes.pointer(vtbl))
            for supported_base in interface_type.get_interface_inheritance():
                if supported_base not in _interface_to_vtbl_idx:
                    _interface_to_vtbl_idx[supported_base] = i

        fields = []
        for i, itf in enumerate(implemented_interfaces):
            fields.append((f'vtbl_ptr_{i}', ctypes.POINTER(itf._vtbl_struct_type)))
        fields.append(('self_', ctypes.py_object))

        cls._interface_to_vtbl_idx = _interface_to_vtbl_idx
        cls._vtbl_pointers = _vtbl_pointers
        cls._struct_type = _StructType(f"{cls.__name__}_Struct", (ctypes.Structure,), {'_fields_': fields})

    def __init__(self):
        self._struct = self._struct_type(*self._vtbl_pointers, ctypes.py_object(self))
