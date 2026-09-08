from __future__ import annotations

from ctypes import c_void_p, POINTER, CFUNCTYPE
from . import define_struct
from .vulkan_core import VkFlags, VkStructureType, VkResult, VkInstance, VkAllocationCallbacks, VkSurfaceKHR

VULKAN_IOS_H_: int = 1

VK_MVK_IOS_SURFACE_SPEC_VERSION: int = 3
VK_MVK_IOS_SURFACE_EXTENSION_NAME: str = "VK_MVK_ios_surface"
VkIOSSurfaceCreateFlagsMVK: type[VkFlags] = VkFlags
VkIOSSurfaceCreateInfoMVK = define_struct('VkIOSSurfaceCreateInfoMVK',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('flags', VkIOSSurfaceCreateFlagsMVK),
    ('pView', c_void_p),
)

PFN_vkCreateIOSSurfaceMVK = CFUNCTYPE(VkResult, VkInstance, POINTER(VkIOSSurfaceCreateInfoMVK), POINTER(VkAllocationCallbacks), POINTER(VkSurfaceKHR))
InstanceFunctions = (
  ("vkCreateIOSSurfaceMVK", PFN_vkCreateIOSSurfaceMVK),
)

DeviceFunctions = (
)

LoaderFunctions = (
)

