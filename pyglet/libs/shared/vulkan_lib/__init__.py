from __future__ import annotations

import ctypes
from platform import system
from types import ModuleType
from typing import Any, TYPE_CHECKING, Sequence, Callable, NoReturn
from ctypes import Structure, Union, cast, c_void_p

from _ctypes import _SimpleCData

import pyglet

from pyglet.util import asbytes

# Helper functions

# System initialization
system_name = system()
print("SYSTEM_NAME", system_name)
if system_name == 'Windows':
    lib_name = 'vulkan-1'
elif system_name == 'Linux':
    lib_name = 'libvulkan.so.1'
elif system_name == 'Darwin':
    lib_name = 'libMoltenVK.dylib'
else:
    raise ImportError("Not currently supported.")

try:
    vk_lib = pyglet.lib.load_library(lib_name)
except ImportError:
    raise ImportError("Vulkan Library was not found.")

if TYPE_CHECKING:
    from pyglet.libs.shared.vulkan_lib import VkInstance, VkDevice

repr_fn = lambda self: f"{self.__class__.__name__}{dict(self._fields_)!s}"

def define_struct(name: str, *args: Any) -> type[Structure]:
    return type(name, (Structure,), {'_fields_': args, '__repr__': repr_fn})

def define_union(name: str, *args: Any) -> type[Structure]:
    return type(name, (Union,), {'_fields_': args, '__repr__': repr_fn})

_debug_api = pyglet.options.debug_api
_debug_api_trace = pyglet.options.debug_api_trace
_debug_api_trace_args = pyglet.options.debug_api_trace_args

from pyglet.libs.shared.vulkan_lib import vulkan_core
from pyglet.libs.shared.vulkan_lib import exceptions
from pyglet.libs.shared.vulkan_lib.func import InstanceFunc, DeviceFunc

def errcheck(result: int | None, func: Callable, arguments: Sequence) -> Any:
    if _debug_api_trace:
        try:
            name = func.__name__
        except AttributeError:
            name = repr(func)
        if _debug_api_trace_args:
            trace_args = ', '.join([repr(arg)[:20] for arg in arguments])
            print(f'{name}({trace_args})')
        else:
            print(name)

    # If not VK_SUCCESS or None, then it is most likely an error.
    if result:
        VkException = exceptions.get(result)
        raise VkException(result)
    return result

def set_instance_functions(instance: VkInstance, modules: Sequence[ModuleType]) -> list[tuple[str, Callable]]:
    print("loading instance functions...")
    funcs = []
    for module in modules:
        for loaded_funcs in load_functions(instance, module.InstanceFunctions, vkGetInstanceProcAddr):
            funcs.append(loaded_funcs)
            name, fn = loaded_funcs
            setattr(InstanceFunc, name, fn)

    return funcs

def set_device_functions(instance: VkDevice, modules: Sequence[ModuleType]) -> list[tuple[str, Callable]]:
    print("loading device functions...")
    funcs = []
    for module in modules:
        for loaded_funcs in load_functions(instance, module.DeviceFunctions, vkGetDeviceProcAddr):
            funcs.append(loaded_funcs)
            name, fn = loaded_funcs
            setattr(DeviceFunc, name, fn)

    return funcs

def load_loader_functions():
    """Loader functions do not need any instance or device instance."""
    for module in modules:
        for loaded_funcs in load_functions(None, module.LoaderFunctions, vkGetInstanceProcAddr):
            fn_name, func = loaded_funcs
            setattr(module, fn_name, func)

def load_functions(vk_object, functions_list, loader):
    functions = []
    for name, prototype in functions_list:
        py_name = name
        address = loader(vk_object, asbytes(name))
        fn_ptr = cast(address, c_void_p)
        if fn_ptr:
            fn = prototype(fn_ptr.value)
            decorate_function(fn, name)
            functions.append((py_name, fn))
        else:
            functions.append((py_name, missing_function(py_name)))
            #if _debug_api is True:
            #     print(f'(debug): Function {py_name} could not be loaded.')
    return functions


class MissingFunctionException(Exception):  # noqa: N818
    def __init__(self, name: str, requires: str | None) -> None:
        msg = f'{name} is unavailable for this version of Vulkan.'
        Exception.__init__(self, msg)


def decorate_function(func: Callable, name: str) -> None:
    if _debug_api and 'ProcAddr' not in name:
        func.errcheck = errcheck
        func.__name__ = name


def link_func(name: str, restype: Any, argtypes: Any, requires: str | None = None) -> Callable[..., Any]:
    try:
        func = getattr(vk_lib, name)
        func.restype = restype
        func.argtypes = argtypes
        decorate_function(func, name)
        return func
    except AttributeError:
        return missing_function(name, requires)

def missing_function(name: str, requires: str | None = None) -> Callable:
    def MissingFunction(*_args, **_kwargs) -> NoReturn:  # noqa: ANN002, ANN003, N802
        raise MissingFunctionException(name, requires)

    return MissingFunction

def c_array_list(data: Sequence, ctypes_type: object):
    arr = (ctypes_type * len(data))()
    arr[:] = data
    pointer_to_ctype = ctypes.cast(arr, ctypes.POINTER(ctypes_type))
    return pointer_to_ctype

def c_str_array_list(data: Sequence):
    arr = (ctypes.c_char_p * len(data))()
    arr[:] = [value.encode('utf-8') for value in data]
    pointer_to_ctype = ctypes.cast(arr, ctypes.POINTER(ctypes.c_char_p))
    return pointer_to_ctype

# Should be available in all implementations.
vkGetInstanceProcAddr = link_func("vkGetInstanceProcAddr", ctypes.c_void_p, argtypes=[vulkan_core.VkInstance, ctypes.c_char_p])
vkGetDeviceProcAddr = link_func("vkGetDeviceProcAddr", ctypes.c_void_p, argtypes=[vulkan_core.VkDevice, ctypes.c_char_p])
# LoaderFunctions, InstanceFunctions, DeviceFunctions
modules = [vulkan_core]

# Load Loaders into the modules.
load_loader_functions()
