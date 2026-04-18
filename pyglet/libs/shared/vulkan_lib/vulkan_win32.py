#
# Vulkan wrapper generated from Vulkan headers
#
from __future__ import annotations

from ctypes import POINTER, c_uint32, CFUNCTYPE, c_void_p, c_uint64, c_int32
from ctypes.wintypes import HINSTANCE, HWND, HANDLE, LPCWSTR, DWORD, HMONITOR

from pyglet.libs.win32 import SECURITY_ATTRIBUTES
from . import define_struct
from .vulkan_core import (VkAllocationCallbacks, VkBool32, VkDevice,
                          VkDeviceGroupPresentModeFlagsKHR, VkDeviceMemory, VkDisplayKHR,
                          VkExternalFenceHandleTypeFlagBits, VkExternalMemoryHandleTypeFlagBits,
                          VkExternalMemoryHandleTypeFlagsNV, VkExternalSemaphoreHandleTypeFlagBits,
                          VkFence, VkFenceImportFlags, VkFlags, VkInstance, VkPhysicalDevice,
                          VkPhysicalDeviceSurfaceInfo2KHR, VkPresentModeKHR, VkResult, VkSemaphore,
                          VkSemaphoreImportFlags, VkStructureType, VkSurfaceKHR, VkSwapchainKHR)

VULKAN_WIN32_H_: int = 1

VK_KHR_WIN32_SURFACE_SPEC_VERSION: int = 6
VK_KHR_WIN32_SURFACE_EXTENSION_NAME: str = "VK_KHR_win32_surface"
VkWin32SurfaceCreateFlagsKHR: type[VkFlags] = VkFlags
VkWin32SurfaceCreateInfoKHR = define_struct('VkWin32SurfaceCreateInfoKHR',
    ('sType', VkStructureType),
    ('pNext', POINTER(None)),
    ('flags', VkWin32SurfaceCreateFlagsKHR),
    ('hinstance', HINSTANCE),
    ('hwnd', HWND),
)

PFN_vkCreateWin32SurfaceKHR = CFUNCTYPE(VkResult, VkInstance, POINTER(VkWin32SurfaceCreateInfoKHR), POINTER(VkAllocationCallbacks), POINTER(VkSurfaceKHR))
PFN_vkGetPhysicalDeviceWin32PresentationSupportKHR = CFUNCTYPE(VkBool32, VkPhysicalDevice, c_uint32)

VK_KHR_EXTERNAL_MEMORY_WIN32_SPEC_VERSION: int = 1
VK_KHR_EXTERNAL_MEMORY_WIN32_EXTENSION_NAME: str = "VK_KHR_external_memory_win32"
VkImportMemoryWin32HandleInfoKHR = define_struct('VkImportMemoryWin32HandleInfoKHR',
    ('sType', VkStructureType),
    ('pNext', POINTER(None)),
    ('handleType', VkExternalMemoryHandleTypeFlagBits),
    ('handle', HANDLE),
    ('name', LPCWSTR),
)

VkExportMemoryWin32HandleInfoKHR = define_struct('VkExportMemoryWin32HandleInfoKHR',
    ('sType', VkStructureType),
    ('pNext', POINTER(None)),
    ('pAttributes', POINTER(SECURITY_ATTRIBUTES)),
    ('dwAccess', DWORD),
    ('name', LPCWSTR),
)

VkMemoryWin32HandlePropertiesKHR = define_struct('VkMemoryWin32HandlePropertiesKHR',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('memoryTypeBits', c_uint32),
)

VkMemoryGetWin32HandleInfoKHR = define_struct('VkMemoryGetWin32HandleInfoKHR',
    ('sType', VkStructureType),
    ('pNext', POINTER(None)),
    ('memory', VkDeviceMemory),
    ('handleType', VkExternalMemoryHandleTypeFlagBits),
)

PFN_vkGetMemoryWin32HandleKHR = CFUNCTYPE(VkResult, VkDevice, POINTER(VkMemoryGetWin32HandleInfoKHR), POINTER(HANDLE))
PFN_vkGetMemoryWin32HandlePropertiesKHR = CFUNCTYPE(VkResult, VkDevice, VkExternalMemoryHandleTypeFlagBits, HANDLE, POINTER(VkMemoryWin32HandlePropertiesKHR))

VK_KHR_WIN32_KEYED_MUTEX_SPEC_VERSION: int = 1
VK_KHR_WIN32_KEYED_MUTEX_EXTENSION_NAME: str = "VK_KHR_win32_keyed_mutex"
VkWin32KeyedMutexAcquireReleaseInfoKHR = define_struct('VkWin32KeyedMutexAcquireReleaseInfoKHR',
    ('sType', VkStructureType),
    ('pNext', POINTER(None)),
    ('acquireCount', c_uint32),
    ('pAcquireSyncs', POINTER(VkDeviceMemory)),
    ('pAcquireKeys', POINTER(c_uint64)),
    ('pAcquireTimeouts', POINTER(c_uint32)),
    ('releaseCount', c_uint32),
    ('pReleaseSyncs', POINTER(VkDeviceMemory)),
    ('pReleaseKeys', POINTER(c_uint64)),
)


VK_KHR_EXTERNAL_SEMAPHORE_WIN32_SPEC_VERSION: int = 1
VK_KHR_EXTERNAL_SEMAPHORE_WIN32_EXTENSION_NAME: str = "VK_KHR_external_semaphore_win32"
VkImportSemaphoreWin32HandleInfoKHR = define_struct('VkImportSemaphoreWin32HandleInfoKHR',
    ('sType', VkStructureType),
    ('pNext', POINTER(None)),
    ('semaphore', VkSemaphore),
    ('flags', VkSemaphoreImportFlags),
    ('handleType', VkExternalSemaphoreHandleTypeFlagBits),
    ('handle', HANDLE),
    ('name', LPCWSTR),
)

VkExportSemaphoreWin32HandleInfoKHR = define_struct('VkExportSemaphoreWin32HandleInfoKHR',
    ('sType', VkStructureType),
    ('pNext', POINTER(None)),
    ('pAttributes', POINTER(SECURITY_ATTRIBUTES)),
    ('dwAccess', DWORD),
    ('name', LPCWSTR),
)

VkD3D12FenceSubmitInfoKHR = define_struct('VkD3D12FenceSubmitInfoKHR',
    ('sType', VkStructureType),
    ('pNext', POINTER(None)),
    ('waitSemaphoreValuesCount', c_uint32),
    ('pWaitSemaphoreValues', POINTER(c_uint64)),
    ('signalSemaphoreValuesCount', c_uint32),
    ('pSignalSemaphoreValues', POINTER(c_uint64)),
)

VkSemaphoreGetWin32HandleInfoKHR = define_struct('VkSemaphoreGetWin32HandleInfoKHR',
    ('sType', VkStructureType),
    ('pNext', POINTER(None)),
    ('semaphore', VkSemaphore),
    ('handleType', VkExternalSemaphoreHandleTypeFlagBits),
)

PFN_vkImportSemaphoreWin32HandleKHR = CFUNCTYPE(VkResult, VkDevice, POINTER(VkImportSemaphoreWin32HandleInfoKHR))
PFN_vkGetSemaphoreWin32HandleKHR = CFUNCTYPE(VkResult, VkDevice, POINTER(VkSemaphoreGetWin32HandleInfoKHR), POINTER(HANDLE))

VK_KHR_EXTERNAL_FENCE_WIN32_SPEC_VERSION: int = 1
VK_KHR_EXTERNAL_FENCE_WIN32_EXTENSION_NAME: str = "VK_KHR_external_fence_win32"
VkImportFenceWin32HandleInfoKHR = define_struct('VkImportFenceWin32HandleInfoKHR',
    ('sType', VkStructureType),
    ('pNext', POINTER(None)),
    ('fence', VkFence),
    ('flags', VkFenceImportFlags),
    ('handleType', VkExternalFenceHandleTypeFlagBits),
    ('handle', HANDLE),
    ('name', LPCWSTR),
)

VkExportFenceWin32HandleInfoKHR = define_struct('VkExportFenceWin32HandleInfoKHR',
    ('sType', VkStructureType),
    ('pNext', POINTER(None)),
    ('pAttributes', POINTER(SECURITY_ATTRIBUTES)),
    ('dwAccess', DWORD),
    ('name', LPCWSTR),
)

VkFenceGetWin32HandleInfoKHR = define_struct('VkFenceGetWin32HandleInfoKHR',
    ('sType', VkStructureType),
    ('pNext', POINTER(None)),
    ('fence', VkFence),
    ('handleType', VkExternalFenceHandleTypeFlagBits),
)

PFN_vkImportFenceWin32HandleKHR = CFUNCTYPE(VkResult, VkDevice, POINTER(VkImportFenceWin32HandleInfoKHR))
PFN_vkGetFenceWin32HandleKHR = CFUNCTYPE(VkResult, VkDevice, POINTER(VkFenceGetWin32HandleInfoKHR), POINTER(HANDLE))

VK_NV_EXTERNAL_MEMORY_WIN32_SPEC_VERSION: int = 1
VK_NV_EXTERNAL_MEMORY_WIN32_EXTENSION_NAME: str = "VK_NV_external_memory_win32"
VkImportMemoryWin32HandleInfoNV = define_struct('VkImportMemoryWin32HandleInfoNV',
    ('sType', VkStructureType),
    ('pNext', POINTER(None)),
    ('handleType', VkExternalMemoryHandleTypeFlagsNV),
    ('handle', HANDLE),
)

VkExportMemoryWin32HandleInfoNV = define_struct('VkExportMemoryWin32HandleInfoNV',
    ('sType', VkStructureType),
    ('pNext', POINTER(None)),
    ('pAttributes', POINTER(SECURITY_ATTRIBUTES)),
    ('dwAccess', DWORD),
)

PFN_vkGetMemoryWin32HandleNV = CFUNCTYPE(VkResult, VkDevice, VkDeviceMemory, VkExternalMemoryHandleTypeFlagsNV, POINTER(HANDLE))

VK_NV_WIN32_KEYED_MUTEX_SPEC_VERSION: int = 2
VK_NV_WIN32_KEYED_MUTEX_EXTENSION_NAME: str = "VK_NV_win32_keyed_mutex"
VkWin32KeyedMutexAcquireReleaseInfoNV = define_struct('VkWin32KeyedMutexAcquireReleaseInfoNV',
    ('sType', VkStructureType),
    ('pNext', POINTER(None)),
    ('acquireCount', c_uint32),
    ('pAcquireSyncs', POINTER(VkDeviceMemory)),
    ('pAcquireKeys', POINTER(c_uint64)),
    ('pAcquireTimeoutMilliseconds', POINTER(c_uint32)),
    ('releaseCount', c_uint32),
    ('pReleaseSyncs', POINTER(VkDeviceMemory)),
    ('pReleaseKeys', POINTER(c_uint64)),
)


VK_EXT_FULL_SCREEN_EXCLUSIVE_SPEC_VERSION: int = 4
VK_EXT_FULL_SCREEN_EXCLUSIVE_EXTENSION_NAME: str = "VK_EXT_full_screen_exclusive"

VkFullScreenExclusiveEXT = c_int32
VK_FULL_SCREEN_EXCLUSIVE_DEFAULT_EXT: int = 0
VK_FULL_SCREEN_EXCLUSIVE_ALLOWED_EXT: int = 1
VK_FULL_SCREEN_EXCLUSIVE_DISALLOWED_EXT: int = 2
VK_FULL_SCREEN_EXCLUSIVE_APPLICATION_CONTROLLED_EXT: int = 3
VK_FULL_SCREEN_EXCLUSIVE_MAX_ENUM_EXT: int = 0x7FFFFFFF
VkSurfaceFullScreenExclusiveInfoEXT = define_struct('VkSurfaceFullScreenExclusiveInfoEXT',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('fullScreenExclusive', VkFullScreenExclusiveEXT),
)

VkSurfaceCapabilitiesFullScreenExclusiveEXT = define_struct('VkSurfaceCapabilitiesFullScreenExclusiveEXT',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('fullScreenExclusiveSupported', VkBool32),
)

VkSurfaceFullScreenExclusiveWin32InfoEXT = define_struct('VkSurfaceFullScreenExclusiveWin32InfoEXT',
    ('sType', VkStructureType),
    ('pNext', POINTER(None)),
    ('hmonitor', HMONITOR),
)

PFN_vkGetPhysicalDeviceSurfacePresentModes2EXT = CFUNCTYPE(VkResult, VkPhysicalDevice, POINTER(VkPhysicalDeviceSurfaceInfo2KHR), POINTER(c_uint32), POINTER(VkPresentModeKHR))
PFN_vkAcquireFullScreenExclusiveModeEXT = CFUNCTYPE(VkResult, VkDevice, VkSwapchainKHR)
PFN_vkReleaseFullScreenExclusiveModeEXT = CFUNCTYPE(VkResult, VkDevice, VkSwapchainKHR)
PFN_vkGetDeviceGroupSurfacePresentModes2EXT = CFUNCTYPE(VkResult, VkDevice, POINTER(VkPhysicalDeviceSurfaceInfo2KHR), POINTER(VkDeviceGroupPresentModeFlagsKHR))

VK_NV_ACQUIRE_WINRT_DISPLAY_SPEC_VERSION: int = 1
VK_NV_ACQUIRE_WINRT_DISPLAY_EXTENSION_NAME: str = "VK_NV_acquire_winrt_display"
PFN_vkAcquireWinrtDisplayNV = CFUNCTYPE(VkResult, VkPhysicalDevice, VkDisplayKHR)
PFN_vkGetWinrtDisplayNV = CFUNCTYPE(VkResult, VkPhysicalDevice, c_uint32, POINTER(VkDisplayKHR))
InstanceFunctions = (
  ("vkCreateWin32SurfaceKHR", PFN_vkCreateWin32SurfaceKHR),
  ("vkGetPhysicalDeviceWin32PresentationSupportKHR", PFN_vkGetPhysicalDeviceWin32PresentationSupportKHR),
  ("vkGetPhysicalDeviceSurfacePresentModes2EXT", PFN_vkGetPhysicalDeviceSurfacePresentModes2EXT),
  ("vkAcquireWinrtDisplayNV", PFN_vkAcquireWinrtDisplayNV),
  ("vkGetWinrtDisplayNV", PFN_vkGetWinrtDisplayNV),
)

DeviceFunctions = (
  ("vkGetMemoryWin32HandleKHR", PFN_vkGetMemoryWin32HandleKHR),
  ("vkGetMemoryWin32HandlePropertiesKHR", PFN_vkGetMemoryWin32HandlePropertiesKHR),
  ("vkImportSemaphoreWin32HandleKHR", PFN_vkImportSemaphoreWin32HandleKHR),
  ("vkGetSemaphoreWin32HandleKHR", PFN_vkGetSemaphoreWin32HandleKHR),
  ("vkImportFenceWin32HandleKHR", PFN_vkImportFenceWin32HandleKHR),
  ("vkGetFenceWin32HandleKHR", PFN_vkGetFenceWin32HandleKHR),
  ("vkGetMemoryWin32HandleNV", PFN_vkGetMemoryWin32HandleNV),
  ("vkAcquireFullScreenExclusiveModeEXT", PFN_vkAcquireFullScreenExclusiveModeEXT),
  ("vkReleaseFullScreenExclusiveModeEXT", PFN_vkReleaseFullScreenExclusiveModeEXT),
  ("vkGetDeviceGroupSurfacePresentModes2EXT", PFN_vkGetDeviceGroupSurfacePresentModes2EXT),
)

LoaderFunctions = (
)

