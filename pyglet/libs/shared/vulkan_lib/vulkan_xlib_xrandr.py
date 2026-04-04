from ctypes import POINTER, CFUNCTYPE

from pyglet.libs.x11.xlib import Display, XID
from .vulkan_core import VkResult, VkPhysicalDevice, VkDisplayKHR

RROutput = XID

VULKAN_XLIB_XRANDR_H_: int = 1

VK_EXT_ACQUIRE_XLIB_DISPLAY_SPEC_VERSION: int = 1
VK_EXT_ACQUIRE_XLIB_DISPLAY_EXTENSION_NAME: str = "VK_EXT_acquire_xlib_display"
PFN_vkAcquireXlibDisplayEXT = CFUNCTYPE(VkResult, VkPhysicalDevice, POINTER(Display), VkDisplayKHR)
PFN_vkGetRandROutputDisplayEXT = CFUNCTYPE(VkResult, VkPhysicalDevice, POINTER(Display), RROutput, POINTER(VkDisplayKHR))  # noqa: F821
InstanceFunctions = (
  ("vkAcquireXlibDisplayEXT", PFN_vkAcquireXlibDisplayEXT),
  ("vkGetRandROutputDisplayEXT", PFN_vkGetRandROutputDisplayEXT),
)

DeviceFunctions = (
)

LoaderFunctions = (
)

