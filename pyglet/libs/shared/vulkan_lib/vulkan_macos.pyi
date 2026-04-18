from pyglet.libs.shared.vulkan_lib.vulkan_core import VkFlags, VkInstance, VkAllocationCallbacks, VkSurfaceKHR, \
    VkStructureType, VkResult
from ctypes import c_void_p, POINTER, Structure


VULKAN_MACOS_H_: int = 1
VK_MVK_MACOS_SURFACE_SPEC_VERSION: int = 3
VK_MVK_MACOS_SURFACE_EXTENSION_NAME: str = "VK_MVK_macos_surface"
VkMacOSSurfaceCreateFlagsMVK: VkFlags
def vkCreateMacOSSurfaceMVK(instance: VkInstance, pCreateInfo: POINTER(VkMacOSSurfaceCreateInfoMVK), pAllocator: POINTER(VkAllocationCallbacks), pSurface: POINTER(VkSurfaceKHR)) -> VkResult:
    ...

class VkMacOSSurfaceCreateInfoMVK(Structure):
    sType: VkStructureType
    pNext: c_void_p
    flags: VkMacOSSurfaceCreateFlagsMVK
    pView: c_void_p

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 flags: VkMacOSSurfaceCreateFlagsMVK | None = None,
                 pView: c_void_p | None = None,
    ) -> None: ...

