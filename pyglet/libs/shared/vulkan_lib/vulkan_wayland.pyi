from pyglet.libs.shared.vulkan_lib.vulkan_core import VkFlags, VkInstance, VkAllocationCallbacks, VkSurfaceKHR, \
    VkStructureType, VkResult, VkPhysicalDevice, VkBool32
from ctypes import c_void_p, POINTER, Structure

wl_display: c_void_p
wl_surface: c_void_p

VULKAN_WAYLAND_H_: int = 1
VK_KHR_WAYLAND_SURFACE_SPEC_VERSION: int = 6
VK_KHR_WAYLAND_SURFACE_EXTENSION_NAME: str = "VK_KHR_wayland_surface"
VkWaylandSurfaceCreateFlagsKHR: VkFlags
def vkCreateWaylandSurfaceKHR(instance: VkInstance, pCreateInfo: POINTER(VkWaylandSurfaceCreateInfoKHR), pAllocator: POINTER(VkAllocationCallbacks), pSurface: POINTER(VkSurfaceKHR)) -> VkResult:
    ...

def vkGetPhysicalDeviceWaylandPresentationSupportKHR(physicalDevice: VkPhysicalDevice, queueFamilyIndex: int, display: POINTER(wl_display)) -> VkBool32:
    ...

class VkWaylandSurfaceCreateInfoKHR(Structure):
    sType: VkStructureType
    pNext: c_void_p
    flags: VkWaylandSurfaceCreateFlagsKHR
    display: POINTER(wl_display)
    surface: POINTER(wl_surface)

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 flags: VkWaylandSurfaceCreateFlagsKHR | None = None,
                 display: POINTER(wl_display) | None = None,
                 surface: POINTER(wl_surface) | None = None,
    ) -> None: ...

