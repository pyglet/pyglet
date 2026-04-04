from pyglet.libs.shared.vulkan_lib.vulkan_core import VkFlags, VkInstance, VkAllocationCallbacks, VkSurfaceKHR, \
    VkStructureType, VkResult, VkPhysicalDevice, VkBool32
from ctypes import c_void_p, POINTER, Structure

xcb_connection_t: c_void_p
xcb_window_t: c_void_p
xcb_visualid_t: c_void_p

VULKAN_XCB_H_: int = 1
VK_KHR_XCB_SURFACE_SPEC_VERSION: int = 6
VK_KHR_XCB_SURFACE_EXTENSION_NAME: str = "VK_KHR_xcb_surface"
VkXcbSurfaceCreateFlagsKHR: VkFlags
def vkCreateXcbSurfaceKHR(instance: VkInstance, pCreateInfo: POINTER(VkXcbSurfaceCreateInfoKHR), pAllocator: POINTER(VkAllocationCallbacks), pSurface: POINTER(VkSurfaceKHR)) -> VkResult:
    ...

def vkGetPhysicalDeviceXcbPresentationSupportKHR(physicalDevice: VkPhysicalDevice, queueFamilyIndex: int, connection: POINTER(xcb_connection_t), visual_id: xcb_visualid_t) -> VkBool32:
    ...

class VkXcbSurfaceCreateInfoKHR(Structure):
    sType: VkStructureType
    pNext: c_void_p
    flags: VkXcbSurfaceCreateFlagsKHR
    connection: POINTER(xcb_connection_t)
    window: xcb_window_t

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 flags: VkXcbSurfaceCreateFlagsKHR | None = None,
                 connection: POINTER(xcb_connection_t) | None = None,
                 window: xcb_window_t | None = None,
    ) -> None: ...

