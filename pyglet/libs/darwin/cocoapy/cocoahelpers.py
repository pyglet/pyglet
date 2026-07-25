from __future__ import annotations

from typing import Any

from pyglet.libs.darwin.cocoapy.runtime import ObjCInstance, ObjCClass

NSSet = ObjCClass('NSSet')
NSNull = ObjCClass('NSNull')
NSString = ObjCClass("NSString")
NSData = ObjCClass("NSData")
NSNumber = ObjCClass("NSNumber")
NSMutableArray = ObjCClass("NSMutableArray")
NSArray = ObjCClass("NSArray")
NSDictionary = ObjCClass("NSDictionary")
NSMutableDictionary = ObjCClass("NSMutableDictionary")

def pystr_to_ns(value: str):
    return NSString.stringWithUTF8String_(value.encode("utf-8"))

def pybool_to_ns(value: bool):
    return NSNumber.numberWithBool_(value)

def pyint_to_ns(value: int):
    return NSNumber.numberWithInt_(value)

def pyfloat_to_ns(value: float):
    return NSNumber.numberWithDouble_(value)

def pynone_to_ns(_value):
    return NSNull.null()

def _iterable_to_mutable_array(value: list | tuple):
    arr = NSMutableArray.array()
    for item in value:
        arr.addObject_(py_to_ns(item))
    return arr

def pylist_to_ns(value: list) -> NSMutableArray:
    """Convert Python list to NSMutableArray."""
    return _iterable_to_mutable_array(value)

def pytuple_to_ns(value: tuple) -> NSArray:
    """Convert Python tuple to NSArray (immutable)."""
    mutable = _iterable_to_mutable_array(value)
    return NSArray.arrayWithArray_(mutable)

def pydict_to_ns(value: dict, mutable: bool=True) -> NSMutableDictionary | NSDictionary:
    """Convert Python dict to NSMutableDictionary."""
    d = NSMutableDictionary.dictionary()
    for k, v in value.items():
        ns_key = py_to_ns(k)
        ns_val = py_to_ns(v)
        d.setObject_forKey_(ns_val, ns_key)
    if not mutable:
        return NSDictionary.dictionaryWithDictionary_(d)
    return d


_CONVERTERS = {
    str:     pystr_to_ns,
    bool:    pybool_to_ns,
    int:     pyint_to_ns,
    float:   pyfloat_to_ns,
    list:    pylist_to_ns,
    tuple:   pytuple_to_ns,
    dict:    pydict_to_ns,
    type(None): pynone_to_ns,
}

def py_to_ns(value: Any) -> ObjCInstance:
    """General Python to NS object converter.

    Should be used whenever interacting with AppKit, Cocoa, or any other NS-related functions.
    """
    if isinstance(value, ObjCInstance):
        return value

    t = type(value)
    converter = _CONVERTERS.get(t)

    if converter:
        return converter(value)

    raise TypeError(f"Cannot convert Python type {t} to NS object")

# ===== Converting from NS to Python
def nsstr_to_py(nsobj: NSString) -> str:
    return nsobj.UTF8String().decode("utf-8")


def nsnum_to_py(nsobj: NSNumber) -> int | float:
    """Converting from NSNumber

    NSNumber can represent bool, int, or float internally"""
    t = nsobj.objCType().decode()

    if t == 'c':  # char / BOOL
        return bool(nsobj.boolValue())
    elif t in ('i', 'l', 'q', 's'):
        return int(nsobj.intValue())
    elif t in ('f', 'd'):
        return float(nsobj.doubleValue())

    return nsobj.doubleValue()


def nsarray_to_py(nsobj: NSArray) -> list:
    py_list = []
    for i in range(nsobj.count()):
        item = nsobj.objectAtIndex_(i)
        py_list.append(ns_to_py(item))
    return py_list


def nsmutarray_to_py(nsobj: NSMutableArray):
    return nsarray_to_py(nsobj)


def nsdict_to_py(nsobj: NSDictionary):
    py_dict = {}

    # NSDictionary requires enumerating keys
    keys = nsobj.allKeys()
    for i in range(keys.count()):
        key = keys.objectAtIndex_(i)
        val = nsobj.objectForKey_(key)

        py_key = ns_to_py(key)
        py_val = ns_to_py(val)

        py_dict[py_key] = py_val

    return py_dict


# NSMutableDictionary handled the same
def nsmutdict_to_py(nsobj: NSMutableDictionary):
    return nsdict_to_py(nsobj)


def nsset_to_py(nsset) -> set:
    """Convert NSSet or NSFrozenSet to a Python set."""
    py = set()
    enumerator = nsset.objectEnumerator()
    while True:
        obj = enumerator.nextObject()
        if obj is None:
            break
        py.add(ns_to_py(obj))
    return py

def nsnull_to_py(_nsnull):
    return None

_NS_TO_PY_CONVERTERS = {
    NSString: nsstr_to_py,
    NSNumber: nsnum_to_py,
    NSArray: nsarray_to_py,
    NSMutableArray: nsmutarray_to_py,
    NSDictionary: nsdict_to_py,
    NSMutableDictionary: nsmutdict_to_py,
    NSNull: nsnull_to_py,
    NSSet: nsset_to_py,
}


def ns_to_py(nsobj: ObjCInstance):
    """Convert NS object to Python, recursively."""
    if nsobj is None:
        return None

    if not isinstance(nsobj, ObjCInstance):
        raise Exception(f"{nsobj} Not an ObjCInstance")

    for cls, converter in _NS_TO_PY_CONVERTERS.items():
        # NS Objects have many different variations of the same type.
        # For example a string can be NSTaggedPointerString, __NSCFString, NSMutableString, NSString, etc..
        if nsobj.isKindOfClass_(cls):
            return converter(nsobj)

    return nsobj
