from __future__ import annotations

from ctypes import POINTER, c_uint32, c_void_p, c_uint64, c_int32, Structure
from ctypes.wintypes import HINSTANCE, HWND, HANDLE, LPCWSTR, DWORD, HMONITOR

from pyglet.libs.win32 import SECURITY_ATTRIBUTES
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
VkWin32SurfaceCreateFlagsKHR: type[VkFlags]
def vkCreateWin32SurfaceKHR(instance: VkInstance, pCreateInfo: POINTER(VkWin32SurfaceCreateInfoKHR), pAllocator: POINTER(VkAllocationCallbacks), pSurface: POINTER(VkSurfaceKHR)) -> VkResult:
    ...

def vkGetPhysicalDeviceWin32PresentationSupportKHR(physicalDevice: VkPhysicalDevice, queueFamilyIndex: c_uint32) -> VkBool32:
    ...

VK_KHR_EXTERNAL_MEMORY_WIN32_SPEC_VERSION: int = 1
VK_KHR_EXTERNAL_MEMORY_WIN32_EXTENSION_NAME: str = "VK_KHR_external_memory_win32"
def vkGetMemoryWin32HandleKHR(device: VkDevice, pGetWin32HandleInfo: POINTER(VkMemoryGetWin32HandleInfoKHR), pHandle: POINTER(HANDLE)) -> VkResult:
    ...

def vkGetMemoryWin32HandlePropertiesKHR(device: VkDevice, handleType: VkExternalMemoryHandleTypeFlagBits, handle: HANDLE, pMemoryWin32HandleProperties: POINTER(VkMemoryWin32HandlePropertiesKHR)) -> VkResult:
    ...

VK_KHR_WIN32_KEYED_MUTEX_SPEC_VERSION: int = 1
VK_KHR_WIN32_KEYED_MUTEX_EXTENSION_NAME: str = "VK_KHR_win32_keyed_mutex"
VK_KHR_EXTERNAL_SEMAPHORE_WIN32_SPEC_VERSION: int = 1
VK_KHR_EXTERNAL_SEMAPHORE_WIN32_EXTENSION_NAME: str = "VK_KHR_external_semaphore_win32"
def vkImportSemaphoreWin32HandleKHR(device: VkDevice, pImportSemaphoreWin32HandleInfo: POINTER(VkImportSemaphoreWin32HandleInfoKHR)) -> VkResult:
    ...

def vkGetSemaphoreWin32HandleKHR(device: VkDevice, pGetWin32HandleInfo: POINTER(VkSemaphoreGetWin32HandleInfoKHR), pHandle: POINTER(HANDLE)) -> VkResult:
    ...

VK_KHR_EXTERNAL_FENCE_WIN32_SPEC_VERSION: int = 1
VK_KHR_EXTERNAL_FENCE_WIN32_EXTENSION_NAME: str = "VK_KHR_external_fence_win32"
def vkImportFenceWin32HandleKHR(device: VkDevice, pImportFenceWin32HandleInfo: POINTER(VkImportFenceWin32HandleInfoKHR)) -> VkResult:
    ...

def vkGetFenceWin32HandleKHR(device: VkDevice, pGetWin32HandleInfo: POINTER(VkFenceGetWin32HandleInfoKHR), pHandle: POINTER(HANDLE)) -> VkResult:
    ...

VK_NV_EXTERNAL_MEMORY_WIN32_SPEC_VERSION: int = 1
VK_NV_EXTERNAL_MEMORY_WIN32_EXTENSION_NAME: str = "VK_NV_external_memory_win32"
def vkGetMemoryWin32HandleNV(device: VkDevice, memory: VkDeviceMemory, handleType: VkExternalMemoryHandleTypeFlagsNV, pHandle: POINTER(HANDLE)) -> VkResult:
    ...

VK_NV_WIN32_KEYED_MUTEX_SPEC_VERSION: int = 2
VK_NV_WIN32_KEYED_MUTEX_EXTENSION_NAME: str = "VK_NV_win32_keyed_mutex"
VK_EXT_FULL_SCREEN_EXCLUSIVE_SPEC_VERSION: int = 4
VK_EXT_FULL_SCREEN_EXCLUSIVE_EXTENSION_NAME: str = "VK_EXT_full_screen_exclusive"

VkFullScreenExclusiveEXT: type[c_int32]
VK_FULL_SCREEN_EXCLUSIVE_DEFAULT_EXT: int = 0
VK_FULL_SCREEN_EXCLUSIVE_ALLOWED_EXT: int = 1
VK_FULL_SCREEN_EXCLUSIVE_DISALLOWED_EXT: int = 2
VK_FULL_SCREEN_EXCLUSIVE_APPLICATION_CONTROLLED_EXT: int = 3
VK_FULL_SCREEN_EXCLUSIVE_MAX_ENUM_EXT: int = 0x7FFFFFFF
def vkGetPhysicalDeviceSurfacePresentModes2EXT(physicalDevice: VkPhysicalDevice, pSurfaceInfo: POINTER(VkPhysicalDeviceSurfaceInfo2KHR), pPresentModeCount: POINTER(c_uint32), pPresentModes: POINTER(VkPresentModeKHR)) -> VkResult:
    ...

def vkAcquireFullScreenExclusiveModeEXT(device: VkDevice, swapchain: VkSwapchainKHR) -> VkResult:
    ...

def vkReleaseFullScreenExclusiveModeEXT(device: VkDevice, swapchain: VkSwapchainKHR) -> VkResult:
    ...

def vkGetDeviceGroupSurfacePresentModes2EXT(device: VkDevice, pSurfaceInfo: POINTER(VkPhysicalDeviceSurfaceInfo2KHR), pModes: POINTER(VkDeviceGroupPresentModeFlagsKHR)) -> VkResult:
    ...

VK_NV_ACQUIRE_WINRT_DISPLAY_SPEC_VERSION: int = 1
VK_NV_ACQUIRE_WINRT_DISPLAY_EXTENSION_NAME: str = "VK_NV_acquire_winrt_display"
def vkAcquireWinrtDisplayNV(physicalDevice: VkPhysicalDevice, display: VkDisplayKHR) -> VkResult:
    ...

def vkGetWinrtDisplayNV(physicalDevice: VkPhysicalDevice, deviceRelativeId: c_uint32, pDisplay: POINTER(VkDisplayKHR)) -> VkResult:
    ...

class VkWin32SurfaceCreateInfoKHR(Structure):
    sType: VkStructureType
    pNext: POINTER(None)
    flags: VkWin32SurfaceCreateFlagsKHR
    hinstance: HINSTANCE
    hwnd: HWND

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: POINTER(None) | None = None,
                 flags: VkWin32SurfaceCreateFlagsKHR | None = None,
                 hinstance: HINSTANCE | None = None,
                 hwnd: HWND | None = None,
    ) -> None: ...

class VkImportMemoryWin32HandleInfoKHR(Structure):
    sType: VkStructureType
    pNext: POINTER(None)
    handleType: VkExternalMemoryHandleTypeFlagBits
    handle: HANDLE
    name: LPCWSTR

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: POINTER(None) | None = None,
                 handleType: VkExternalMemoryHandleTypeFlagBits | None = None,
                 handle: HANDLE | None = None,
                 name: LPCWSTR | None = None,
    ) -> None: ...

class VkExportMemoryWin32HandleInfoKHR(Structure):
    sType: VkStructureType
    pNext: POINTER(None)
    pAttributes: POINTER(SECURITY_ATTRIBUTES)
    dwAccess: DWORD
    name: LPCWSTR

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: POINTER(None) | None = None,
                 pAttributes: POINTER(SECURITY_ATTRIBUTES) | None = None,
                 dwAccess: DWORD | None = None,
                 name: LPCWSTR | None = None,
    ) -> None: ...

class VkMemoryWin32HandlePropertiesKHR(Structure):
    sType: VkStructureType
    pNext: c_void_p
    memoryTypeBits: c_uint32

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 memoryTypeBits: c_uint32 | None = None,
    ) -> None: ...

class VkMemoryGetWin32HandleInfoKHR(Structure):
    sType: VkStructureType
    pNext: POINTER(None)
    memory: VkDeviceMemory
    handleType: VkExternalMemoryHandleTypeFlagBits

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: POINTER(None) | None = None,
                 memory: VkDeviceMemory | None = None,
                 handleType: VkExternalMemoryHandleTypeFlagBits | None = None,
    ) -> None: ...

class VkWin32KeyedMutexAcquireReleaseInfoKHR(Structure):
    sType: VkStructureType
    pNext: POINTER(None)
    acquireCount: c_uint32
    pAcquireSyncs: POINTER(VkDeviceMemory)
    pAcquireKeys: POINTER(c_uint64)
    pAcquireTimeouts: POINTER(c_uint32)
    releaseCount: c_uint32
    pReleaseSyncs: POINTER(VkDeviceMemory)
    pReleaseKeys: POINTER(c_uint64)

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: POINTER(None) | None = None,
                 acquireCount: c_uint32 | None = None,
                 pAcquireSyncs: POINTER(VkDeviceMemory) | None = None,
                 pAcquireKeys: POINTER(c_uint64) | None = None,
                 pAcquireTimeouts: POINTER(c_uint32) | None = None,
                 releaseCount: c_uint32 | None = None,
                 pReleaseSyncs: POINTER(VkDeviceMemory) | None = None,
                 pReleaseKeys: POINTER(c_uint64) | None = None,
    ) -> None: ...

class VkImportSemaphoreWin32HandleInfoKHR(Structure):
    sType: VkStructureType
    pNext: POINTER(None)
    semaphore: VkSemaphore
    flags: VkSemaphoreImportFlags
    handleType: VkExternalSemaphoreHandleTypeFlagBits
    handle: HANDLE
    name: LPCWSTR

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: POINTER(None) | None = None,
                 semaphore: VkSemaphore | None = None,
                 flags: VkSemaphoreImportFlags | None = None,
                 handleType: VkExternalSemaphoreHandleTypeFlagBits | None = None,
                 handle: HANDLE | None = None,
                 name: LPCWSTR | None = None,
    ) -> None: ...

class VkExportSemaphoreWin32HandleInfoKHR(Structure):
    sType: VkStructureType
    pNext: POINTER(None)
    pAttributes: POINTER(SECURITY_ATTRIBUTES)
    dwAccess: DWORD
    name: LPCWSTR

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: POINTER(None) | None = None,
                 pAttributes: POINTER(SECURITY_ATTRIBUTES) | None = None,
                 dwAccess: DWORD | None = None,
                 name: LPCWSTR | None = None,
    ) -> None: ...

class VkD3D12FenceSubmitInfoKHR(Structure):
    sType: VkStructureType
    pNext: POINTER(None)
    waitSemaphoreValuesCount: c_uint32
    pWaitSemaphoreValues: POINTER(c_uint64)
    signalSemaphoreValuesCount: c_uint32
    pSignalSemaphoreValues: POINTER(c_uint64)

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: POINTER(None) | None = None,
                 waitSemaphoreValuesCount: c_uint32 | None = None,
                 pWaitSemaphoreValues: POINTER(c_uint64) | None = None,
                 signalSemaphoreValuesCount: c_uint32 | None = None,
                 pSignalSemaphoreValues: POINTER(c_uint64) | None = None,
    ) -> None: ...

class VkSemaphoreGetWin32HandleInfoKHR(Structure):
    sType: VkStructureType
    pNext: POINTER(None)
    semaphore: VkSemaphore
    handleType: VkExternalSemaphoreHandleTypeFlagBits

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: POINTER(None) | None = None,
                 semaphore: VkSemaphore | None = None,
                 handleType: VkExternalSemaphoreHandleTypeFlagBits | None = None,
    ) -> None: ...

class VkImportFenceWin32HandleInfoKHR(Structure):
    sType: VkStructureType
    pNext: POINTER(None)
    fence: VkFence
    flags: VkFenceImportFlags
    handleType: VkExternalFenceHandleTypeFlagBits
    handle: HANDLE
    name: LPCWSTR

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: POINTER(None) | None = None,
                 fence: VkFence | None = None,
                 flags: VkFenceImportFlags | None = None,
                 handleType: VkExternalFenceHandleTypeFlagBits | None = None,
                 handle: HANDLE | None = None,
                 name: LPCWSTR | None = None,
    ) -> None: ...

class VkExportFenceWin32HandleInfoKHR(Structure):
    sType: VkStructureType
    pNext: POINTER(None)
    pAttributes: POINTER(SECURITY_ATTRIBUTES)
    dwAccess: DWORD
    name: LPCWSTR

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: POINTER(None) | None = None,
                 pAttributes: POINTER(SECURITY_ATTRIBUTES) | None = None,
                 dwAccess: DWORD | None = None,
                 name: LPCWSTR | None = None,
    ) -> None: ...

class VkFenceGetWin32HandleInfoKHR(Structure):
    sType: VkStructureType
    pNext: POINTER(None)
    fence: VkFence
    handleType: VkExternalFenceHandleTypeFlagBits

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: POINTER(None) | None = None,
                 fence: VkFence | None = None,
                 handleType: VkExternalFenceHandleTypeFlagBits | None = None,
    ) -> None: ...

class VkImportMemoryWin32HandleInfoNV(Structure):
    sType: VkStructureType
    pNext: POINTER(None)
    handleType: VkExternalMemoryHandleTypeFlagsNV
    handle: HANDLE

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: POINTER(None) | None = None,
                 handleType: VkExternalMemoryHandleTypeFlagsNV | None = None,
                 handle: HANDLE | None = None,
    ) -> None: ...

class VkExportMemoryWin32HandleInfoNV(Structure):
    sType: VkStructureType
    pNext: POINTER(None)
    pAttributes: POINTER(SECURITY_ATTRIBUTES)
    dwAccess: DWORD

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: POINTER(None) | None = None,
                 pAttributes: POINTER(SECURITY_ATTRIBUTES) | None = None,
                 dwAccess: DWORD | None = None,
    ) -> None: ...

class VkWin32KeyedMutexAcquireReleaseInfoNV(Structure):
    sType: VkStructureType
    pNext: POINTER(None)
    acquireCount: c_uint32
    pAcquireSyncs: POINTER(VkDeviceMemory)
    pAcquireKeys: POINTER(c_uint64)
    pAcquireTimeoutMilliseconds: POINTER(c_uint32)
    releaseCount: c_uint32
    pReleaseSyncs: POINTER(VkDeviceMemory)
    pReleaseKeys: POINTER(c_uint64)

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: POINTER(None) | None = None,
                 acquireCount: c_uint32 | None = None,
                 pAcquireSyncs: POINTER(VkDeviceMemory) | None = None,
                 pAcquireKeys: POINTER(c_uint64) | None = None,
                 pAcquireTimeoutMilliseconds: POINTER(c_uint32) | None = None,
                 releaseCount: c_uint32 | None = None,
                 pReleaseSyncs: POINTER(VkDeviceMemory) | None = None,
                 pReleaseKeys: POINTER(c_uint64) | None = None,
    ) -> None: ...

class VkSurfaceFullScreenExclusiveInfoEXT(Structure):
    sType: VkStructureType
    pNext: c_void_p
    fullScreenExclusive: VkFullScreenExclusiveEXT

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 fullScreenExclusive: VkFullScreenExclusiveEXT | None = None,
    ) -> None: ...

class VkSurfaceCapabilitiesFullScreenExclusiveEXT(Structure):
    sType: VkStructureType
    pNext: c_void_p
    fullScreenExclusiveSupported: VkBool32

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 fullScreenExclusiveSupported: VkBool32 | None = None,
    ) -> None: ...

class VkSurfaceFullScreenExclusiveWin32InfoEXT(Structure):
    sType: VkStructureType
    pNext: POINTER(None)
    hmonitor: HMONITOR

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: POINTER(None) | None = None,
                 hmonitor: HMONITOR | None = None,
    ) -> None: ...

