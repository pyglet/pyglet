
CTypesDataType = Type[_SimpleCData]
CTypesPointer = _Pointer

from ctypes import c_int, c_int8, c_uint8, c_int16, c_uint16, c_int32, c_uint32, c_int64, c_uint64, c_size_t, c_float, c_double, c_char, c_char_p, c_void_p, POINTER, Structure, Union, cast, CFUNCTYPE

VULKAN_XLIB_H_: int = 1
VK_KHR_XLIB_SURFACE_SPEC_VERSION: int = 6
VK_KHR_XLIB_SURFACE_EXTENSION_NAME: str = "VK_KHR_xlib_surface"
VkXlibSurfaceCreateFlagsKHR: VkFlags
def vkCreateXlibSurfaceKHR(instance: VkInstance, pCreateInfo: POINTER(VkXlibSurfaceCreateInfoKHR), pAllocator: POINTER(VkAllocationCallbacks), pSurface: POINTER(VkSurfaceKHR)) -> VkResult:
    ...

def vkGetPhysicalDeviceXlibPresentationSupportKHR(physicalDevice: VkPhysicalDevice, queueFamilyIndex: int, dpy: POINTER(Display), visualID: VisualID) -> VkBool32:
    ...

class VkXlibSurfaceCreateInfoKHR(Structure):
    sType: VkStructureType
    pNext: c_void_p
    flags: VkXlibSurfaceCreateFlagsKHR
    dpy: POINTER(Display)
    window: Window

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 flags: VkXlibSurfaceCreateFlagsKHR | None = None,
                 dpy: POINTER(Display) | None = None,
                 window: Window | None = None,
    ) -> None: ...

