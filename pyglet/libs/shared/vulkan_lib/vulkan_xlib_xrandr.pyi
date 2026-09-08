from ctypes import POINTER
from pyglet.libs.x11.xlib import Display, XID

RROutput: XID

from pyglet.libs.shared.vulkan_lib.vulkan_core import VkPhysicalDevice, VkResult, VkDisplayKHR

VULKAN_XLIB_XRANDR_H_: int = 1
VK_EXT_ACQUIRE_XLIB_DISPLAY_SPEC_VERSION: int = 1
VK_EXT_ACQUIRE_XLIB_DISPLAY_EXTENSION_NAME: str = "VK_EXT_acquire_xlib_display"
def vkAcquireXlibDisplayEXT(physicalDevice: VkPhysicalDevice, dpy: POINTER(Display), display: VkDisplayKHR) -> VkResult:
    ...

def vkGetRandROutputDisplayEXT(physicalDevice: VkPhysicalDevice, dpy: POINTER(Display), rrOutput: RROutput, pDisplay: POINTER(VkDisplayKHR)) -> VkResult:
    ...

