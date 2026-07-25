from __future__ import annotations

from ctypes import c_void_p, POINTER, CFUNCTYPE, c_uint32
from . import define_struct
from .vulkan_core import VkFlags, VkStructureType, VkResult, VkInstance, VkAllocationCallbacks, VkSurfaceKHR, \
    VkPhysicalDevice, VkBool32

# Replace these 2 with wayland structs. Unknown currently.
wl_display = c_void_p
wl_surface = c_void_p

VULKAN_WAYLAND_H_: int = 1

VK_KHR_WAYLAND_SURFACE_SPEC_VERSION: int = 6
VK_KHR_WAYLAND_SURFACE_EXTENSION_NAME: str = "VK_KHR_wayland_surface"
VkWaylandSurfaceCreateFlagsKHR: type[VkFlags] = VkFlags
VkWaylandSurfaceCreateInfoKHR = define_struct('VkWaylandSurfaceCreateInfoKHR',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('flags', VkWaylandSurfaceCreateFlagsKHR),
    ('display', POINTER(wl_display)),
    ('surface', POINTER(wl_surface)),
)

PFN_vkCreateWaylandSurfaceKHR = CFUNCTYPE(VkResult, VkInstance, POINTER(VkWaylandSurfaceCreateInfoKHR), POINTER(VkAllocationCallbacks), POINTER(VkSurfaceKHR))
PFN_vkGetPhysicalDeviceWaylandPresentationSupportKHR = CFUNCTYPE(VkBool32, VkPhysicalDevice, c_uint32, POINTER(wl_display))
InstanceFunctions = (
  ("vkCreateWaylandSurfaceKHR", PFN_vkCreateWaylandSurfaceKHR),
  ("vkGetPhysicalDeviceWaylandPresentationSupportKHR", PFN_vkGetPhysicalDeviceWaylandPresentationSupportKHR),
)

DeviceFunctions = (
)

LoaderFunctions = (
)

