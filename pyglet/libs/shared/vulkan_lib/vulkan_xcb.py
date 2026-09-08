from __future__ import annotations

from ctypes import c_void_p, POINTER, CFUNCTYPE, c_uint32, c_int
from . import define_struct
from .vulkan_core import VkFlags, VkStructureType, VkResult, VkInstance, VkAllocationCallbacks, VkSurfaceKHR, \
    VkPhysicalDevice, VkBool32

# Replace these 3 with actual values. Unknown:
xcb_connection_t = c_void_p
xcb_window_t = c_void_p
xcb_visualid_t = c_void_p

VULKAN_XCB_H_: int = 1

VK_KHR_XCB_SURFACE_SPEC_VERSION: int = 6
VK_KHR_XCB_SURFACE_EXTENSION_NAME: str = "VK_KHR_xcb_surface"
VkXcbSurfaceCreateFlagsKHR: type[VkFlags] = VkFlags
VkXcbSurfaceCreateInfoKHR = define_struct('VkXcbSurfaceCreateInfoKHR',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('flags', VkXcbSurfaceCreateFlagsKHR),
    ('connection', POINTER(xcb_connection_t)),
    ('window', xcb_window_t),
)

PFN_vkCreateXcbSurfaceKHR = CFUNCTYPE(VkResult, VkInstance, POINTER(VkXcbSurfaceCreateInfoKHR), POINTER(VkAllocationCallbacks), POINTER(VkSurfaceKHR))
PFN_vkGetPhysicalDeviceXcbPresentationSupportKHR = CFUNCTYPE(VkBool32, VkPhysicalDevice, c_uint32, POINTER(xcb_connection_t), xcb_visualid_t)
InstanceFunctions = (
  ("vkCreateXcbSurfaceKHR", PFN_vkCreateXcbSurfaceKHR),
  ("vkGetPhysicalDeviceXcbPresentationSupportKHR", PFN_vkGetPhysicalDeviceXcbPresentationSupportKHR),
)

DeviceFunctions = (
)

LoaderFunctions = (
)

