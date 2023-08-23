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
    """Dummy struct to serve as the type of all COM pointers."""
    _fields_ = [('vtbl_ptr', ctypes.c_void_p)]


_COMInterfaceDummyPointer = ctypes.POINTER(_COMInterfaceDummy)
_PointerType = type(_COMInterfaceDummyPointer)
_StructType = type(ctypes.Structure)


def _accumulate_inherited_methods(from_, barrier):
    methods = []
    for base in reversed(from_.__mro__[:from_.__mro__.index(barrier)]):
        methods.extend(base.__dict__.get('_methods_', ()))
    return methods


class _InterfaceMeta(_StructType):
    def __new__(cls, name, bases, dct, /, pointer_type_dict=None):
        if len(bases) > 1:
            assert _debug_com(f"Ignoring {len(bases) - 1} bases on {name}")
            bases = (bases[0],)

        inh_methods = _accumulate_inherited_methods(bases[0], ctypes.Structure)
        new_methods = tuple(dct.get('_methods_', ()))

        for i, (meth_name, meth_type) in enumerate(new_methods, start=len(inh_methods)):
            dct[meth_name] = meth_type.get_com_proxy(i, meth_name)

        all_methods = tuple(inh_methods) + new_methods
        for i, (method_name, _) in enumerate(all_methods):
            assert _debug_com(f"{name}[{i}]: {method_name}")

        vtbl_struct_type = _StructType(f"Vtable_{name}",
                                       (ctypes.Structure,),
                                       {'_fields_': [(n, x.direct_prototype) for n, x in all_methods]})
        dct['_vtbl_struct_type'] = vtbl_struct_type
        dct['vtbl_own_offset'] = len(inh_methods)

        dct['_fields_'] = (('vtbl_ptr', ctypes.POINTER(vtbl_struct_type)),)

        res_interface_struct = super().__new__(cls, name, bases, dct)

        # Create special pInterface pointer subclass
        b = _COMInterfaceDummyPointer if bases[0] is _COMInterfaceDummy else ctypes.POINTER(bases[0])
        if pointer_type_dict is None:
            pointer_type_dict = {}
        pointer_type_dict['_type_'] = res_interface_struct
        own_pointer_type = _pInterfaceMeta(f"p{name}", (b,), pointer_type_dict)

        # Hack it into the ctypes pointer cache so all uses of `ctypes.POINTER` on this interface
        # type will yield it instead of the extremely inflexible standard
        from ctypes import _pointer_type_cache
        _pointer_type_cache[res_interface_struct] = own_pointer_type

        return res_interface_struct


# Unfortunately, ctypes' pointer factory only checks the immediate typedict for `_type_`,
# making meaningful propagation of the _type_ attribute impossible via simple subclassing
class _pInterfaceMeta(_PointerType):
    def __new__(cls, name, bases, dct):
        # Interfaces can also be declared by inheritance of pInterface subclasses
        # If this happens, create the interface and then become pointer to its struct.

        target = dct.get('_type_', None)

        # If we weren't created due to an Interface subclass definition (don't have a _type_),
        # just define that Interface subclass, which will then actually create the type properly.
        if target is None:
            interface_base = bases[0]._type_

            # Create corresponding interface type and then retrieve own new type through cache
            it = _InterfaceMeta(f"_{name}_FoundationInterface",
                                (interface_base,),
                                {'_methods_': dct.get('_methods_', ())},
                                pointer_type_dict=dct)
            return ctypes.POINTER(it)

        # Create method proxies that will forward ourselves into the 
        vtbl_struct_type = target._vtbl_struct_type
        for i in range(target.vtbl_own_offset, len(vtbl_struct_type._fields_)):
            method_name = vtbl_struct_type._fields_[i][0]
            m = getattr(target, method_name)
            def pinterface_method_forward(self, *args, _m=m):
                _m(self, *args)
            dct[method_name] = pinterface_method_forward

        return super().__new__(cls, name, bases, dct)


class Interface(_COMInterfaceDummy, metaclass=_InterfaceMeta):
    pass
    # def __init__(self):
    #     raise RuntimeError("Cannot instantiate interfaces")


class pInterface(_COMInterfaceDummyPointer, metaclass=_pInterfaceMeta):
    @classmethod
    def from_param(cls, obj):
        """When dealing with a COMObject, pry a fitting interface out of it
        via a GUID-less version of the QueryInterface mechanism
        """

        raise RuntimeError("todo")
        # if isinstance(obj, )
        return obj


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

    def missing_cb_func(*args):
        """Return E_NOTIMPL because the method is not implemented."""
        assert _debug_com(f"Undefined method {method_name} called in interface {interface_name}")
        return 0

    return missing_cb_func


def _found_impl(interface_name, method_name, method_func, self_distance):
    """If a method was found in class, we can set it as a callback."""

    def self_extracting_cb_func(p, *args):
        offset = ctypes.sizeof(ctypes.c_void_p) * self_distance
        self = ctypes.cast(p.value + offset, ctypes.py_object).value
        result = method_func(self, *args)

        if not result:  # QOL so callbacks don't need to specify a return for assumed OK's.
            return 0

        return result

    return cb_func


class _COMObjectMeta(_StructType):
    def __new__(cls, name, bases, dct):
        is_user_subclass = bases[0] is not ctypes.Structure
        if len(bases) != 1 and is_user_subclass:
            raise TypeError("Must directly inherit from COMObject only")

        implemented_interfaces = dct.pop('_interfaces_', ())
        if not implemented_interfaces and is_user_subclass:
            # could also just create an empty struct, but there's no point
            raise TypeError("Must implement at least one COM Interface in '_interfaces_'")

        for interface_type in implemented_interfaces:
            for other in implemented_interfaces:
                if interface_type is other:
                    continue
                if issubclass(interface_type, other):
                    raise TypeError("Only specify the leaf interfaces")

        # Done with sanity checks

        _vtbl_pointers = []
        implemented_methods = {}
        # NOTE: If two interfaces were to have name collisions, the last one will
        # overwrite previous ones.

        for i, interface_type in enumerate(implemented_interfaces):
            vtbl = interface_type._vtbl_struct_type()

            for method_name, method_type in interface_type._vtbl_struct_type._fields_:
                if method_name in implemented_methods:
                    # Method is already implemented on a previous interface; redirect to it
                    # See https://devblogs.microsoft.com/oldnewthing/20040206-00/?p=40723
                    method_obj, interface_idx = implemented_methods[method_name]
                    def adjustor(p, *args, _m=method_obj):
                        # Modification of p may be a bad idea
                        p.value += (interface_idx - i) * ctypes.sizeof(ctypes.c_void_p)
                        _m(p, *args)
                    setattr(vtbl, method_name, method_type(adjustor))
                else:
                    if (found_method := getattr(cls, name, None)) is None:
                        mth = _missing_impl(interface_type.__name__, name)
                    else:
                        mth = _found_impl(interface_type.__name__, name, found_method)

                    wrapped = method_type(mth)
                    setattr(vtbl, method_name, wrapped)
                    implemented_methods[method_name] = (wrapped, i)

            _vtbl_pointers.append(ctypes.cast(ctypes.pointer(vtbl), ctypes.c_void_p))

        dct['_vtbl_pointers'] = _vtbl_pointers
        # Discard all other _fields_, struct part is business of the metaclass
        # vtbl pointers to all distinct interfaces and then a reference to self
        dct['_fields_'] = [
            *((f'vtbl_ptr_{i}', ctypes.c_void_p) for i in range(len(implemented_interfaces))),
            ('self', ctypes.py_object),
        ]
        com_object_struct = super().__new__(cls, name, bases, dct)

        return com_object_struct


class COMObject(ctypes.Structure, metaclass=_COMObjectMeta):
    def __init__(self):
        # For some reason, complains about receiving a c_void_p instead of a py_object instance
        # Set them over multiple lines then
        # super().__init__(*self._vtbl_pointers, ctypes.py_object(self))
        super().__init__()
        for i, p in enumerate(self._vtbl_pointers):
            setattr(self, f"vtbl_ptr_{i}", p)
        self.self = ctypes.py_object(self)
