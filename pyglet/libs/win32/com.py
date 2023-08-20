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

from pyglet.util import debug_print

_debug_com = debug_print('debug_com')

if sys.platform != 'win32':
    raise ImportError('pyglet.libs.win32.com requires a Windows build of Python')


class GUID(ctypes.Structure):
    _fields_ = [
        ('Data1', ctypes.c_ulong),
        ('Data2', ctypes.c_ushort),
        ('Data3', ctypes.c_ushort),
        ('Data4', ctypes.c_ubyte * 8)
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

    def get_field(self):
        # ctypes caches WINFUNCTYPE's so this should be ok.
        return ctypes.WINFUNCTYPE(self.restype, *self.argtypes)


class STDMETHOD(METHOD):
    """COM method with HRESULT return value."""

    def __init__(self, *args):
        super().__init__(ctypes.HRESULT, *args)


class COMMethodInstance:
    """Binds a COM interface method."""

    def __init__(self, name, i, method):
        self.name = name
        self.i = i
        self.method = method

    # x->F(a, b, c)
    # x->lpVtbl->F(x, a, b, c)
    # ((FunctionPointerTrustMeBro *)x->lpVtbl)[i](a, b, c)

    def __get__(self, obj, tp):
        if obj is not None:
            def _call(*args):
                # assert _debug_com(f'COM: IN  {obj.__class__.__name__}.{self.name}[{self.i}]: (~, {", ".join(map(repr, args))})')
                ret = self.method.get_field()(self.i, self.name)(obj, *args)
                # assert _debug_com(f'COM: OUT {obj.__class__.__name__}.{self.name}[{self.i}]: (~, {", ".join(map(repr, args))})')
                # assert _debug_com(f'COM: RETURN {ret}')
                return ret

            return _call

        raise AttributeError()


class _COMInterface(ctypes.Structure):
    """Dummy struct to serve as the type of all COM pointers."""
    _fields_ = [('lpVtbl', ctypes.c_void_p)]


COMInterfacePointer = ctypes.POINTER(_COMInterface)
_PointerType = type(COMInterfacePointer)


# Unfortunately, ctypes' pointer factory only checks the immediate typedict for `_type_`,
# making meaningful propagation of the _type_ attribute impossible via simple subclassing:
# Every pointer type beneath COMInterfacePointer has no type as far as ctypes is concerned,
# resulting in the error "Cannot create instance: has no _type_" upon pointer creation.
# Use a metaclass to force _type_ in as early as possible just like the POINTER factory does.
class _pInterfaceMeta(_PointerType):
    def __new__(cls, name, bases, dct):
        dct['_type_'] = _COMInterface
        return super().__new__(cls, name, bases, dct)


class pInterface(COMInterfacePointer, metaclass=_pInterfaceMeta):
    """Base COM interface pointer."""

    def __init_subclass__(cls, /, **kwargs):
        methods = []
        relevant_bases = cls.__mro__[:cls.__mro__.index(pInterface)]
        for base in reversed(relevant_bases):
            methods.extend(base.__dict__.get('_methods_', ()))

        for i, (method_name, method_type) in enumerate(methods):
            assert _debug_com(f'{cls.__name__}[{i}]: {method_name}')
            setattr(cls, method_name, COMMethodInstance(method_name, i, method_type))

        super().__init_subclass__(**kwargs)


<<<<<<< HEAD
class pInterface(ctypes.POINTER(COMInterface), metaclass=InterfacePtrMeta):
    """Base COM interface pointer."""
=======
class pIUnknown(pInterface):
    _methods_ = [
        ('QueryInterface', STDMETHOD(REFIID, ctypes.c_void_p)),
        ('AddRef', METHOD(ctypes.c_int)),
        ('Release', METHOD(ctypes.c_int))
    ]
>>>>>>> b7e8f8ff (COM module rewrite step 0)


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


def _found_impl(interface_name, method_name, method_func):
    """If a method was found in class, we can set it as a callback."""

    def cb_func(*args, **kw):
        try:
            result = method_func(*args, **kw)
        except Exception as err:
            raise err

        if not result:  # QOL so callbacks don't need to specify a return for assumed OK's.
            return 0

        return result

    return cb_func


# Store structures with same fields to prevent duplicate table creations.
_cached_structures = {}


def create_vtbl_structure(fields, interface):
    """Create virtual table structure with fields for use in COM's."""
    try:
        return _cached_structures[fields]
    except KeyError:
        Vtbl = type("Vtbl_{}".format(interface.__name__), (ctypes.Structure,), {"_fields_": fields})
        _cached_structures[fields] = Vtbl
        _debug_com(f"vtbl len {len(fields)} created for {interface}")
        return Vtbl


class COMObject:
    """A base class for defining a COM object for use with callbacks and custom implementations."""
    _interfaces_ = []

    def __new__(cls, *args, **kw):
        new_cls = super().__new__(cls)
        assert len(cls._interfaces_) > 0, "Atleast one interface must be defined to use a COMObject."
        new_cls._pointers = {}
        new_cls.__create_interface_pointers()
        return new_cls

    def __create_interface_pointers(cls):
        """Create a custom ctypes structure to handle COM functions in a COM Object."""
        interfaces = tuple(cls._interfaces_)
        for itf in interfaces[::-1]:
            methods = []
            fields = []
            print(itf.__mro__)
            for interface in itf.__mro__[-2::-1]:
                for method in interface._methods_:
                    name, com_method = method

                    if (found_method := getattr(cls, name, None)) is None:
                        mth = _missing_impl(itf.__name__, name)
                    else:
                        mth = _found_impl(itf.__name__, name, found_method)

                    proto = ctypes.WINFUNCTYPE(com_method.restype, *com_method.argtypes)

                    fields.append((name, proto))
                    methods.append(proto(mth))

            # Make a structure dynamically with the fields given.
            itf_structure = create_vtbl_structure(tuple(fields), interface)

            # Assign the methods to the fields
            vtbl = itf_structure(*methods)

            cls._pointers[itf] = ctypes.pointer(ctypes.pointer(vtbl))

    @property
    def pointers(self):
        """Returns pointers to the implemented interfaces in this COMObject.  Read-only.

        :type: dict
        """
        return self._pointers
