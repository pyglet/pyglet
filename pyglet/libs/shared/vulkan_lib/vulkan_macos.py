from __future__ import annotations

from ctypes import c_void_p, POINTER, CFUNCTYPE
from . import define_struct
from .vulkan_core import VkFlags, VkStructureType, VkResult, VkInstance, VkAllocationCallbacks, VkSurfaceKHR

VULKAN_MACOS_H_: int = 1

VK_MVK_MACOS_SURFACE_SPEC_VERSION: int = 3
VK_MVK_MACOS_SURFACE_EXTENSION_NAME: str = "VK_MVK_macos_surface"
VkMacOSSurfaceCreateFlagsMVK: type[VkFlags] = VkFlags
VkMacOSSurfaceCreateInfoMVK = define_struct('VkMacOSSurfaceCreateInfoMVK',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('flags', VkMacOSSurfaceCreateFlagsMVK),
    ('pView', c_void_p),
)

PFN_vkCreateMacOSSurfaceMVK = CFUNCTYPE(VkResult, VkInstance, POINTER(VkMacOSSurfaceCreateInfoMVK), POINTER(VkAllocationCallbacks), POINTER(VkSurfaceKHR))
InstanceFunctions = (
  ("vkCreateMacOSSurfaceMVK", PFN_vkCreateMacOSSurfaceMVK),
)

DeviceFunctions = (
)

LoaderFunctions = (
)

