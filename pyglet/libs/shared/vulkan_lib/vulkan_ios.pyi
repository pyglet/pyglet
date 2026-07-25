from pyglet.libs.shared.vulkan_lib.vulkan_core import VkFlags, VkInstance, VkAllocationCallbacks, VkSurfaceKHR, \
    VkStructureType, VkResult
from ctypes import c_void_p, POINTER, Structure

VULKAN_IOS_H_: int = 1
VK_MVK_IOS_SURFACE_SPEC_VERSION: int = 3
VK_MVK_IOS_SURFACE_EXTENSION_NAME: str = "VK_MVK_ios_surface"
VkIOSSurfaceCreateFlagsMVK: VkFlags
def vkCreateIOSSurfaceMVK(instance: VkInstance, pCreateInfo: POINTER(VkIOSSurfaceCreateInfoMVK), pAllocator: POINTER(VkAllocationCallbacks), pSurface: POINTER(VkSurfaceKHR)) -> VkResult:
    ...

class VkIOSSurfaceCreateInfoMVK(Structure):
    sType: VkStructureType
    pNext: c_void_p
    flags: VkIOSSurfaceCreateFlagsMVK
    pView: c_void_p

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 flags: VkIOSSurfaceCreateFlagsMVK | None = None,
                 pView: c_void_p | None = None,
    ) -> None: ...

