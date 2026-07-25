from ctypes import c_void_p, CFUNCTYPE, c_uint32

#
# Vulkan wrapper generated from Vulkan headers
#
from ctypes import POINTER

from pyglet.libs.x11.xlib import Display, Window, VisualID
from . import define_struct, define_union
from .vulkan_core import VkFlags, VkStructureType, VkResult, VkInstance, VkAllocationCallbacks, VkSurfaceKHR, \
    VkPhysicalDevice, VkBool32

VULKAN_XLIB_H_: int = 1

VK_KHR_XLIB_SURFACE_SPEC_VERSION: int = 6
VK_KHR_XLIB_SURFACE_EXTENSION_NAME: str = "VK_KHR_xlib_surface"
VkXlibSurfaceCreateFlagsKHR: type[VkFlags] = VkFlags
VkXlibSurfaceCreateInfoKHR = define_struct('VkXlibSurfaceCreateInfoKHR',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('flags', VkXlibSurfaceCreateFlagsKHR),
    ('dpy', POINTER(Display)),
    ('window', Window),
)

PFN_vkCreateXlibSurfaceKHR = CFUNCTYPE(VkResult, VkInstance, POINTER(VkXlibSurfaceCreateInfoKHR), POINTER(VkAllocationCallbacks), POINTER(VkSurfaceKHR))
PFN_vkGetPhysicalDeviceXlibPresentationSupportKHR = CFUNCTYPE(VkBool32, VkPhysicalDevice, c_uint32, POINTER(Display), VisualID)
InstanceFunctions = (
  ("vkCreateXlibSurfaceKHR", PFN_vkCreateXlibSurfaceKHR),
  ("vkGetPhysicalDeviceXlibPresentationSupportKHR", PFN_vkGetPhysicalDeviceXlibPresentationSupportKHR),
)

DeviceFunctions = (
)

LoaderFunctions = (
)

