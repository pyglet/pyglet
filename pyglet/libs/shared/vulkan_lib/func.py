from __future__ import annotations

from .exceptions import VulkanNoInstance, VulkanNoLogicalDevice

from typing import TYPE_CHECKING

from _ctypes import _Pointer

if TYPE_CHECKING:
    from .vulkan_core import *
    from ctypes import c_uint32, c_size_t, Array, c_int32, c_uint64, c_float


class InstanceFunc:
    @staticmethod
    def vkDestroyInstance(instance: VkInstance, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkEnumeratePhysicalDevices(instance: VkInstance, pPhysicalDeviceCount: CTypesPointer[c_uint32] | None, pPhysicalDevices: CTypesPointer[VkPhysicalDevice] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetDeviceProcAddr(device: VkDevice, pName: bytes) -> PFN_vkVoidFunction:
        raise VulkanNoInstance

    @staticmethod
    def vkGetInstanceProcAddr(instance: VkInstance, pName: bytes) -> PFN_vkVoidFunction:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceProperties(physicalDevice: VkPhysicalDevice, pProperties: CTypesPointer[VkPhysicalDeviceProperties]) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceQueueFamilyProperties(physicalDevice: VkPhysicalDevice, pQueueFamilyPropertyCount: CTypesPointer[c_uint32] | None, pQueueFamilyProperties: CTypesPointer[VkQueueFamilyProperties] | None) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceMemoryProperties(physicalDevice: VkPhysicalDevice, pMemoryProperties: CTypesPointer[VkPhysicalDeviceMemoryProperties]) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceFeatures(physicalDevice: VkPhysicalDevice, pFeatures: CTypesPointer[VkPhysicalDeviceFeatures]) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceFormatProperties(physicalDevice: VkPhysicalDevice, format: VkFormat, pFormatProperties: CTypesPointer[VkFormatProperties]) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceImageFormatProperties(physicalDevice: VkPhysicalDevice, format: VkFormat, type: VkImageType, tiling: VkImageTiling, usage: VkImageUsageFlags, flags: VkImageCreateFlags, pImageFormatProperties: CTypesPointer[VkImageFormatProperties]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkCreateDevice(physicalDevice: VkPhysicalDevice, pCreateInfo: CTypesPointer[VkDeviceCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pDevice: CTypesPointer[VkDevice]) -> int:
        raise VulkanNoInstance

    @staticmethod
    def vkEnumerateDeviceLayerProperties(physicalDevice: VkPhysicalDevice, pPropertyCount: CTypesPointer[c_uint32] | None, pProperties: CTypesPointer[VkLayerProperties] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkEnumerateDeviceLayerProperties(physicalDevice: VkPhysicalDevice, pPropertyCount: CTypesPointer[c_uint32] | None, pProperties: CTypesPointer[VkLayerProperties] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkEnumerateDeviceExtensionProperties(physicalDevice: VkPhysicalDevice, pLayerName: bytes, pPropertyCount: CTypesPointer[c_uint32] | None, pProperties: CTypesPointer[VkExtensionProperties] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceSparseImageFormatProperties(physicalDevice: VkPhysicalDevice, format: VkFormat, type: VkImageType, samples: VkSampleCountFlagBits, usage: VkImageUsageFlags, tiling: VkImageTiling, pPropertyCount: CTypesPointer[c_uint32] | None, pProperties: CTypesPointer[VkSparseImageFormatProperties] | None) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkCreateAndroidSurfaceKHR(instance: VkInstance, pCreateInfo: CTypesPointer[VkAndroidSurfaceCreateInfoKHR], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSurface: CTypesPointer[VkSurfaceKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceDisplayPropertiesKHR(physicalDevice: VkPhysicalDevice, pPropertyCount: CTypesPointer[c_uint32] | None, pProperties: CTypesPointer[VkDisplayPropertiesKHR] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceDisplayPlanePropertiesKHR(physicalDevice: VkPhysicalDevice, pPropertyCount: CTypesPointer[c_uint32] | None, pProperties: CTypesPointer[VkDisplayPlanePropertiesKHR] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetDisplayPlaneSupportedDisplaysKHR(physicalDevice: VkPhysicalDevice, planeIndex: int, pDisplayCount: CTypesPointer[c_uint32] | None, pDisplays: CTypesPointer[VkDisplayKHR] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetDisplayModePropertiesKHR(physicalDevice: VkPhysicalDevice, display: VkDisplayKHR, pPropertyCount: CTypesPointer[c_uint32] | None, pProperties: CTypesPointer[VkDisplayModePropertiesKHR] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkCreateDisplayModeKHR(physicalDevice: VkPhysicalDevice, display: VkDisplayKHR, pCreateInfo: CTypesPointer[VkDisplayModeCreateInfoKHR], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pMode: CTypesPointer[VkDisplayModeKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetDisplayPlaneCapabilitiesKHR(physicalDevice: VkPhysicalDevice, mode: VkDisplayModeKHR, planeIndex: int, pCapabilities: CTypesPointer[VkDisplayPlaneCapabilitiesKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkCreateDisplayPlaneSurfaceKHR(instance: VkInstance, pCreateInfo: CTypesPointer[VkDisplaySurfaceCreateInfoKHR], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSurface: CTypesPointer[VkSurfaceKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkDestroySurfaceKHR(instance: VkInstance, surface: VkSurfaceKHR, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceSurfaceSupportKHR(physicalDevice: VkPhysicalDevice, queueFamilyIndex: int, surface: VkSurfaceKHR, pSupported: CTypesPointer[VkBool32]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physicalDevice: VkPhysicalDevice, surface: VkSurfaceKHR, pSurfaceCapabilities: CTypesPointer[VkSurfaceCapabilitiesKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceSurfaceFormatsKHR(physicalDevice: VkPhysicalDevice, surface: VkSurfaceKHR, pSurfaceFormatCount: CTypesPointer[c_uint32] | None, pSurfaceFormats: CTypesPointer[VkSurfaceFormatKHR] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceSurfacePresentModesKHR(physicalDevice: VkPhysicalDevice, surface: VkSurfaceKHR, pPresentModeCount: CTypesPointer[c_uint32] | None, pPresentModes: CTypesPointer[VkPresentModeKHR] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkCreateViSurfaceNN(instance: VkInstance, pCreateInfo: CTypesPointer[VkViSurfaceCreateInfoNN], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSurface: CTypesPointer[VkSurfaceKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkCreateWaylandSurfaceKHR(instance: VkInstance, pCreateInfo: CTypesPointer[VkWaylandSurfaceCreateInfoKHR], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSurface: CTypesPointer[VkSurfaceKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceWaylandPresentationSupportKHR(physicalDevice: VkPhysicalDevice, queueFamilyIndex: int, display: CTypesPointer[wl_display]) -> VkBool32:
        raise VulkanNoInstance

    @staticmethod
    def vkCreateWin32SurfaceKHR(instance: VkInstance, pCreateInfo: CTypesPointer[VkWin32SurfaceCreateInfoKHR], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSurface: CTypesPointer[VkSurfaceKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceWin32PresentationSupportKHR(physicalDevice: VkPhysicalDevice, queueFamilyIndex: int) -> VkBool32:
        raise VulkanNoInstance

    @staticmethod
    def vkCreateXlibSurfaceKHR(instance: VkInstance, pCreateInfo: CTypesPointer[VkXlibSurfaceCreateInfoKHR], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSurface: CTypesPointer[VkSurfaceKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceXlibPresentationSupportKHR(physicalDevice: VkPhysicalDevice, queueFamilyIndex: int, dpy: CTypesPointer[Display], visualID: VisualID) -> VkBool32:
        raise VulkanNoInstance

    @staticmethod
    def vkCreateXcbSurfaceKHR(instance: VkInstance, pCreateInfo: CTypesPointer[VkXcbSurfaceCreateInfoKHR], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSurface: CTypesPointer[VkSurfaceKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceXcbPresentationSupportKHR(physicalDevice: VkPhysicalDevice, queueFamilyIndex: int, connection: CTypesPointer[xcb_connection_t], visual_id: xcb_visualid_t) -> VkBool32:
        raise VulkanNoInstance

    @staticmethod
    def vkCreateDirectFBSurfaceEXT(instance: VkInstance, pCreateInfo: CTypesPointer[VkDirectFBSurfaceCreateInfoEXT], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSurface: CTypesPointer[VkSurfaceKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceDirectFBPresentationSupportEXT(physicalDevice: VkPhysicalDevice, queueFamilyIndex: int, dfb: CTypesPointer[IDirectFB]) -> VkBool32:
        raise VulkanNoInstance

    @staticmethod
    def vkCreateImagePipeSurfaceFUCHSIA(instance: VkInstance, pCreateInfo: CTypesPointer[VkImagePipeSurfaceCreateInfoFUCHSIA], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSurface: CTypesPointer[VkSurfaceKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkCreateStreamDescriptorSurfaceGGP(instance: VkInstance, pCreateInfo: CTypesPointer[VkStreamDescriptorSurfaceCreateInfoGGP], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSurface: CTypesPointer[VkSurfaceKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkCreateScreenSurfaceQNX(instance: VkInstance, pCreateInfo: CTypesPointer[VkScreenSurfaceCreateInfoQNX], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSurface: CTypesPointer[VkSurfaceKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceScreenPresentationSupportQNX(physicalDevice: VkPhysicalDevice, queueFamilyIndex: int, window: CTypesPointer[_screen_window]) -> VkBool32:
        raise VulkanNoInstance

    @staticmethod
    def vkCreateDebugReportCallbackEXT(instance: VkInstance, pCreateInfo: CTypesPointer[VkDebugReportCallbackCreateInfoEXT], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pCallback: CTypesPointer[VkDebugReportCallbackEXT]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkDestroyDebugReportCallbackEXT(instance: VkInstance, callback: VkDebugReportCallbackEXT, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkDebugReportMessageEXT(instance: VkInstance, flags: VkDebugReportFlagsEXT, objectType: VkDebugReportObjectTypeEXT, object: int, location: int, messageCode: int, pLayerPrefix: bytes, pMessage: bytes) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceExternalImageFormatPropertiesNV(physicalDevice: VkPhysicalDevice, format: VkFormat, type: VkImageType, tiling: VkImageTiling, usage: VkImageUsageFlags, flags: VkImageCreateFlags, externalHandleType: VkExternalMemoryHandleTypeFlagsNV, pExternalImageFormatProperties: CTypesPointer[VkExternalImageFormatPropertiesNV]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceFeatures2(physicalDevice: VkPhysicalDevice, pFeatures: CTypesPointer[VkPhysicalDeviceFeatures2]) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceFeatures2KHR(physicalDevice: VkPhysicalDevice, pFeatures: CTypesPointer[VkPhysicalDeviceFeatures2]) -> None:  # Alias of vkGetPhysicalDeviceFeatures2
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceProperties2(physicalDevice: VkPhysicalDevice, pProperties: CTypesPointer[VkPhysicalDeviceProperties2]) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceProperties2KHR(physicalDevice: VkPhysicalDevice, pProperties: CTypesPointer[VkPhysicalDeviceProperties2]) -> None:  # Alias of vkGetPhysicalDeviceProperties2
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceFormatProperties2(physicalDevice: VkPhysicalDevice, format: VkFormat, pFormatProperties: CTypesPointer[VkFormatProperties2]) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceFormatProperties2KHR(physicalDevice: VkPhysicalDevice, format: VkFormat, pFormatProperties: CTypesPointer[VkFormatProperties2]) -> None:  # Alias of vkGetPhysicalDeviceFormatProperties2
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceImageFormatProperties2(physicalDevice: VkPhysicalDevice, pImageFormatInfo: CTypesPointer[VkPhysicalDeviceImageFormatInfo2], pImageFormatProperties: CTypesPointer[VkImageFormatProperties2]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceImageFormatProperties2KHR(physicalDevice: VkPhysicalDevice, pImageFormatInfo: CTypesPointer[VkPhysicalDeviceImageFormatInfo2], pImageFormatProperties: CTypesPointer[VkImageFormatProperties2]) -> VkResult:  # Alias of vkGetPhysicalDeviceImageFormatProperties2
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceQueueFamilyProperties2(physicalDevice: VkPhysicalDevice, pQueueFamilyPropertyCount: CTypesPointer[c_uint32] | None, pQueueFamilyProperties: CTypesPointer[VkQueueFamilyProperties2] | None) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceQueueFamilyProperties2KHR(physicalDevice: VkPhysicalDevice, pQueueFamilyPropertyCount: CTypesPointer[c_uint32] | None, pQueueFamilyProperties: CTypesPointer[VkQueueFamilyProperties2] | None) -> None:  # Alias of vkGetPhysicalDeviceQueueFamilyProperties2
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceMemoryProperties2(physicalDevice: VkPhysicalDevice, pMemoryProperties: CTypesPointer[VkPhysicalDeviceMemoryProperties2]) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceMemoryProperties2KHR(physicalDevice: VkPhysicalDevice, pMemoryProperties: CTypesPointer[VkPhysicalDeviceMemoryProperties2]) -> None:  # Alias of vkGetPhysicalDeviceMemoryProperties2
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceSparseImageFormatProperties2(physicalDevice: VkPhysicalDevice, pFormatInfo: CTypesPointer[VkPhysicalDeviceSparseImageFormatInfo2], pPropertyCount: CTypesPointer[c_uint32] | None, pProperties: CTypesPointer[VkSparseImageFormatProperties2] | None) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceSparseImageFormatProperties2KHR(physicalDevice: VkPhysicalDevice, pFormatInfo: CTypesPointer[VkPhysicalDeviceSparseImageFormatInfo2], pPropertyCount: CTypesPointer[c_uint32] | None, pProperties: CTypesPointer[VkSparseImageFormatProperties2] | None) -> None:  # Alias of vkGetPhysicalDeviceSparseImageFormatProperties2
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceExternalBufferProperties(physicalDevice: VkPhysicalDevice, pExternalBufferInfo: CTypesPointer[VkPhysicalDeviceExternalBufferInfo], pExternalBufferProperties: CTypesPointer[VkExternalBufferProperties]) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceExternalBufferPropertiesKHR(physicalDevice: VkPhysicalDevice, pExternalBufferInfo: CTypesPointer[VkPhysicalDeviceExternalBufferInfo], pExternalBufferProperties: CTypesPointer[VkExternalBufferProperties]) -> None:  # Alias of vkGetPhysicalDeviceExternalBufferProperties
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceExternalMemorySciBufPropertiesNV(physicalDevice: VkPhysicalDevice, handleType: VkExternalMemoryHandleTypeFlagBits, handle: NvSciBufObj, pMemorySciBufProperties: CTypesPointer[VkMemorySciBufPropertiesNV]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceSciBufAttributesNV(physicalDevice: VkPhysicalDevice, pAttributes: NvSciBufAttrList) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceExternalSemaphoreProperties(physicalDevice: VkPhysicalDevice, pExternalSemaphoreInfo: CTypesPointer[VkPhysicalDeviceExternalSemaphoreInfo], pExternalSemaphoreProperties: CTypesPointer[VkExternalSemaphoreProperties]) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceExternalSemaphorePropertiesKHR(physicalDevice: VkPhysicalDevice, pExternalSemaphoreInfo: CTypesPointer[VkPhysicalDeviceExternalSemaphoreInfo], pExternalSemaphoreProperties: CTypesPointer[VkExternalSemaphoreProperties]) -> None:  # Alias of vkGetPhysicalDeviceExternalSemaphoreProperties
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceExternalFenceProperties(physicalDevice: VkPhysicalDevice, pExternalFenceInfo: CTypesPointer[VkPhysicalDeviceExternalFenceInfo], pExternalFenceProperties: CTypesPointer[VkExternalFenceProperties]) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceExternalFencePropertiesKHR(physicalDevice: VkPhysicalDevice, pExternalFenceInfo: CTypesPointer[VkPhysicalDeviceExternalFenceInfo], pExternalFenceProperties: CTypesPointer[VkExternalFenceProperties]) -> None:  # Alias of vkGetPhysicalDeviceExternalFenceProperties
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceSciSyncAttributesNV(physicalDevice: VkPhysicalDevice, pSciSyncAttributesInfo: CTypesPointer[VkSciSyncAttributesInfoNV], pAttributes: NvSciSyncAttrList) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkReleaseDisplayEXT(physicalDevice: VkPhysicalDevice, display: VkDisplayKHR) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkAcquireXlibDisplayEXT(physicalDevice: VkPhysicalDevice, dpy: CTypesPointer[Display], display: VkDisplayKHR) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetRandROutputDisplayEXT(physicalDevice: VkPhysicalDevice, dpy: CTypesPointer[Display], rrOutput: RROutput, pDisplay: CTypesPointer[VkDisplayKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkAcquireWinrtDisplayNV(physicalDevice: VkPhysicalDevice, display: VkDisplayKHR) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetWinrtDisplayNV(physicalDevice: VkPhysicalDevice, deviceRelativeId: int, pDisplay: CTypesPointer[VkDisplayKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceSurfaceCapabilities2EXT(physicalDevice: VkPhysicalDevice, surface: VkSurfaceKHR, pSurfaceCapabilities: CTypesPointer[VkSurfaceCapabilities2EXT]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkEnumeratePhysicalDeviceGroups(instance: VkInstance, pPhysicalDeviceGroupCount: CTypesPointer[c_uint32] | None, pPhysicalDeviceGroupProperties: CTypesPointer[VkPhysicalDeviceGroupProperties] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkEnumeratePhysicalDeviceGroupsKHR(instance: VkInstance, pPhysicalDeviceGroupCount: CTypesPointer[c_uint32] | None, pPhysicalDeviceGroupProperties: CTypesPointer[VkPhysicalDeviceGroupProperties] | None) -> VkResult:  # Alias of vkEnumeratePhysicalDeviceGroups
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDevicePresentRectanglesKHR(physicalDevice: VkPhysicalDevice, surface: VkSurfaceKHR, pRectCount: CTypesPointer[c_uint32] | None, pRects: CTypesPointer[VkRect2D] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkCreateIOSSurfaceMVK(instance: VkInstance, pCreateInfo: CTypesPointer[VkIOSSurfaceCreateInfoMVK], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSurface: CTypesPointer[VkSurfaceKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkCreateMacOSSurfaceMVK(instance: VkInstance, pCreateInfo: CTypesPointer[VkMacOSSurfaceCreateInfoMVK], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSurface: CTypesPointer[VkSurfaceKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkCreateMetalSurfaceEXT(instance: VkInstance, pCreateInfo: CTypesPointer[VkMetalSurfaceCreateInfoEXT], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSurface: CTypesPointer[VkSurfaceKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceMultisamplePropertiesEXT(physicalDevice: VkPhysicalDevice, samples: VkSampleCountFlagBits, pMultisampleProperties: CTypesPointer[VkMultisamplePropertiesEXT]) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceSurfaceCapabilities2KHR(physicalDevice: VkPhysicalDevice, pSurfaceInfo: CTypesPointer[VkPhysicalDeviceSurfaceInfo2KHR], pSurfaceCapabilities: CTypesPointer[VkSurfaceCapabilities2KHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceSurfaceFormats2KHR(physicalDevice: VkPhysicalDevice, pSurfaceInfo: CTypesPointer[VkPhysicalDeviceSurfaceInfo2KHR], pSurfaceFormatCount: CTypesPointer[c_uint32] | None, pSurfaceFormats: CTypesPointer[VkSurfaceFormat2KHR] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceDisplayProperties2KHR(physicalDevice: VkPhysicalDevice, pPropertyCount: CTypesPointer[c_uint32] | None, pProperties: CTypesPointer[VkDisplayProperties2KHR] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceDisplayPlaneProperties2KHR(physicalDevice: VkPhysicalDevice, pPropertyCount: CTypesPointer[c_uint32] | None, pProperties: CTypesPointer[VkDisplayPlaneProperties2KHR] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetDisplayModeProperties2KHR(physicalDevice: VkPhysicalDevice, display: VkDisplayKHR, pPropertyCount: CTypesPointer[c_uint32] | None, pProperties: CTypesPointer[VkDisplayModeProperties2KHR] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetDisplayPlaneCapabilities2KHR(physicalDevice: VkPhysicalDevice, pDisplayPlaneInfo: CTypesPointer[VkDisplayPlaneInfo2KHR], pCapabilities: CTypesPointer[VkDisplayPlaneCapabilities2KHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceCalibrateableTimeDomainsKHR(physicalDevice: VkPhysicalDevice, pTimeDomainCount: CTypesPointer[c_uint32] | None, pTimeDomains: CTypesPointer[VkTimeDomainKHR] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceCalibrateableTimeDomainsEXT(physicalDevice: VkPhysicalDevice, pTimeDomainCount: CTypesPointer[c_uint32] | None, pTimeDomains: CTypesPointer[VkTimeDomainKHR] | None) -> VkResult:  # Alias of vkGetPhysicalDeviceCalibrateableTimeDomainsKHR
        raise VulkanNoInstance

    @staticmethod
    def vkCreateDebugUtilsMessengerEXT(instance: VkInstance, pCreateInfo: CTypesPointer[VkDebugUtilsMessengerCreateInfoEXT], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pMessenger: CTypesPointer[VkDebugUtilsMessengerEXT]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkDestroyDebugUtilsMessengerEXT(instance: VkInstance, messenger: VkDebugUtilsMessengerEXT, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkSubmitDebugUtilsMessageEXT(instance: VkInstance, messageSeverity: VkDebugUtilsMessageSeverityFlagBitsEXT, messageTypes: VkDebugUtilsMessageTypeFlagsEXT, pCallbackData: CTypesPointer[VkDebugUtilsMessengerCallbackDataEXT]) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceCooperativeMatrixPropertiesNV(physicalDevice: VkPhysicalDevice, pPropertyCount: CTypesPointer[c_uint32] | None, pProperties: CTypesPointer[VkCooperativeMatrixPropertiesNV] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceSurfacePresentModes2EXT(physicalDevice: VkPhysicalDevice, pSurfaceInfo: CTypesPointer[VkPhysicalDeviceSurfaceInfo2KHR], pPresentModeCount: CTypesPointer[c_uint32] | None, pPresentModes: CTypesPointer[VkPresentModeKHR] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkEnumeratePhysicalDeviceQueueFamilyPerformanceQueryCountersKHR(physicalDevice: VkPhysicalDevice, queueFamilyIndex: int, pCounterCount: CTypesPointer[c_uint32] | None, pCounters: CTypesPointer[VkPerformanceCounterKHR] | None, pCounterDescriptions: CTypesPointer[VkPerformanceCounterDescriptionKHR] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceQueueFamilyPerformanceQueryPassesKHR(physicalDevice: VkPhysicalDevice, pPerformanceQueryCreateInfo: CTypesPointer[VkQueryPoolPerformanceCreateInfoKHR], pNumPasses: CTypesPointer[c_uint32]) -> None:
        raise VulkanNoInstance

    @staticmethod
    def vkCreateHeadlessSurfaceEXT(instance: VkInstance, pCreateInfo: CTypesPointer[VkHeadlessSurfaceCreateInfoEXT], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSurface: CTypesPointer[VkSurfaceKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceSupportedFramebufferMixedSamplesCombinationsNV(physicalDevice: VkPhysicalDevice, pCombinationCount: CTypesPointer[c_uint32] | None, pCombinations: CTypesPointer[VkFramebufferMixedSamplesCombinationNV] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceToolProperties(physicalDevice: VkPhysicalDevice, pToolCount: CTypesPointer[c_uint32] | None, pToolProperties: CTypesPointer[VkPhysicalDeviceToolProperties] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceToolPropertiesEXT(physicalDevice: VkPhysicalDevice, pToolCount: CTypesPointer[c_uint32] | None, pToolProperties: CTypesPointer[VkPhysicalDeviceToolProperties] | None) -> VkResult:  # Alias of vkGetPhysicalDeviceToolProperties
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceRefreshableObjectTypesKHR(physicalDevice: VkPhysicalDevice, pRefreshableObjectTypeCount: CTypesPointer[c_uint32] | None, pRefreshableObjectTypes: CTypesPointer[VkObjectType] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceFragmentShadingRatesKHR(physicalDevice: VkPhysicalDevice, pFragmentShadingRateCount: CTypesPointer[c_uint32] | None, pFragmentShadingRates: CTypesPointer[VkPhysicalDeviceFragmentShadingRateKHR] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceVideoCapabilitiesKHR(physicalDevice: VkPhysicalDevice, pVideoProfile: CTypesPointer[VkVideoProfileInfoKHR], pCapabilities: CTypesPointer[VkVideoCapabilitiesKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceVideoFormatPropertiesKHR(physicalDevice: VkPhysicalDevice, pVideoFormatInfo: CTypesPointer[VkPhysicalDeviceVideoFormatInfoKHR], pVideoFormatPropertyCount: CTypesPointer[c_uint32] | None, pVideoFormatProperties: CTypesPointer[VkVideoFormatPropertiesKHR] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceVideoEncodeQualityLevelPropertiesKHR(physicalDevice: VkPhysicalDevice, pQualityLevelInfo: CTypesPointer[VkPhysicalDeviceVideoEncodeQualityLevelInfoKHR], pQualityLevelProperties: CTypesPointer[VkVideoEncodeQualityLevelPropertiesKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkAcquireDrmDisplayEXT(physicalDevice: VkPhysicalDevice, drmFd: int, display: VkDisplayKHR) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetDrmDisplayEXT(physicalDevice: VkPhysicalDevice, drmFd: int, connectorId: int, display: CTypesPointer[VkDisplayKHR]) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceOpticalFlowImageFormatsNV(physicalDevice: VkPhysicalDevice, pOpticalFlowImageFormatInfo: CTypesPointer[VkOpticalFlowImageFormatInfoNV], pFormatCount: CTypesPointer[c_uint32] | None, pImageFormatProperties: CTypesPointer[VkOpticalFlowImageFormatPropertiesNV] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceCooperativeMatrixPropertiesKHR(physicalDevice: VkPhysicalDevice, pPropertyCount: CTypesPointer[c_uint32] | None, pProperties: CTypesPointer[VkCooperativeMatrixPropertiesKHR] | None) -> VkResult:
        raise VulkanNoInstance

    @staticmethod
    def vkGetPhysicalDeviceCooperativeMatrixFlexibleDimensionsPropertiesNV(physicalDevice: VkPhysicalDevice, pPropertyCount: CTypesPointer[c_uint32] | None, pProperties: CTypesPointer[VkCooperativeMatrixFlexibleDimensionsPropertiesNV] | None) -> VkResult:
        raise VulkanNoInstance


class DeviceFunc:
    @staticmethod
    def vkDestroyDevice(device: VkDevice, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceQueue(device: VkDevice, queueFamilyIndex: int, queueIndex: int, pQueue: CTypesPointer[VkQueue]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkQueueSubmit(queue: VkQueue, submitCount: int, pSubmits: CTypesPointer[VkSubmitInfo], fence: VkFence) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkQueueWaitIdle(queue: VkQueue) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDeviceWaitIdle(device: VkDevice) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkAllocateMemory(device: VkDevice, pAllocateInfo: CTypesPointer[VkMemoryAllocateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pMemory: CTypesPointer[VkDeviceMemory]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkFreeMemory(device: VkDevice, memory: VkDeviceMemory, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkMapMemory(device: VkDevice, memory: VkDeviceMemory, offset: VkDeviceSize, size: VkDeviceSize, flags: VkMemoryMapFlags, ppData: CTypesPointer[None] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkUnmapMemory(device: VkDevice, memory: VkDeviceMemory) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkFlushMappedMemoryRanges(device: VkDevice, memoryRangeCount: int, pMemoryRanges: CTypesPointer[VkMappedMemoryRange]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkInvalidateMappedMemoryRanges(device: VkDevice, memoryRangeCount: int, pMemoryRanges: CTypesPointer[VkMappedMemoryRange]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceMemoryCommitment(device: VkDevice, memory: VkDeviceMemory, pCommittedMemoryInBytes: CTypesPointer[VkDeviceSize]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetBufferMemoryRequirements(device: VkDevice, buffer: VkBuffer, pMemoryRequirements: CTypesPointer[VkMemoryRequirements]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkBindBufferMemory(device: VkDevice, buffer: VkBuffer, memory: VkDeviceMemory, memoryOffset: VkDeviceSize) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetImageMemoryRequirements(device: VkDevice, image: VkImage, pMemoryRequirements: CTypesPointer[VkMemoryRequirements]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkBindImageMemory(device: VkDevice, image: VkImage, memory: VkDeviceMemory, memoryOffset: VkDeviceSize) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetImageSparseMemoryRequirements(device: VkDevice, image: VkImage, pSparseMemoryRequirementCount: CTypesPointer[c_uint32] | None, pSparseMemoryRequirements: CTypesPointer[VkSparseImageMemoryRequirements] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkQueueBindSparse(queue: VkQueue, bindInfoCount: int, pBindInfo: CTypesPointer[VkBindSparseInfo], fence: VkFence) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateFence(device: VkDevice, pCreateInfo: CTypesPointer[VkFenceCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pFence: CTypesPointer[VkFence]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyFence(device: VkDevice, fence: VkFence, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkResetFences(device: VkDevice, fenceCount: int, pFences: CTypesPointer[VkFence]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetFenceStatus(device: VkDevice, fence: VkFence) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkWaitForFences(device: VkDevice, fenceCount: int, pFences: CTypesPointer[VkFence], waitAll: VkBool32, timeout: int) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateSemaphore(device: VkDevice, pCreateInfo: CTypesPointer[VkSemaphoreCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSemaphore: CTypesPointer[VkSemaphore]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroySemaphore(device: VkDevice, semaphore: VkSemaphore, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateEvent(device: VkDevice, pCreateInfo: CTypesPointer[VkEventCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pEvent: CTypesPointer[VkEvent]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyEvent(device: VkDevice, event: VkEvent, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetEventStatus(device: VkDevice, event: VkEvent) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkSetEvent(device: VkDevice, event: VkEvent) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkResetEvent(device: VkDevice, event: VkEvent) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateQueryPool(device: VkDevice, pCreateInfo: CTypesPointer[VkQueryPoolCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pQueryPool: CTypesPointer[VkQueryPool]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyQueryPool(device: VkDevice, queryPool: VkQueryPool, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetQueryPoolResults(device: VkDevice, queryPool: VkQueryPool, firstQuery: int, queryCount: int, dataSize: int, pData: CTypesPointer[None], stride: VkDeviceSize, flags: VkQueryResultFlags) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkResetQueryPool(device: VkDevice, queryPool: VkQueryPool, firstQuery: int, queryCount: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkResetQueryPoolEXT(device: VkDevice, queryPool: VkQueryPool, firstQuery: int, queryCount: int) -> None:  # Alias of vkResetQueryPool
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateBuffer(device: VkDevice, pCreateInfo: CTypesPointer[VkBufferCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pBuffer: CTypesPointer[VkBuffer]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyBuffer(device: VkDevice, buffer: VkBuffer, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateBufferView(device: VkDevice, pCreateInfo: CTypesPointer[VkBufferViewCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pView: CTypesPointer[VkBufferView]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyBufferView(device: VkDevice, bufferView: VkBufferView, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateImage(device: VkDevice, pCreateInfo: CTypesPointer[VkImageCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pImage: CTypesPointer[VkImage]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyImage(device: VkDevice, image: VkImage, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetImageSubresourceLayout(device: VkDevice, image: VkImage, pSubresource: CTypesPointer[VkImageSubresource], pLayout: CTypesPointer[VkSubresourceLayout]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateImageView(device: VkDevice, pCreateInfo: CTypesPointer[VkImageViewCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pView: CTypesPointer[VkImageView]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyImageView(device: VkDevice, imageView: VkImageView, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateShaderModule(device: VkDevice, pCreateInfo: CTypesPointer[VkShaderModuleCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pShaderModule: CTypesPointer[VkShaderModule]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyShaderModule(device: VkDevice, shaderModule: VkShaderModule, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreatePipelineCache(device: VkDevice, pCreateInfo: CTypesPointer[VkPipelineCacheCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pPipelineCache: CTypesPointer[VkPipelineCache]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreatePipelineCache(device: VkDevice, pCreateInfo: CTypesPointer[VkPipelineCacheCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pPipelineCache: CTypesPointer[VkPipelineCache]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyPipelineCache(device: VkDevice, pipelineCache: VkPipelineCache, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetPipelineCacheData(device: VkDevice, pipelineCache: VkPipelineCache, pDataSize: CTypesPointer[c_size_t] | None, pData: CTypesPointer[None] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkMergePipelineCaches(device: VkDevice, dstCache: VkPipelineCache, srcCacheCount: int, pSrcCaches: CTypesPointer[VkPipelineCache]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreatePipelineBinariesKHR(device: VkDevice, pCreateInfo: CTypesPointer[VkPipelineBinaryCreateInfoKHR], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pBinaries: CTypesPointer[VkPipelineBinaryHandlesInfoKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyPipelineBinaryKHR(device: VkDevice, pipelineBinary: VkPipelineBinaryKHR, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetPipelineKeyKHR(device: VkDevice, pPipelineCreateInfo: CTypesPointer[VkPipelineCreateInfoKHR] | None, pPipelineKey: CTypesPointer[VkPipelineBinaryKeyKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetPipelineBinaryDataKHR(device: VkDevice, pInfo: CTypesPointer[VkPipelineBinaryDataInfoKHR], pPipelineBinaryKey: CTypesPointer[VkPipelineBinaryKeyKHR], pPipelineBinaryDataSize: CTypesPointer[c_size_t] | None, pPipelineBinaryData: CTypesPointer[None] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkReleaseCapturedPipelineDataKHR(device: VkDevice, pInfo: CTypesPointer[VkReleaseCapturedPipelineDataInfoKHR], pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateGraphicsPipelines(device: VkDevice, pipelineCache: VkPipelineCache, createInfoCount: int, pCreateInfos: CTypesPointer[VkGraphicsPipelineCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pPipelines: CTypesPointer[VkPipeline]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateGraphicsPipelines(device: VkDevice, pipelineCache: VkPipelineCache, createInfoCount: int, pCreateInfos: CTypesPointer[VkGraphicsPipelineCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pPipelines: CTypesPointer[VkPipeline]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateComputePipelines(device: VkDevice, pipelineCache: VkPipelineCache, createInfoCount: int, pCreateInfos: CTypesPointer[VkComputePipelineCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pPipelines: CTypesPointer[VkPipeline]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateComputePipelines(device: VkDevice, pipelineCache: VkPipelineCache, createInfoCount: int, pCreateInfos: CTypesPointer[VkComputePipelineCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pPipelines: CTypesPointer[VkPipeline]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceSubpassShadingMaxWorkgroupSizeHUAWEI(device: VkDevice, renderpass: VkRenderPass, pMaxWorkgroupSize: CTypesPointer[VkExtent2D]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyPipeline(device: VkDevice, pipeline: VkPipeline, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreatePipelineLayout(device: VkDevice, pCreateInfo: CTypesPointer[VkPipelineLayoutCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pPipelineLayout: CTypesPointer[VkPipelineLayout]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyPipelineLayout(device: VkDevice, pipelineLayout: VkPipelineLayout, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateSampler(device: VkDevice, pCreateInfo: CTypesPointer[VkSamplerCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSampler: CTypesPointer[VkSampler]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroySampler(device: VkDevice, sampler: VkSampler, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateDescriptorSetLayout(device: VkDevice, pCreateInfo: CTypesPointer[VkDescriptorSetLayoutCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSetLayout: CTypesPointer[VkDescriptorSetLayout]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyDescriptorSetLayout(device: VkDevice, descriptorSetLayout: VkDescriptorSetLayout, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateDescriptorPool(device: VkDevice, pCreateInfo: CTypesPointer[VkDescriptorPoolCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pDescriptorPool: CTypesPointer[VkDescriptorPool]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyDescriptorPool(device: VkDevice, descriptorPool: VkDescriptorPool, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkResetDescriptorPool(device: VkDevice, descriptorPool: VkDescriptorPool, flags: VkDescriptorPoolResetFlags) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkAllocateDescriptorSets(device: VkDevice, pAllocateInfo: CTypesPointer[VkDescriptorSetAllocateInfo], pDescriptorSets: CTypesPointer[VkDescriptorSet]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkFreeDescriptorSets(device: VkDevice, descriptorPool: VkDescriptorPool, descriptorSetCount: int, pDescriptorSets: CTypesPointer[VkDescriptorSet]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkUpdateDescriptorSets(device: VkDevice, descriptorWriteCount: int, pDescriptorWrites: CTypesPointer[VkWriteDescriptorSet], descriptorCopyCount: int, pDescriptorCopies: CTypesPointer[VkCopyDescriptorSet]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateFramebuffer(device: VkDevice, pCreateInfo: CTypesPointer[VkFramebufferCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pFramebuffer: CTypesPointer[VkFramebuffer]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyFramebuffer(device: VkDevice, framebuffer: VkFramebuffer, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateRenderPass(device: VkDevice, pCreateInfo: CTypesPointer[VkRenderPassCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pRenderPass: CTypesPointer[VkRenderPass]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyRenderPass(device: VkDevice, renderPass: VkRenderPass, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetRenderAreaGranularity(device: VkDevice, renderPass: VkRenderPass, pGranularity: CTypesPointer[VkExtent2D]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetRenderingAreaGranularityKHR(device: VkDevice, pRenderingAreaInfo: CTypesPointer[VkRenderingAreaInfoKHR], pGranularity: CTypesPointer[VkExtent2D]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateCommandPool(device: VkDevice, pCreateInfo: CTypesPointer[VkCommandPoolCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pCommandPool: CTypesPointer[VkCommandPool]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyCommandPool(device: VkDevice, commandPool: VkCommandPool, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkResetCommandPool(device: VkDevice, commandPool: VkCommandPool, flags: VkCommandPoolResetFlags) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkAllocateCommandBuffers(device: VkDevice, pAllocateInfo: CTypesPointer[VkCommandBufferAllocateInfo], pCommandBuffers: CTypesPointer[VkCommandBuffer]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkFreeCommandBuffers(device: VkDevice, commandPool: VkCommandPool, commandBufferCount: int, pCommandBuffers: CTypesPointer[VkCommandBuffer]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkBeginCommandBuffer(commandBuffer: VkCommandBuffer, pBeginInfo: CTypesPointer[VkCommandBufferBeginInfo]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkEndCommandBuffer(commandBuffer: VkCommandBuffer) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkResetCommandBuffer(commandBuffer: VkCommandBuffer, flags: VkCommandBufferResetFlags) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBindPipeline(commandBuffer: VkCommandBuffer, pipelineBindPoint: VkPipelineBindPoint, pipeline: VkPipeline) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetAttachmentFeedbackLoopEnableEXT(commandBuffer: VkCommandBuffer, aspectMask: VkImageAspectFlags) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetViewport(commandBuffer: VkCommandBuffer, firstViewport: int, viewportCount: int, pViewports: CTypesPointer[VkViewport]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetScissor(commandBuffer: VkCommandBuffer, firstScissor: int, scissorCount: int, pScissors: CTypesPointer[VkRect2D]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetLineWidth(commandBuffer: VkCommandBuffer, lineWidth: float) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDepthBias(commandBuffer: VkCommandBuffer, depthBiasConstantFactor: float, depthBiasClamp: float, depthBiasSlopeFactor: float) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetBlendConstants(commandBuffer: VkCommandBuffer, blendConstants: Array[float, 4]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDepthBounds(commandBuffer: VkCommandBuffer, minDepthBounds: float, maxDepthBounds: float) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetStencilCompareMask(commandBuffer: VkCommandBuffer, faceMask: VkStencilFaceFlags, compareMask: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetStencilWriteMask(commandBuffer: VkCommandBuffer, faceMask: VkStencilFaceFlags, writeMask: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetStencilReference(commandBuffer: VkCommandBuffer, faceMask: VkStencilFaceFlags, reference: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBindDescriptorSets(commandBuffer: VkCommandBuffer, pipelineBindPoint: VkPipelineBindPoint, layout: VkPipelineLayout, firstSet: int, descriptorSetCount: int, pDescriptorSets: CTypesPointer[VkDescriptorSet] | None, dynamicOffsetCount: int, pDynamicOffsets: CTypesPointer[c_uint32]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBindIndexBuffer(commandBuffer: VkCommandBuffer, buffer: VkBuffer, offset: VkDeviceSize, indexType: VkIndexType) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBindVertexBuffers(commandBuffer: VkCommandBuffer, firstBinding: int, bindingCount: int, pBuffers: CTypesPointer[VkBuffer] | None, pOffsets: CTypesPointer[VkDeviceSize]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDraw(commandBuffer: VkCommandBuffer, vertexCount: int, instanceCount: int, firstVertex: int, firstInstance: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawIndexed(commandBuffer: VkCommandBuffer, indexCount: int, instanceCount: int, firstIndex: int, vertexOffset: int, firstInstance: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawMultiEXT(commandBuffer: VkCommandBuffer, drawCount: int, pVertexInfo: CTypesPointer[VkMultiDrawInfoEXT], instanceCount: int, firstInstance: int, stride: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawMultiIndexedEXT(commandBuffer: VkCommandBuffer, drawCount: int, pIndexInfo: CTypesPointer[VkMultiDrawIndexedInfoEXT], instanceCount: int, firstInstance: int, stride: int, pVertexOffset: CTypesPointer[c_int32] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawIndirect(commandBuffer: VkCommandBuffer, buffer: VkBuffer, offset: VkDeviceSize, drawCount: int, stride: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawIndexedIndirect(commandBuffer: VkCommandBuffer, buffer: VkBuffer, offset: VkDeviceSize, drawCount: int, stride: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDispatch(commandBuffer: VkCommandBuffer, groupCountX: int, groupCountY: int, groupCountZ: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDispatchIndirect(commandBuffer: VkCommandBuffer, buffer: VkBuffer, offset: VkDeviceSize) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSubpassShadingHUAWEI(commandBuffer: VkCommandBuffer) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawClusterHUAWEI(commandBuffer: VkCommandBuffer, groupCountX: int, groupCountY: int, groupCountZ: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawClusterIndirectHUAWEI(commandBuffer: VkCommandBuffer, buffer: VkBuffer, offset: VkDeviceSize) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdUpdatePipelineIndirectBufferNV(commandBuffer: VkCommandBuffer, pipelineBindPoint: VkPipelineBindPoint, pipeline: VkPipeline) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyBuffer(commandBuffer: VkCommandBuffer, srcBuffer: VkBuffer, dstBuffer: VkBuffer, regionCount: int, pRegions: CTypesPointer[VkBufferCopy]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyImage(commandBuffer: VkCommandBuffer, srcImage: VkImage, srcImageLayout: VkImageLayout, dstImage: VkImage, dstImageLayout: VkImageLayout, regionCount: int, pRegions: CTypesPointer[VkImageCopy]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBlitImage(commandBuffer: VkCommandBuffer, srcImage: VkImage, srcImageLayout: VkImageLayout, dstImage: VkImage, dstImageLayout: VkImageLayout, regionCount: int, pRegions: CTypesPointer[VkImageBlit], filter: VkFilter) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyBufferToImage(commandBuffer: VkCommandBuffer, srcBuffer: VkBuffer, dstImage: VkImage, dstImageLayout: VkImageLayout, regionCount: int, pRegions: CTypesPointer[VkBufferImageCopy]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyImageToBuffer(commandBuffer: VkCommandBuffer, srcImage: VkImage, srcImageLayout: VkImageLayout, dstBuffer: VkBuffer, regionCount: int, pRegions: CTypesPointer[VkBufferImageCopy]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyMemoryIndirectNV(commandBuffer: VkCommandBuffer, copyBufferAddress: VkDeviceAddress, copyCount: int, stride: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyMemoryToImageIndirectNV(commandBuffer: VkCommandBuffer, copyBufferAddress: VkDeviceAddress, copyCount: int, stride: int, dstImage: VkImage, dstImageLayout: VkImageLayout, pImageSubresources: CTypesPointer[VkImageSubresourceLayers]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdUpdateBuffer(commandBuffer: VkCommandBuffer, dstBuffer: VkBuffer, dstOffset: VkDeviceSize, dataSize: VkDeviceSize, pData: CTypesPointer[None]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdFillBuffer(commandBuffer: VkCommandBuffer, dstBuffer: VkBuffer, dstOffset: VkDeviceSize, size: VkDeviceSize, data: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdClearColorImage(commandBuffer: VkCommandBuffer, image: VkImage, imageLayout: VkImageLayout, pColor: CTypesPointer[VkClearColorValue], rangeCount: int, pRanges: CTypesPointer[VkImageSubresourceRange]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdClearDepthStencilImage(commandBuffer: VkCommandBuffer, image: VkImage, imageLayout: VkImageLayout, pDepthStencil: CTypesPointer[VkClearDepthStencilValue], rangeCount: int, pRanges: CTypesPointer[VkImageSubresourceRange]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdClearAttachments(commandBuffer: VkCommandBuffer, attachmentCount: int, pAttachments: CTypesPointer[VkClearAttachment], rectCount: int, pRects: CTypesPointer[VkClearRect]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdResolveImage(commandBuffer: VkCommandBuffer, srcImage: VkImage, srcImageLayout: VkImageLayout, dstImage: VkImage, dstImageLayout: VkImageLayout, regionCount: int, pRegions: CTypesPointer[VkImageResolve]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetEvent(commandBuffer: VkCommandBuffer, event: VkEvent, stageMask: VkPipelineStageFlags) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdResetEvent(commandBuffer: VkCommandBuffer, event: VkEvent, stageMask: VkPipelineStageFlags) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdWaitEvents(commandBuffer: VkCommandBuffer, eventCount: int, pEvents: CTypesPointer[VkEvent], srcStageMask: VkPipelineStageFlags, dstStageMask: VkPipelineStageFlags, memoryBarrierCount: int, pMemoryBarriers: CTypesPointer[VkMemoryBarrier], bufferMemoryBarrierCount: int, pBufferMemoryBarriers: CTypesPointer[VkBufferMemoryBarrier], imageMemoryBarrierCount: int, pImageMemoryBarriers: CTypesPointer[VkImageMemoryBarrier]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdPipelineBarrier(commandBuffer: VkCommandBuffer, srcStageMask: VkPipelineStageFlags, dstStageMask: VkPipelineStageFlags, dependencyFlags: VkDependencyFlags, memoryBarrierCount: int, pMemoryBarriers: CTypesPointer[VkMemoryBarrier], bufferMemoryBarrierCount: int, pBufferMemoryBarriers: CTypesPointer[VkBufferMemoryBarrier], imageMemoryBarrierCount: int, pImageMemoryBarriers: CTypesPointer[VkImageMemoryBarrier]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBeginQuery(commandBuffer: VkCommandBuffer, queryPool: VkQueryPool, query: int, flags: VkQueryControlFlags) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdEndQuery(commandBuffer: VkCommandBuffer, queryPool: VkQueryPool, query: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBeginConditionalRenderingEXT(commandBuffer: VkCommandBuffer, pConditionalRenderingBegin: CTypesPointer[VkConditionalRenderingBeginInfoEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdEndConditionalRenderingEXT(commandBuffer: VkCommandBuffer) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdResetQueryPool(commandBuffer: VkCommandBuffer, queryPool: VkQueryPool, firstQuery: int, queryCount: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdWriteTimestamp(commandBuffer: VkCommandBuffer, pipelineStage: VkPipelineStageFlagBits, queryPool: VkQueryPool, query: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyQueryPoolResults(commandBuffer: VkCommandBuffer, queryPool: VkQueryPool, firstQuery: int, queryCount: int, dstBuffer: VkBuffer, dstOffset: VkDeviceSize, stride: VkDeviceSize, flags: VkQueryResultFlags) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdPushConstants(commandBuffer: VkCommandBuffer, layout: VkPipelineLayout, stageFlags: VkShaderStageFlags, offset: int, size: int, pValues: CTypesPointer[None]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBeginRenderPass(commandBuffer: VkCommandBuffer, pRenderPassBegin: CTypesPointer[VkRenderPassBeginInfo], contents: VkSubpassContents) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdNextSubpass(commandBuffer: VkCommandBuffer, contents: VkSubpassContents) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdEndRenderPass(commandBuffer: VkCommandBuffer) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdExecuteCommands(commandBuffer: VkCommandBuffer, commandBufferCount: int, pCommandBuffers: CTypesPointer[VkCommandBuffer]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateSharedSwapchainsKHR(device: VkDevice, swapchainCount: int, pCreateInfos: CTypesPointer[VkSwapchainCreateInfoKHR], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSwapchains: CTypesPointer[VkSwapchainKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateSwapchainKHR(device: VkDevice, pCreateInfo: CTypesPointer[VkSwapchainCreateInfoKHR], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSwapchain: CTypesPointer[VkSwapchainKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroySwapchainKHR(device: VkDevice, swapchain: VkSwapchainKHR, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetSwapchainImagesKHR(device: VkDevice, swapchain: VkSwapchainKHR, pSwapchainImageCount: CTypesPointer[c_uint32] | None, pSwapchainImages: CTypesPointer[VkImage] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkAcquireNextImageKHR(device: VkDevice, swapchain: VkSwapchainKHR, timeout: int, semaphore: VkSemaphore, fence: VkFence, pImageIndex: CTypesPointer[c_uint32]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkQueuePresentKHR(queue: VkQueue, pPresentInfo: CTypesPointer[VkPresentInfoKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDebugMarkerSetObjectNameEXT(device: VkDevice, pNameInfo: CTypesPointer[VkDebugMarkerObjectNameInfoEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDebugMarkerSetObjectTagEXT(device: VkDevice, pTagInfo: CTypesPointer[VkDebugMarkerObjectTagInfoEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDebugMarkerBeginEXT(commandBuffer: VkCommandBuffer, pMarkerInfo: CTypesPointer[VkDebugMarkerMarkerInfoEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDebugMarkerEndEXT(commandBuffer: VkCommandBuffer) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDebugMarkerInsertEXT(commandBuffer: VkCommandBuffer, pMarkerInfo: CTypesPointer[VkDebugMarkerMarkerInfoEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetMemoryWin32HandleNV(device: VkDevice, memory: VkDeviceMemory, handleType: VkExternalMemoryHandleTypeFlagsNV, pHandle: CTypesPointer[HANDLE]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdExecuteGeneratedCommandsNV(commandBuffer: VkCommandBuffer, isPreprocessed: VkBool32, pGeneratedCommandsInfo: CTypesPointer[VkGeneratedCommandsInfoNV]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdPreprocessGeneratedCommandsNV(commandBuffer: VkCommandBuffer, pGeneratedCommandsInfo: CTypesPointer[VkGeneratedCommandsInfoNV]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBindPipelineShaderGroupNV(commandBuffer: VkCommandBuffer, pipelineBindPoint: VkPipelineBindPoint, pipeline: VkPipeline, groupIndex: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetGeneratedCommandsMemoryRequirementsNV(device: VkDevice, pInfo: CTypesPointer[VkGeneratedCommandsMemoryRequirementsInfoNV], pMemoryRequirements: CTypesPointer[VkMemoryRequirements2]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateIndirectCommandsLayoutNV(device: VkDevice, pCreateInfo: CTypesPointer[VkIndirectCommandsLayoutCreateInfoNV], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pIndirectCommandsLayout: CTypesPointer[VkIndirectCommandsLayoutNV]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyIndirectCommandsLayoutNV(device: VkDevice, indirectCommandsLayout: VkIndirectCommandsLayoutNV, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdExecuteGeneratedCommandsEXT(commandBuffer: VkCommandBuffer, isPreprocessed: VkBool32, pGeneratedCommandsInfo: CTypesPointer[VkGeneratedCommandsInfoEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdPreprocessGeneratedCommandsEXT(commandBuffer: VkCommandBuffer, pGeneratedCommandsInfo: CTypesPointer[VkGeneratedCommandsInfoEXT], stateCommandBuffer: VkCommandBuffer) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetGeneratedCommandsMemoryRequirementsEXT(device: VkDevice, pInfo: CTypesPointer[VkGeneratedCommandsMemoryRequirementsInfoEXT], pMemoryRequirements: CTypesPointer[VkMemoryRequirements2]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateIndirectCommandsLayoutEXT(device: VkDevice, pCreateInfo: CTypesPointer[VkIndirectCommandsLayoutCreateInfoEXT], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pIndirectCommandsLayout: CTypesPointer[VkIndirectCommandsLayoutEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyIndirectCommandsLayoutEXT(device: VkDevice, indirectCommandsLayout: VkIndirectCommandsLayoutEXT, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateIndirectExecutionSetEXT(device: VkDevice, pCreateInfo: CTypesPointer[VkIndirectExecutionSetCreateInfoEXT], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pIndirectExecutionSet: CTypesPointer[VkIndirectExecutionSetEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyIndirectExecutionSetEXT(device: VkDevice, indirectExecutionSet: VkIndirectExecutionSetEXT, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkUpdateIndirectExecutionSetPipelineEXT(device: VkDevice, indirectExecutionSet: VkIndirectExecutionSetEXT, executionSetWriteCount: int, pExecutionSetWrites: CTypesPointer[VkWriteIndirectExecutionSetPipelineEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkUpdateIndirectExecutionSetShaderEXT(device: VkDevice, indirectExecutionSet: VkIndirectExecutionSetEXT, executionSetWriteCount: int, pExecutionSetWrites: CTypesPointer[VkWriteIndirectExecutionSetShaderEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdPushDescriptorSetKHR(commandBuffer: VkCommandBuffer, pipelineBindPoint: VkPipelineBindPoint, layout: VkPipelineLayout, set: int, descriptorWriteCount: int, pDescriptorWrites: CTypesPointer[VkWriteDescriptorSet]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkTrimCommandPool(device: VkDevice, commandPool: VkCommandPool, flags: VkCommandPoolTrimFlags) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkTrimCommandPoolKHR(device: VkDevice, commandPool: VkCommandPool, flags: VkCommandPoolTrimFlags) -> None:  # Alias of vkTrimCommandPool
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetMemoryWin32HandleKHR(device: VkDevice, pGetWin32HandleInfo: CTypesPointer[VkMemoryGetWin32HandleInfoKHR], pHandle: CTypesPointer[HANDLE]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetMemoryWin32HandlePropertiesKHR(device: VkDevice, handleType: VkExternalMemoryHandleTypeFlagBits, handle: HANDLE, pMemoryWin32HandleProperties: CTypesPointer[VkMemoryWin32HandlePropertiesKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetMemoryFdKHR(device: VkDevice, pGetFdInfo: CTypesPointer[VkMemoryGetFdInfoKHR], pFd: CTypesPointer[int]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetMemoryFdPropertiesKHR(device: VkDevice, handleType: VkExternalMemoryHandleTypeFlagBits, fd: int, pMemoryFdProperties: CTypesPointer[VkMemoryFdPropertiesKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetMemoryZirconHandleFUCHSIA(device: VkDevice, pGetZirconHandleInfo: CTypesPointer[VkMemoryGetZirconHandleInfoFUCHSIA], pZirconHandle: CTypesPointer[zx_handle_t]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetMemoryZirconHandlePropertiesFUCHSIA(device: VkDevice, handleType: VkExternalMemoryHandleTypeFlagBits, zirconHandle: zx_handle_t, pMemoryZirconHandleProperties: CTypesPointer[VkMemoryZirconHandlePropertiesFUCHSIA]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetMemoryRemoteAddressNV(device: VkDevice, pMemoryGetRemoteAddressInfo: CTypesPointer[VkMemoryGetRemoteAddressInfoNV], pAddress: CTypesPointer[VkRemoteAddressNV]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetMemorySciBufNV(device: VkDevice, pGetSciBufInfo: CTypesPointer[VkMemoryGetSciBufInfoNV], pHandle: CTypesPointer[NvSciBufObj]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetSemaphoreWin32HandleKHR(device: VkDevice, pGetWin32HandleInfo: CTypesPointer[VkSemaphoreGetWin32HandleInfoKHR], pHandle: CTypesPointer[HANDLE]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkImportSemaphoreWin32HandleKHR(device: VkDevice, pImportSemaphoreWin32HandleInfo: CTypesPointer[VkImportSemaphoreWin32HandleInfoKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetSemaphoreFdKHR(device: VkDevice, pGetFdInfo: CTypesPointer[VkSemaphoreGetFdInfoKHR], pFd: CTypesPointer[int]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkImportSemaphoreFdKHR(device: VkDevice, pImportSemaphoreFdInfo: CTypesPointer[VkImportSemaphoreFdInfoKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetSemaphoreZirconHandleFUCHSIA(device: VkDevice, pGetZirconHandleInfo: CTypesPointer[VkSemaphoreGetZirconHandleInfoFUCHSIA], pZirconHandle: CTypesPointer[zx_handle_t]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkImportSemaphoreZirconHandleFUCHSIA(device: VkDevice, pImportSemaphoreZirconHandleInfo: CTypesPointer[VkImportSemaphoreZirconHandleInfoFUCHSIA]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetFenceWin32HandleKHR(device: VkDevice, pGetWin32HandleInfo: CTypesPointer[VkFenceGetWin32HandleInfoKHR], pHandle: CTypesPointer[HANDLE]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkImportFenceWin32HandleKHR(device: VkDevice, pImportFenceWin32HandleInfo: CTypesPointer[VkImportFenceWin32HandleInfoKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetFenceFdKHR(device: VkDevice, pGetFdInfo: CTypesPointer[VkFenceGetFdInfoKHR], pFd: CTypesPointer[int]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkImportFenceFdKHR(device: VkDevice, pImportFenceFdInfo: CTypesPointer[VkImportFenceFdInfoKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetFenceSciSyncFenceNV(device: VkDevice, pGetSciSyncHandleInfo: CTypesPointer[VkFenceGetSciSyncInfoNV], pHandle: CTypesPointer[None]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetFenceSciSyncObjNV(device: VkDevice, pGetSciSyncHandleInfo: CTypesPointer[VkFenceGetSciSyncInfoNV], pHandle: CTypesPointer[None]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkImportFenceSciSyncFenceNV(device: VkDevice, pImportFenceSciSyncInfo: CTypesPointer[VkImportFenceSciSyncInfoNV]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkImportFenceSciSyncObjNV(device: VkDevice, pImportFenceSciSyncInfo: CTypesPointer[VkImportFenceSciSyncInfoNV]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetSemaphoreSciSyncObjNV(device: VkDevice, pGetSciSyncInfo: CTypesPointer[VkSemaphoreGetSciSyncInfoNV], pHandle: CTypesPointer[None]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkImportSemaphoreSciSyncObjNV(device: VkDevice, pImportSemaphoreSciSyncInfo: CTypesPointer[VkImportSemaphoreSciSyncInfoNV]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateSemaphoreSciSyncPoolNV(device: VkDevice, pCreateInfo: CTypesPointer[VkSemaphoreSciSyncPoolCreateInfoNV], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSemaphorePool: CTypesPointer[VkSemaphoreSciSyncPoolNV]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroySemaphoreSciSyncPoolNV(device: VkDevice, semaphorePool: VkSemaphoreSciSyncPoolNV, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDisplayPowerControlEXT(device: VkDevice, display: VkDisplayKHR, pDisplayPowerInfo: CTypesPointer[VkDisplayPowerInfoEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkRegisterDeviceEventEXT(device: VkDevice, pDeviceEventInfo: CTypesPointer[VkDeviceEventInfoEXT], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pFence: CTypesPointer[VkFence]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkRegisterDisplayEventEXT(device: VkDevice, display: VkDisplayKHR, pDisplayEventInfo: CTypesPointer[VkDisplayEventInfoEXT], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pFence: CTypesPointer[VkFence]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetSwapchainCounterEXT(device: VkDevice, swapchain: VkSwapchainKHR, counter: VkSurfaceCounterFlagBitsEXT, pCounterValue: CTypesPointer[c_uint64]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceGroupPeerMemoryFeatures(device: VkDevice, heapIndex: int, localDeviceIndex: int, remoteDeviceIndex: int, pPeerMemoryFeatures: CTypesPointer[VkPeerMemoryFeatureFlags]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceGroupPeerMemoryFeaturesKHR(device: VkDevice, heapIndex: int, localDeviceIndex: int, remoteDeviceIndex: int, pPeerMemoryFeatures: CTypesPointer[VkPeerMemoryFeatureFlags]) -> None:  # Alias of vkGetDeviceGroupPeerMemoryFeatures
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkBindBufferMemory2(device: VkDevice, bindInfoCount: int, pBindInfos: CTypesPointer[VkBindBufferMemoryInfo]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkBindBufferMemory2KHR(device: VkDevice, bindInfoCount: int, pBindInfos: CTypesPointer[VkBindBufferMemoryInfo]) -> VkResult:  # Alias of vkBindBufferMemory2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkBindImageMemory2(device: VkDevice, bindInfoCount: int, pBindInfos: CTypesPointer[VkBindImageMemoryInfo]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkBindImageMemory2KHR(device: VkDevice, bindInfoCount: int, pBindInfos: CTypesPointer[VkBindImageMemoryInfo]) -> VkResult:  # Alias of vkBindImageMemory2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDeviceMask(commandBuffer: VkCommandBuffer, deviceMask: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDeviceMaskKHR(commandBuffer: VkCommandBuffer, deviceMask: int) -> None:  # Alias of vkCmdSetDeviceMask
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceGroupPresentCapabilitiesKHR(device: VkDevice, pDeviceGroupPresentCapabilities: CTypesPointer[VkDeviceGroupPresentCapabilitiesKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceGroupSurfacePresentModesKHR(device: VkDevice, surface: VkSurfaceKHR, pModes: CTypesPointer[VkDeviceGroupPresentModeFlagsKHR] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkAcquireNextImage2KHR(device: VkDevice, pAcquireInfo: CTypesPointer[VkAcquireNextImageInfoKHR], pImageIndex: CTypesPointer[c_uint32]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDispatchBase(commandBuffer: VkCommandBuffer, baseGroupX: int, baseGroupY: int, baseGroupZ: int, groupCountX: int, groupCountY: int, groupCountZ: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDispatchBaseKHR(commandBuffer: VkCommandBuffer, baseGroupX: int, baseGroupY: int, baseGroupZ: int, groupCountX: int, groupCountY: int, groupCountZ: int) -> None:  # Alias of vkCmdDispatchBase
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateDescriptorUpdateTemplate(device: VkDevice, pCreateInfo: CTypesPointer[VkDescriptorUpdateTemplateCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pDescriptorUpdateTemplate: CTypesPointer[VkDescriptorUpdateTemplate]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateDescriptorUpdateTemplateKHR(device: VkDevice, pCreateInfo: CTypesPointer[VkDescriptorUpdateTemplateCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pDescriptorUpdateTemplate: CTypesPointer[VkDescriptorUpdateTemplate]) -> VkResult:  # Alias of vkCreateDescriptorUpdateTemplate
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyDescriptorUpdateTemplate(device: VkDevice, descriptorUpdateTemplate: VkDescriptorUpdateTemplate, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyDescriptorUpdateTemplateKHR(device: VkDevice, descriptorUpdateTemplate: VkDescriptorUpdateTemplate, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:  # Alias of vkDestroyDescriptorUpdateTemplate
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkUpdateDescriptorSetWithTemplate(device: VkDevice, descriptorSet: VkDescriptorSet, descriptorUpdateTemplate: VkDescriptorUpdateTemplate, pData: CTypesPointer[None]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkUpdateDescriptorSetWithTemplateKHR(device: VkDevice, descriptorSet: VkDescriptorSet, descriptorUpdateTemplate: VkDescriptorUpdateTemplate, pData: CTypesPointer[None]) -> None:  # Alias of vkUpdateDescriptorSetWithTemplate
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdPushDescriptorSetWithTemplateKHR(commandBuffer: VkCommandBuffer, descriptorUpdateTemplate: VkDescriptorUpdateTemplate, layout: VkPipelineLayout, set: int, pData: CTypesPointer[None]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkSetHdrMetadataEXT(device: VkDevice, swapchainCount: int, pSwapchains: CTypesPointer[VkSwapchainKHR], pMetadata: CTypesPointer[VkHdrMetadataEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetSwapchainStatusKHR(device: VkDevice, swapchain: VkSwapchainKHR) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetRefreshCycleDurationGOOGLE(device: VkDevice, swapchain: VkSwapchainKHR, pDisplayTimingProperties: CTypesPointer[VkRefreshCycleDurationGOOGLE]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetPastPresentationTimingGOOGLE(device: VkDevice, swapchain: VkSwapchainKHR, pPresentationTimingCount: CTypesPointer[c_uint32] | None, pPresentationTimings: CTypesPointer[VkPastPresentationTimingGOOGLE] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetViewportWScalingNV(commandBuffer: VkCommandBuffer, firstViewport: int, viewportCount: int, pViewportWScalings: CTypesPointer[VkViewportWScalingNV]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDiscardRectangleEXT(commandBuffer: VkCommandBuffer, firstDiscardRectangle: int, discardRectangleCount: int, pDiscardRectangles: CTypesPointer[VkRect2D]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDiscardRectangleEnableEXT(commandBuffer: VkCommandBuffer, discardRectangleEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDiscardRectangleModeEXT(commandBuffer: VkCommandBuffer, discardRectangleMode: VkDiscardRectangleModeEXT) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetSampleLocationsEXT(commandBuffer: VkCommandBuffer, pSampleLocationsInfo: CTypesPointer[VkSampleLocationsInfoEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetBufferMemoryRequirements2(device: VkDevice, pInfo: CTypesPointer[VkBufferMemoryRequirementsInfo2], pMemoryRequirements: CTypesPointer[VkMemoryRequirements2]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetBufferMemoryRequirements2KHR(device: VkDevice, pInfo: CTypesPointer[VkBufferMemoryRequirementsInfo2], pMemoryRequirements: CTypesPointer[VkMemoryRequirements2]) -> None:  # Alias of vkGetBufferMemoryRequirements2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetImageMemoryRequirements2(device: VkDevice, pInfo: CTypesPointer[VkImageMemoryRequirementsInfo2], pMemoryRequirements: CTypesPointer[VkMemoryRequirements2]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetImageMemoryRequirements2KHR(device: VkDevice, pInfo: CTypesPointer[VkImageMemoryRequirementsInfo2], pMemoryRequirements: CTypesPointer[VkMemoryRequirements2]) -> None:  # Alias of vkGetImageMemoryRequirements2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetImageSparseMemoryRequirements2(device: VkDevice, pInfo: CTypesPointer[VkImageSparseMemoryRequirementsInfo2], pSparseMemoryRequirementCount: CTypesPointer[c_uint32] | None, pSparseMemoryRequirements: CTypesPointer[VkSparseImageMemoryRequirements2] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetImageSparseMemoryRequirements2KHR(device: VkDevice, pInfo: CTypesPointer[VkImageSparseMemoryRequirementsInfo2], pSparseMemoryRequirementCount: CTypesPointer[c_uint32] | None, pSparseMemoryRequirements: CTypesPointer[VkSparseImageMemoryRequirements2] | None) -> None:  # Alias of vkGetImageSparseMemoryRequirements2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceBufferMemoryRequirements(device: VkDevice, pInfo: CTypesPointer[VkDeviceBufferMemoryRequirements], pMemoryRequirements: CTypesPointer[VkMemoryRequirements2]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceBufferMemoryRequirementsKHR(device: VkDevice, pInfo: CTypesPointer[VkDeviceBufferMemoryRequirements], pMemoryRequirements: CTypesPointer[VkMemoryRequirements2]) -> None:  # Alias of vkGetDeviceBufferMemoryRequirements
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceImageMemoryRequirements(device: VkDevice, pInfo: CTypesPointer[VkDeviceImageMemoryRequirements], pMemoryRequirements: CTypesPointer[VkMemoryRequirements2]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceImageMemoryRequirementsKHR(device: VkDevice, pInfo: CTypesPointer[VkDeviceImageMemoryRequirements], pMemoryRequirements: CTypesPointer[VkMemoryRequirements2]) -> None:  # Alias of vkGetDeviceImageMemoryRequirements
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceImageSparseMemoryRequirements(device: VkDevice, pInfo: CTypesPointer[VkDeviceImageMemoryRequirements], pSparseMemoryRequirementCount: CTypesPointer[c_uint32] | None, pSparseMemoryRequirements: CTypesPointer[VkSparseImageMemoryRequirements2] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceImageSparseMemoryRequirementsKHR(device: VkDevice, pInfo: CTypesPointer[VkDeviceImageMemoryRequirements], pSparseMemoryRequirementCount: CTypesPointer[c_uint32] | None, pSparseMemoryRequirements: CTypesPointer[VkSparseImageMemoryRequirements2] | None) -> None:  # Alias of vkGetDeviceImageSparseMemoryRequirements
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateSamplerYcbcrConversion(device: VkDevice, pCreateInfo: CTypesPointer[VkSamplerYcbcrConversionCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pYcbcrConversion: CTypesPointer[VkSamplerYcbcrConversion]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateSamplerYcbcrConversionKHR(device: VkDevice, pCreateInfo: CTypesPointer[VkSamplerYcbcrConversionCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pYcbcrConversion: CTypesPointer[VkSamplerYcbcrConversion]) -> VkResult:  # Alias of vkCreateSamplerYcbcrConversion
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroySamplerYcbcrConversion(device: VkDevice, ycbcrConversion: VkSamplerYcbcrConversion, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroySamplerYcbcrConversionKHR(device: VkDevice, ycbcrConversion: VkSamplerYcbcrConversion, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:  # Alias of vkDestroySamplerYcbcrConversion
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceQueue2(device: VkDevice, pQueueInfo: CTypesPointer[VkDeviceQueueInfo2], pQueue: CTypesPointer[VkQueue]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateValidationCacheEXT(device: VkDevice, pCreateInfo: CTypesPointer[VkValidationCacheCreateInfoEXT], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pValidationCache: CTypesPointer[VkValidationCacheEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyValidationCacheEXT(device: VkDevice, validationCache: VkValidationCacheEXT, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetValidationCacheDataEXT(device: VkDevice, validationCache: VkValidationCacheEXT, pDataSize: CTypesPointer[c_size_t] | None, pData: CTypesPointer[None] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkMergeValidationCachesEXT(device: VkDevice, dstCache: VkValidationCacheEXT, srcCacheCount: int, pSrcCaches: CTypesPointer[VkValidationCacheEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDescriptorSetLayoutSupport(device: VkDevice, pCreateInfo: CTypesPointer[VkDescriptorSetLayoutCreateInfo], pSupport: CTypesPointer[VkDescriptorSetLayoutSupport]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDescriptorSetLayoutSupportKHR(device: VkDevice, pCreateInfo: CTypesPointer[VkDescriptorSetLayoutCreateInfo], pSupport: CTypesPointer[VkDescriptorSetLayoutSupport]) -> None:  # Alias of vkGetDescriptorSetLayoutSupport
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetSwapchainGrallocUsageANDROID(device: VkDevice, format: VkFormat, imageUsage: VkImageUsageFlags, grallocUsage: CTypesPointer[int]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetSwapchainGrallocUsage2ANDROID(device: VkDevice, format: VkFormat, imageUsage: VkImageUsageFlags, swapchainImageUsage: VkSwapchainImageUsageFlagsANDROID, grallocConsumerUsage: CTypesPointer[c_uint64], grallocProducerUsage: CTypesPointer[c_uint64]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkAcquireImageANDROID(device: VkDevice, image: VkImage, nativeFenceFd: int, semaphore: VkSemaphore, fence: VkFence) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkQueueSignalReleaseImageANDROID(queue: VkQueue, waitSemaphoreCount: int, pWaitSemaphores: CTypesPointer[VkSemaphore], image: VkImage, pNativeFenceFd: CTypesPointer[int]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetShaderInfoAMD(device: VkDevice, pipeline: VkPipeline, shaderStage: VkShaderStageFlagBits, infoType: VkShaderInfoTypeAMD, pInfoSize: CTypesPointer[c_size_t] | None, pInfo: CTypesPointer[None] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkSetLocalDimmingAMD(device: VkDevice, swapChain: VkSwapchainKHR, localDimmingEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetCalibratedTimestampsKHR(device: VkDevice, timestampCount: int, pTimestampInfos: CTypesPointer[VkCalibratedTimestampInfoKHR], pTimestamps: CTypesPointer[c_uint64], pMaxDeviation: CTypesPointer[c_uint64]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetCalibratedTimestampsEXT(device: VkDevice, timestampCount: int, pTimestampInfos: CTypesPointer[VkCalibratedTimestampInfoKHR], pTimestamps: CTypesPointer[c_uint64], pMaxDeviation: CTypesPointer[c_uint64]) -> VkResult:  # Alias of vkGetCalibratedTimestampsKHR
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkSetDebugUtilsObjectNameEXT(device: VkDevice, pNameInfo: CTypesPointer[VkDebugUtilsObjectNameInfoEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkSetDebugUtilsObjectTagEXT(device: VkDevice, pTagInfo: CTypesPointer[VkDebugUtilsObjectTagInfoEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkQueueBeginDebugUtilsLabelEXT(queue: VkQueue, pLabelInfo: CTypesPointer[VkDebugUtilsLabelEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkQueueEndDebugUtilsLabelEXT(queue: VkQueue) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkQueueInsertDebugUtilsLabelEXT(queue: VkQueue, pLabelInfo: CTypesPointer[VkDebugUtilsLabelEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBeginDebugUtilsLabelEXT(commandBuffer: VkCommandBuffer, pLabelInfo: CTypesPointer[VkDebugUtilsLabelEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdEndDebugUtilsLabelEXT(commandBuffer: VkCommandBuffer) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdInsertDebugUtilsLabelEXT(commandBuffer: VkCommandBuffer, pLabelInfo: CTypesPointer[VkDebugUtilsLabelEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetMemoryHostPointerPropertiesEXT(device: VkDevice, handleType: VkExternalMemoryHandleTypeFlagBits, pHostPointer: CTypesPointer[None], pMemoryHostPointerProperties: CTypesPointer[VkMemoryHostPointerPropertiesEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdWriteBufferMarkerAMD(commandBuffer: VkCommandBuffer, pipelineStage: VkPipelineStageFlagBits, dstBuffer: VkBuffer, dstOffset: VkDeviceSize, marker: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateRenderPass2(device: VkDevice, pCreateInfo: CTypesPointer[VkRenderPassCreateInfo2], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pRenderPass: CTypesPointer[VkRenderPass]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateRenderPass2KHR(device: VkDevice, pCreateInfo: CTypesPointer[VkRenderPassCreateInfo2], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pRenderPass: CTypesPointer[VkRenderPass]) -> VkResult:  # Alias of vkCreateRenderPass2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBeginRenderPass2(commandBuffer: VkCommandBuffer, pRenderPassBegin: CTypesPointer[VkRenderPassBeginInfo], pSubpassBeginInfo: CTypesPointer[VkSubpassBeginInfo]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBeginRenderPass2KHR(commandBuffer: VkCommandBuffer, pRenderPassBegin: CTypesPointer[VkRenderPassBeginInfo], pSubpassBeginInfo: CTypesPointer[VkSubpassBeginInfo]) -> None:  # Alias of vkCmdBeginRenderPass2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdNextSubpass2(commandBuffer: VkCommandBuffer, pSubpassBeginInfo: CTypesPointer[VkSubpassBeginInfo], pSubpassEndInfo: CTypesPointer[VkSubpassEndInfo]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdNextSubpass2KHR(commandBuffer: VkCommandBuffer, pSubpassBeginInfo: CTypesPointer[VkSubpassBeginInfo], pSubpassEndInfo: CTypesPointer[VkSubpassEndInfo]) -> None:  # Alias of vkCmdNextSubpass2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdEndRenderPass2(commandBuffer: VkCommandBuffer, pSubpassEndInfo: CTypesPointer[VkSubpassEndInfo]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdEndRenderPass2KHR(commandBuffer: VkCommandBuffer, pSubpassEndInfo: CTypesPointer[VkSubpassEndInfo]) -> None:  # Alias of vkCmdEndRenderPass2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetSemaphoreCounterValue(device: VkDevice, semaphore: VkSemaphore, pValue: CTypesPointer[c_uint64]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetSemaphoreCounterValueKHR(device: VkDevice, semaphore: VkSemaphore, pValue: CTypesPointer[c_uint64]) -> VkResult:  # Alias of vkGetSemaphoreCounterValue
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkWaitSemaphores(device: VkDevice, pWaitInfo: CTypesPointer[VkSemaphoreWaitInfo], timeout: int) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkWaitSemaphoresKHR(device: VkDevice, pWaitInfo: CTypesPointer[VkSemaphoreWaitInfo], timeout: int) -> VkResult:  # Alias of vkWaitSemaphores
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkSignalSemaphore(device: VkDevice, pSignalInfo: CTypesPointer[VkSemaphoreSignalInfo]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkSignalSemaphoreKHR(device: VkDevice, pSignalInfo: CTypesPointer[VkSemaphoreSignalInfo]) -> VkResult:  # Alias of vkSignalSemaphore
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetAndroidHardwareBufferPropertiesANDROID(device: VkDevice, buffer: CTypesPointer[AHardwareBuffer], pProperties: CTypesPointer[VkAndroidHardwareBufferPropertiesANDROID]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetMemoryAndroidHardwareBufferANDROID(device: VkDevice, pInfo: CTypesPointer[VkMemoryGetAndroidHardwareBufferInfoANDROID], pBuffer: CTypesPointer[AHardwareBuffer]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawIndirectCount(commandBuffer: VkCommandBuffer, buffer: VkBuffer, offset: VkDeviceSize, countBuffer: VkBuffer, countBufferOffset: VkDeviceSize, maxDrawCount: int, stride: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawIndirectCountKHR(commandBuffer: VkCommandBuffer, buffer: VkBuffer, offset: VkDeviceSize, countBuffer: VkBuffer, countBufferOffset: VkDeviceSize, maxDrawCount: int, stride: int) -> None:  # Alias of vkCmdDrawIndirectCount
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawIndirectCountAMD(commandBuffer: VkCommandBuffer, buffer: VkBuffer, offset: VkDeviceSize, countBuffer: VkBuffer, countBufferOffset: VkDeviceSize, maxDrawCount: int, stride: int) -> None:  # Alias of vkCmdDrawIndirectCount
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawIndexedIndirectCount(commandBuffer: VkCommandBuffer, buffer: VkBuffer, offset: VkDeviceSize, countBuffer: VkBuffer, countBufferOffset: VkDeviceSize, maxDrawCount: int, stride: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawIndexedIndirectCountKHR(commandBuffer: VkCommandBuffer, buffer: VkBuffer, offset: VkDeviceSize, countBuffer: VkBuffer, countBufferOffset: VkDeviceSize, maxDrawCount: int, stride: int) -> None:  # Alias of vkCmdDrawIndexedIndirectCount
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawIndexedIndirectCountAMD(commandBuffer: VkCommandBuffer, buffer: VkBuffer, offset: VkDeviceSize, countBuffer: VkBuffer, countBufferOffset: VkDeviceSize, maxDrawCount: int, stride: int) -> None:  # Alias of vkCmdDrawIndexedIndirectCount
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetCheckpointNV(commandBuffer: VkCommandBuffer, pCheckpointMarker: CTypesPointer[None]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetQueueCheckpointDataNV(queue: VkQueue, pCheckpointDataCount: CTypesPointer[c_uint32] | None, pCheckpointData: CTypesPointer[VkCheckpointDataNV] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBindTransformFeedbackBuffersEXT(commandBuffer: VkCommandBuffer, firstBinding: int, bindingCount: int, pBuffers: CTypesPointer[VkBuffer], pOffsets: CTypesPointer[VkDeviceSize], pSizes: CTypesPointer[VkDeviceSize] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBeginTransformFeedbackEXT(commandBuffer: VkCommandBuffer, firstCounterBuffer: int, counterBufferCount: int, pCounterBuffers: CTypesPointer[VkBuffer], pCounterBufferOffsets: CTypesPointer[VkDeviceSize] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdEndTransformFeedbackEXT(commandBuffer: VkCommandBuffer, firstCounterBuffer: int, counterBufferCount: int, pCounterBuffers: CTypesPointer[VkBuffer], pCounterBufferOffsets: CTypesPointer[VkDeviceSize] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBeginQueryIndexedEXT(commandBuffer: VkCommandBuffer, queryPool: VkQueryPool, query: int, flags: VkQueryControlFlags, index: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdEndQueryIndexedEXT(commandBuffer: VkCommandBuffer, queryPool: VkQueryPool, query: int, index: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawIndirectByteCountEXT(commandBuffer: VkCommandBuffer, instanceCount: int, firstInstance: int, counterBuffer: VkBuffer, counterBufferOffset: VkDeviceSize, counterOffset: int, vertexStride: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetExclusiveScissorNV(commandBuffer: VkCommandBuffer, firstExclusiveScissor: int, exclusiveScissorCount: int, pExclusiveScissors: CTypesPointer[VkRect2D]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetExclusiveScissorEnableNV(commandBuffer: VkCommandBuffer, firstExclusiveScissor: int, exclusiveScissorCount: int, pExclusiveScissorEnables: CTypesPointer[VkBool32]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBindShadingRateImageNV(commandBuffer: VkCommandBuffer, imageView: VkImageView, imageLayout: VkImageLayout) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetViewportShadingRatePaletteNV(commandBuffer: VkCommandBuffer, firstViewport: int, viewportCount: int, pShadingRatePalettes: CTypesPointer[VkShadingRatePaletteNV]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetCoarseSampleOrderNV(commandBuffer: VkCommandBuffer, sampleOrderType: VkCoarseSampleOrderTypeNV, customSampleOrderCount: int, pCustomSampleOrders: CTypesPointer[VkCoarseSampleOrderCustomNV]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawMeshTasksNV(commandBuffer: VkCommandBuffer, taskCount: int, firstTask: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawMeshTasksIndirectNV(commandBuffer: VkCommandBuffer, buffer: VkBuffer, offset: VkDeviceSize, drawCount: int, stride: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawMeshTasksIndirectCountNV(commandBuffer: VkCommandBuffer, buffer: VkBuffer, offset: VkDeviceSize, countBuffer: VkBuffer, countBufferOffset: VkDeviceSize, maxDrawCount: int, stride: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawMeshTasksEXT(commandBuffer: VkCommandBuffer, groupCountX: int, groupCountY: int, groupCountZ: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawMeshTasksIndirectEXT(commandBuffer: VkCommandBuffer, buffer: VkBuffer, offset: VkDeviceSize, drawCount: int, stride: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDrawMeshTasksIndirectCountEXT(commandBuffer: VkCommandBuffer, buffer: VkBuffer, offset: VkDeviceSize, countBuffer: VkBuffer, countBufferOffset: VkDeviceSize, maxDrawCount: int, stride: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCompileDeferredNV(device: VkDevice, pipeline: VkPipeline, shader: int) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateAccelerationStructureNV(device: VkDevice, pCreateInfo: CTypesPointer[VkAccelerationStructureCreateInfoNV], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pAccelerationStructure: CTypesPointer[VkAccelerationStructureNV]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBindInvocationMaskHUAWEI(commandBuffer: VkCommandBuffer, imageView: VkImageView, imageLayout: VkImageLayout) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyAccelerationStructureKHR(device: VkDevice, accelerationStructure: VkAccelerationStructureKHR, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyAccelerationStructureNV(device: VkDevice, accelerationStructure: VkAccelerationStructureNV, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetAccelerationStructureMemoryRequirementsNV(device: VkDevice, pInfo: CTypesPointer[VkAccelerationStructureMemoryRequirementsInfoNV], pMemoryRequirements: CTypesPointer[VkMemoryRequirements2KHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkBindAccelerationStructureMemoryNV(device: VkDevice, bindInfoCount: int, pBindInfos: CTypesPointer[VkBindAccelerationStructureMemoryInfoNV]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyAccelerationStructureNV(commandBuffer: VkCommandBuffer, dst: VkAccelerationStructureNV, src: VkAccelerationStructureNV, mode: VkCopyAccelerationStructureModeKHR) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyAccelerationStructureKHR(commandBuffer: VkCommandBuffer, pInfo: CTypesPointer[VkCopyAccelerationStructureInfoKHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCopyAccelerationStructureKHR(device: VkDevice, deferredOperation: VkDeferredOperationKHR, pInfo: CTypesPointer[VkCopyAccelerationStructureInfoKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyAccelerationStructureToMemoryKHR(commandBuffer: VkCommandBuffer, pInfo: CTypesPointer[VkCopyAccelerationStructureToMemoryInfoKHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCopyAccelerationStructureToMemoryKHR(device: VkDevice, deferredOperation: VkDeferredOperationKHR, pInfo: CTypesPointer[VkCopyAccelerationStructureToMemoryInfoKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyMemoryToAccelerationStructureKHR(commandBuffer: VkCommandBuffer, pInfo: CTypesPointer[VkCopyMemoryToAccelerationStructureInfoKHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCopyMemoryToAccelerationStructureKHR(device: VkDevice, deferredOperation: VkDeferredOperationKHR, pInfo: CTypesPointer[VkCopyMemoryToAccelerationStructureInfoKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdWriteAccelerationStructuresPropertiesKHR(commandBuffer: VkCommandBuffer, accelerationStructureCount: int, pAccelerationStructures: CTypesPointer[VkAccelerationStructureKHR], queryType: VkQueryType, queryPool: VkQueryPool, firstQuery: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdWriteAccelerationStructuresPropertiesNV(commandBuffer: VkCommandBuffer, accelerationStructureCount: int, pAccelerationStructures: CTypesPointer[VkAccelerationStructureNV], queryType: VkQueryType, queryPool: VkQueryPool, firstQuery: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBuildAccelerationStructureNV(commandBuffer: VkCommandBuffer, pInfo: CTypesPointer[VkAccelerationStructureInfoNV], instanceData: VkBuffer, instanceOffset: VkDeviceSize, update: VkBool32, dst: VkAccelerationStructureNV, src: VkAccelerationStructureNV, scratch: VkBuffer, scratchOffset: VkDeviceSize) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkWriteAccelerationStructuresPropertiesKHR(device: VkDevice, accelerationStructureCount: int, pAccelerationStructures: CTypesPointer[VkAccelerationStructureKHR], queryType: VkQueryType, dataSize: int, pData: CTypesPointer[None], stride: int) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdTraceRaysKHR(commandBuffer: VkCommandBuffer, pRaygenShaderBindingTable: CTypesPointer[VkStridedDeviceAddressRegionKHR], pMissShaderBindingTable: CTypesPointer[VkStridedDeviceAddressRegionKHR], pHitShaderBindingTable: CTypesPointer[VkStridedDeviceAddressRegionKHR], pCallableShaderBindingTable: CTypesPointer[VkStridedDeviceAddressRegionKHR], width: int, height: int, depth: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdTraceRaysNV(commandBuffer: VkCommandBuffer, raygenShaderBindingTableBuffer: VkBuffer, raygenShaderBindingOffset: VkDeviceSize, missShaderBindingTableBuffer: VkBuffer, missShaderBindingOffset: VkDeviceSize, missShaderBindingStride: VkDeviceSize, hitShaderBindingTableBuffer: VkBuffer, hitShaderBindingOffset: VkDeviceSize, hitShaderBindingStride: VkDeviceSize, callableShaderBindingTableBuffer: VkBuffer, callableShaderBindingOffset: VkDeviceSize, callableShaderBindingStride: VkDeviceSize, width: int, height: int, depth: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetRayTracingShaderGroupHandlesKHR(device: VkDevice, pipeline: VkPipeline, firstGroup: int, groupCount: int, dataSize: int, pData: CTypesPointer[None]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetRayTracingShaderGroupHandlesNV(device: VkDevice, pipeline: VkPipeline, firstGroup: int, groupCount: int, dataSize: int, pData: CTypesPointer[None]) -> VkResult:  # Alias of vkGetRayTracingShaderGroupHandlesKHR
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetRayTracingCaptureReplayShaderGroupHandlesKHR(device: VkDevice, pipeline: VkPipeline, firstGroup: int, groupCount: int, dataSize: int, pData: CTypesPointer[None]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetAccelerationStructureHandleNV(device: VkDevice, accelerationStructure: VkAccelerationStructureNV, dataSize: int, pData: CTypesPointer[None]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateRayTracingPipelinesNV(device: VkDevice, pipelineCache: VkPipelineCache, createInfoCount: int, pCreateInfos: CTypesPointer[VkRayTracingPipelineCreateInfoNV], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pPipelines: CTypesPointer[VkPipeline]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateRayTracingPipelinesNV(device: VkDevice, pipelineCache: VkPipelineCache, createInfoCount: int, pCreateInfos: CTypesPointer[VkRayTracingPipelineCreateInfoNV], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pPipelines: CTypesPointer[VkPipeline]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateRayTracingPipelinesKHR(device: VkDevice, deferredOperation: VkDeferredOperationKHR, pipelineCache: VkPipelineCache, createInfoCount: int, pCreateInfos: CTypesPointer[VkRayTracingPipelineCreateInfoKHR], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pPipelines: CTypesPointer[VkPipeline]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateRayTracingPipelinesKHR(device: VkDevice, deferredOperation: VkDeferredOperationKHR, pipelineCache: VkPipelineCache, createInfoCount: int, pCreateInfos: CTypesPointer[VkRayTracingPipelineCreateInfoKHR], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pPipelines: CTypesPointer[VkPipeline]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdTraceRaysIndirectKHR(commandBuffer: VkCommandBuffer, pRaygenShaderBindingTable: CTypesPointer[VkStridedDeviceAddressRegionKHR], pMissShaderBindingTable: CTypesPointer[VkStridedDeviceAddressRegionKHR], pHitShaderBindingTable: CTypesPointer[VkStridedDeviceAddressRegionKHR], pCallableShaderBindingTable: CTypesPointer[VkStridedDeviceAddressRegionKHR], indirectDeviceAddress: VkDeviceAddress) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdTraceRaysIndirect2KHR(commandBuffer: VkCommandBuffer, indirectDeviceAddress: VkDeviceAddress) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceAccelerationStructureCompatibilityKHR(device: VkDevice, pVersionInfo: CTypesPointer[VkAccelerationStructureVersionInfoKHR], pCompatibility: CTypesPointer[VkAccelerationStructureCompatibilityKHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetRayTracingShaderGroupStackSizeKHR(device: VkDevice, pipeline: VkPipeline, group: int, groupShader: VkShaderGroupShaderKHR) -> VkDeviceSize:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetRayTracingPipelineStackSizeKHR(commandBuffer: VkCommandBuffer, pipelineStackSize: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetImageViewHandleNVX(device: VkDevice, pInfo: CTypesPointer[VkImageViewHandleInfoNVX]) -> c_uint32:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetImageViewAddressNVX(device: VkDevice, imageView: VkImageView, pProperties: CTypesPointer[VkImageViewAddressPropertiesNVX]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceGroupSurfacePresentModes2EXT(device: VkDevice, pSurfaceInfo: CTypesPointer[VkPhysicalDeviceSurfaceInfo2KHR], pModes: CTypesPointer[VkDeviceGroupPresentModeFlagsKHR] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkAcquireFullScreenExclusiveModeEXT(device: VkDevice, swapchain: VkSwapchainKHR) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkReleaseFullScreenExclusiveModeEXT(device: VkDevice, swapchain: VkSwapchainKHR) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkAcquireProfilingLockKHR(device: VkDevice, pInfo: CTypesPointer[VkAcquireProfilingLockInfoKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkReleaseProfilingLockKHR(device: VkDevice) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetImageDrmFormatModifierPropertiesEXT(device: VkDevice, image: VkImage, pProperties: CTypesPointer[VkImageDrmFormatModifierPropertiesEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetBufferOpaqueCaptureAddress(device: VkDevice, pInfo: CTypesPointer[VkBufferDeviceAddressInfo]) -> c_uint64:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetBufferOpaqueCaptureAddressKHR(device: VkDevice, pInfo: CTypesPointer[VkBufferDeviceAddressInfo]) -> c_uint64:  # Alias of vkGetBufferOpaqueCaptureAddress
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetBufferDeviceAddress(device: VkDevice, pInfo: CTypesPointer[VkBufferDeviceAddressInfo]) -> VkDeviceAddress:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetBufferDeviceAddressKHR(device: VkDevice, pInfo: CTypesPointer[VkBufferDeviceAddressInfo]) -> VkDeviceAddress:  # Alias of vkGetBufferDeviceAddress
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetBufferDeviceAddressEXT(device: VkDevice, pInfo: CTypesPointer[VkBufferDeviceAddressInfo]) -> VkDeviceAddress:  # Alias of vkGetBufferDeviceAddress
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkInitializePerformanceApiINTEL(device: VkDevice, pInitializeInfo: CTypesPointer[VkInitializePerformanceApiInfoINTEL]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkUninitializePerformanceApiINTEL(device: VkDevice) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetPerformanceMarkerINTEL(commandBuffer: VkCommandBuffer, pMarkerInfo: CTypesPointer[VkPerformanceMarkerInfoINTEL]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetPerformanceStreamMarkerINTEL(commandBuffer: VkCommandBuffer, pMarkerInfo: CTypesPointer[VkPerformanceStreamMarkerInfoINTEL]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetPerformanceOverrideINTEL(commandBuffer: VkCommandBuffer, pOverrideInfo: CTypesPointer[VkPerformanceOverrideInfoINTEL]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkAcquirePerformanceConfigurationINTEL(device: VkDevice, pAcquireInfo: CTypesPointer[VkPerformanceConfigurationAcquireInfoINTEL], pConfiguration: CTypesPointer[VkPerformanceConfigurationINTEL]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkReleasePerformanceConfigurationINTEL(device: VkDevice, configuration: VkPerformanceConfigurationINTEL) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkQueueSetPerformanceConfigurationINTEL(queue: VkQueue, configuration: VkPerformanceConfigurationINTEL) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetPerformanceParameterINTEL(device: VkDevice, parameter: VkPerformanceParameterTypeINTEL, pValue: CTypesPointer[VkPerformanceValueINTEL]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceMemoryOpaqueCaptureAddress(device: VkDevice, pInfo: CTypesPointer[VkDeviceMemoryOpaqueCaptureAddressInfo]) -> c_uint64:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceMemoryOpaqueCaptureAddressKHR(device: VkDevice, pInfo: CTypesPointer[VkDeviceMemoryOpaqueCaptureAddressInfo]) -> c_uint64:  # Alias of vkGetDeviceMemoryOpaqueCaptureAddress
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetPipelineExecutablePropertiesKHR(device: VkDevice, pPipelineInfo: CTypesPointer[VkPipelineInfoKHR], pExecutableCount: CTypesPointer[c_uint32] | None, pProperties: CTypesPointer[VkPipelineExecutablePropertiesKHR] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetPipelineExecutableStatisticsKHR(device: VkDevice, pExecutableInfo: CTypesPointer[VkPipelineExecutableInfoKHR], pStatisticCount: CTypesPointer[c_uint32] | None, pStatistics: CTypesPointer[VkPipelineExecutableStatisticKHR] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetPipelineExecutableInternalRepresentationsKHR(device: VkDevice, pExecutableInfo: CTypesPointer[VkPipelineExecutableInfoKHR], pInternalRepresentationCount: CTypesPointer[c_uint32] | None, pInternalRepresentations: CTypesPointer[VkPipelineExecutableInternalRepresentationKHR] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetLineStippleKHR(commandBuffer: VkCommandBuffer, lineStippleFactor: int, lineStipplePattern: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetLineStippleEXT(commandBuffer: VkCommandBuffer, lineStippleFactor: int, lineStipplePattern: int) -> None:  # Alias of vkCmdSetLineStippleKHR
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetFaultData(device: VkDevice, faultQueryBehavior: VkFaultQueryBehavior, pUnrecordedFaults: CTypesPointer[VkBool32], pFaultCount: CTypesPointer[c_uint32] | None, pFaults: CTypesPointer[VkFaultData] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateAccelerationStructureKHR(device: VkDevice, pCreateInfo: CTypesPointer[VkAccelerationStructureCreateInfoKHR], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pAccelerationStructure: CTypesPointer[VkAccelerationStructureKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBuildAccelerationStructuresKHR(commandBuffer: VkCommandBuffer, infoCount: int, pInfos: CTypesPointer[VkAccelerationStructureBuildGeometryInfoKHR], ppBuildRangeInfos: CTypesPointer[VkAccelerationStructureBuildRangeInfoKHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBuildAccelerationStructuresIndirectKHR(commandBuffer: VkCommandBuffer, infoCount: int, pInfos: CTypesPointer[VkAccelerationStructureBuildGeometryInfoKHR], pIndirectDeviceAddresses: CTypesPointer[VkDeviceAddress], pIndirectStrides: CTypesPointer[c_uint32], ppMaxPrimitiveCounts: CTypesPointer[c_uint32]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkBuildAccelerationStructuresKHR(device: VkDevice, deferredOperation: VkDeferredOperationKHR, infoCount: int, pInfos: CTypesPointer[VkAccelerationStructureBuildGeometryInfoKHR], ppBuildRangeInfos: CTypesPointer[VkAccelerationStructureBuildRangeInfoKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetAccelerationStructureDeviceAddressKHR(device: VkDevice, pInfo: CTypesPointer[VkAccelerationStructureDeviceAddressInfoKHR]) -> VkDeviceAddress:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateDeferredOperationKHR(device: VkDevice, pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pDeferredOperation: CTypesPointer[VkDeferredOperationKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyDeferredOperationKHR(device: VkDevice, operation: VkDeferredOperationKHR, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeferredOperationMaxConcurrencyKHR(device: VkDevice, operation: VkDeferredOperationKHR) -> c_uint32:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeferredOperationResultKHR(device: VkDevice, operation: VkDeferredOperationKHR) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDeferredOperationJoinKHR(device: VkDevice, operation: VkDeferredOperationKHR) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetPipelineIndirectMemoryRequirementsNV(device: VkDevice, pCreateInfo: CTypesPointer[VkComputePipelineCreateInfo], pMemoryRequirements: CTypesPointer[VkMemoryRequirements2]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetPipelineIndirectDeviceAddressNV(device: VkDevice, pInfo: CTypesPointer[VkPipelineIndirectDeviceAddressInfoNV]) -> VkDeviceAddress:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkAntiLagUpdateAMD(device: VkDevice, pData: CTypesPointer[VkAntiLagDataAMD]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetCullMode(commandBuffer: VkCommandBuffer, cullMode: VkCullModeFlags) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetCullModeEXT(commandBuffer: VkCommandBuffer, cullMode: VkCullModeFlags) -> None:  # Alias of vkCmdSetCullMode
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetFrontFace(commandBuffer: VkCommandBuffer, frontFace: VkFrontFace) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetFrontFaceEXT(commandBuffer: VkCommandBuffer, frontFace: VkFrontFace) -> None:  # Alias of vkCmdSetFrontFace
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetPrimitiveTopology(commandBuffer: VkCommandBuffer, primitiveTopology: VkPrimitiveTopology) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetPrimitiveTopologyEXT(commandBuffer: VkCommandBuffer, primitiveTopology: VkPrimitiveTopology) -> None:  # Alias of vkCmdSetPrimitiveTopology
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetViewportWithCount(commandBuffer: VkCommandBuffer, viewportCount: int, pViewports: CTypesPointer[VkViewport]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetViewportWithCountEXT(commandBuffer: VkCommandBuffer, viewportCount: int, pViewports: CTypesPointer[VkViewport]) -> None:  # Alias of vkCmdSetViewportWithCount
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetScissorWithCount(commandBuffer: VkCommandBuffer, scissorCount: int, pScissors: CTypesPointer[VkRect2D]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetScissorWithCountEXT(commandBuffer: VkCommandBuffer, scissorCount: int, pScissors: CTypesPointer[VkRect2D]) -> None:  # Alias of vkCmdSetScissorWithCount
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBindIndexBuffer2KHR(commandBuffer: VkCommandBuffer, buffer: VkBuffer, offset: VkDeviceSize, size: VkDeviceSize, indexType: VkIndexType) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBindVertexBuffers2(commandBuffer: VkCommandBuffer, firstBinding: int, bindingCount: int, pBuffers: CTypesPointer[VkBuffer] | None, pOffsets: CTypesPointer[VkDeviceSize], pSizes: CTypesPointer[VkDeviceSize] | None, pStrides: CTypesPointer[VkDeviceSize] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBindVertexBuffers2EXT(commandBuffer: VkCommandBuffer, firstBinding: int, bindingCount: int, pBuffers: CTypesPointer[VkBuffer] | None, pOffsets: CTypesPointer[VkDeviceSize], pSizes: CTypesPointer[VkDeviceSize] | None, pStrides: CTypesPointer[VkDeviceSize] | None) -> None:  # Alias of vkCmdBindVertexBuffers2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDepthTestEnable(commandBuffer: VkCommandBuffer, depthTestEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDepthTestEnableEXT(commandBuffer: VkCommandBuffer, depthTestEnable: VkBool32) -> None:  # Alias of vkCmdSetDepthTestEnable
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDepthWriteEnable(commandBuffer: VkCommandBuffer, depthWriteEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDepthWriteEnableEXT(commandBuffer: VkCommandBuffer, depthWriteEnable: VkBool32) -> None:  # Alias of vkCmdSetDepthWriteEnable
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDepthCompareOp(commandBuffer: VkCommandBuffer, depthCompareOp: VkCompareOp) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDepthCompareOpEXT(commandBuffer: VkCommandBuffer, depthCompareOp: VkCompareOp) -> None:  # Alias of vkCmdSetDepthCompareOp
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDepthBoundsTestEnable(commandBuffer: VkCommandBuffer, depthBoundsTestEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDepthBoundsTestEnableEXT(commandBuffer: VkCommandBuffer, depthBoundsTestEnable: VkBool32) -> None:  # Alias of vkCmdSetDepthBoundsTestEnable
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetStencilTestEnable(commandBuffer: VkCommandBuffer, stencilTestEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetStencilTestEnableEXT(commandBuffer: VkCommandBuffer, stencilTestEnable: VkBool32) -> None:  # Alias of vkCmdSetStencilTestEnable
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetStencilOp(commandBuffer: VkCommandBuffer, faceMask: VkStencilFaceFlags, failOp: VkStencilOp, passOp: VkStencilOp, depthFailOp: VkStencilOp, compareOp: VkCompareOp) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetStencilOpEXT(commandBuffer: VkCommandBuffer, faceMask: VkStencilFaceFlags, failOp: VkStencilOp, passOp: VkStencilOp, depthFailOp: VkStencilOp, compareOp: VkCompareOp) -> None:  # Alias of vkCmdSetStencilOp
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetPatchControlPointsEXT(commandBuffer: VkCommandBuffer, patchControlPoints: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetRasterizerDiscardEnable(commandBuffer: VkCommandBuffer, rasterizerDiscardEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetRasterizerDiscardEnableEXT(commandBuffer: VkCommandBuffer, rasterizerDiscardEnable: VkBool32) -> None:  # Alias of vkCmdSetRasterizerDiscardEnable
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDepthBiasEnable(commandBuffer: VkCommandBuffer, depthBiasEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDepthBiasEnableEXT(commandBuffer: VkCommandBuffer, depthBiasEnable: VkBool32) -> None:  # Alias of vkCmdSetDepthBiasEnable
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetLogicOpEXT(commandBuffer: VkCommandBuffer, logicOp: VkLogicOp) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetPrimitiveRestartEnable(commandBuffer: VkCommandBuffer, primitiveRestartEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetPrimitiveRestartEnableEXT(commandBuffer: VkCommandBuffer, primitiveRestartEnable: VkBool32) -> None:  # Alias of vkCmdSetPrimitiveRestartEnable
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetTessellationDomainOriginEXT(commandBuffer: VkCommandBuffer, domainOrigin: VkTessellationDomainOrigin) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDepthClampEnableEXT(commandBuffer: VkCommandBuffer, depthClampEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetPolygonModeEXT(commandBuffer: VkCommandBuffer, polygonMode: VkPolygonMode) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetRasterizationSamplesEXT(commandBuffer: VkCommandBuffer, rasterizationSamples: VkSampleCountFlagBits) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetSampleMaskEXT(commandBuffer: VkCommandBuffer, samples: VkSampleCountFlagBits, pSampleMask: CTypesPointer[VkSampleMask]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetAlphaToCoverageEnableEXT(commandBuffer: VkCommandBuffer, alphaToCoverageEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetAlphaToOneEnableEXT(commandBuffer: VkCommandBuffer, alphaToOneEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetLogicOpEnableEXT(commandBuffer: VkCommandBuffer, logicOpEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetColorBlendEnableEXT(commandBuffer: VkCommandBuffer, firstAttachment: int, attachmentCount: int, pColorBlendEnables: CTypesPointer[VkBool32]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetColorBlendEquationEXT(commandBuffer: VkCommandBuffer, firstAttachment: int, attachmentCount: int, pColorBlendEquations: CTypesPointer[VkColorBlendEquationEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetColorWriteMaskEXT(commandBuffer: VkCommandBuffer, firstAttachment: int, attachmentCount: int, pColorWriteMasks: CTypesPointer[VkColorComponentFlags] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetRasterizationStreamEXT(commandBuffer: VkCommandBuffer, rasterizationStream: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetConservativeRasterizationModeEXT(commandBuffer: VkCommandBuffer, conservativeRasterizationMode: VkConservativeRasterizationModeEXT) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetExtraPrimitiveOverestimationSizeEXT(commandBuffer: VkCommandBuffer, extraPrimitiveOverestimationSize: float) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDepthClipEnableEXT(commandBuffer: VkCommandBuffer, depthClipEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetSampleLocationsEnableEXT(commandBuffer: VkCommandBuffer, sampleLocationsEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetColorBlendAdvancedEXT(commandBuffer: VkCommandBuffer, firstAttachment: int, attachmentCount: int, pColorBlendAdvanced: CTypesPointer[VkColorBlendAdvancedEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetProvokingVertexModeEXT(commandBuffer: VkCommandBuffer, provokingVertexMode: VkProvokingVertexModeEXT) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetLineRasterizationModeEXT(commandBuffer: VkCommandBuffer, lineRasterizationMode: VkLineRasterizationModeEXT) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetLineStippleEnableEXT(commandBuffer: VkCommandBuffer, stippledLineEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDepthClipNegativeOneToOneEXT(commandBuffer: VkCommandBuffer, negativeOneToOne: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetViewportWScalingEnableNV(commandBuffer: VkCommandBuffer, viewportWScalingEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetViewportSwizzleNV(commandBuffer: VkCommandBuffer, firstViewport: int, viewportCount: int, pViewportSwizzles: CTypesPointer[VkViewportSwizzleNV]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetCoverageToColorEnableNV(commandBuffer: VkCommandBuffer, coverageToColorEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetCoverageToColorLocationNV(commandBuffer: VkCommandBuffer, coverageToColorLocation: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetCoverageModulationModeNV(commandBuffer: VkCommandBuffer, coverageModulationMode: VkCoverageModulationModeNV) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetCoverageModulationTableEnableNV(commandBuffer: VkCommandBuffer, coverageModulationTableEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetCoverageModulationTableNV(commandBuffer: VkCommandBuffer, coverageModulationTableCount: int, pCoverageModulationTable: CTypesPointer[c_float]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetShadingRateImageEnableNV(commandBuffer: VkCommandBuffer, shadingRateImageEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetCoverageReductionModeNV(commandBuffer: VkCommandBuffer, coverageReductionMode: VkCoverageReductionModeNV) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetRepresentativeFragmentTestEnableNV(commandBuffer: VkCommandBuffer, representativeFragmentTestEnable: VkBool32) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreatePrivateDataSlot(device: VkDevice, pCreateInfo: CTypesPointer[VkPrivateDataSlotCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pPrivateDataSlot: CTypesPointer[VkPrivateDataSlot]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreatePrivateDataSlotEXT(device: VkDevice, pCreateInfo: CTypesPointer[VkPrivateDataSlotCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pPrivateDataSlot: CTypesPointer[VkPrivateDataSlot]) -> VkResult:  # Alias of vkCreatePrivateDataSlot
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyPrivateDataSlot(device: VkDevice, privateDataSlot: VkPrivateDataSlot, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyPrivateDataSlotEXT(device: VkDevice, privateDataSlot: VkPrivateDataSlot, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:  # Alias of vkDestroyPrivateDataSlot
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkSetPrivateData(device: VkDevice, objectType: VkObjectType, objectHandle: int, privateDataSlot: VkPrivateDataSlot, data: int) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkSetPrivateDataEXT(device: VkDevice, objectType: VkObjectType, objectHandle: int, privateDataSlot: VkPrivateDataSlot, data: int) -> VkResult:  # Alias of vkSetPrivateData
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetPrivateData(device: VkDevice, objectType: VkObjectType, objectHandle: int, privateDataSlot: VkPrivateDataSlot, pData: CTypesPointer[c_uint64]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetPrivateDataEXT(device: VkDevice, objectType: VkObjectType, objectHandle: int, privateDataSlot: VkPrivateDataSlot, pData: CTypesPointer[c_uint64]) -> None:  # Alias of vkGetPrivateData
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyBuffer2(commandBuffer: VkCommandBuffer, pCopyBufferInfo: CTypesPointer[VkCopyBufferInfo2]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyBuffer2KHR(commandBuffer: VkCommandBuffer, pCopyBufferInfo: CTypesPointer[VkCopyBufferInfo2]) -> None:  # Alias of vkCmdCopyBuffer2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyImage2(commandBuffer: VkCommandBuffer, pCopyImageInfo: CTypesPointer[VkCopyImageInfo2]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyImage2KHR(commandBuffer: VkCommandBuffer, pCopyImageInfo: CTypesPointer[VkCopyImageInfo2]) -> None:  # Alias of vkCmdCopyImage2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBlitImage2(commandBuffer: VkCommandBuffer, pBlitImageInfo: CTypesPointer[VkBlitImageInfo2]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBlitImage2KHR(commandBuffer: VkCommandBuffer, pBlitImageInfo: CTypesPointer[VkBlitImageInfo2]) -> None:  # Alias of vkCmdBlitImage2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyBufferToImage2(commandBuffer: VkCommandBuffer, pCopyBufferToImageInfo: CTypesPointer[VkCopyBufferToImageInfo2]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyBufferToImage2KHR(commandBuffer: VkCommandBuffer, pCopyBufferToImageInfo: CTypesPointer[VkCopyBufferToImageInfo2]) -> None:  # Alias of vkCmdCopyBufferToImage2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyImageToBuffer2(commandBuffer: VkCommandBuffer, pCopyImageToBufferInfo: CTypesPointer[VkCopyImageToBufferInfo2]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyImageToBuffer2KHR(commandBuffer: VkCommandBuffer, pCopyImageToBufferInfo: CTypesPointer[VkCopyImageToBufferInfo2]) -> None:  # Alias of vkCmdCopyImageToBuffer2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdResolveImage2(commandBuffer: VkCommandBuffer, pResolveImageInfo: CTypesPointer[VkResolveImageInfo2]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdResolveImage2KHR(commandBuffer: VkCommandBuffer, pResolveImageInfo: CTypesPointer[VkResolveImageInfo2]) -> None:  # Alias of vkCmdResolveImage2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdRefreshObjectsKHR(commandBuffer: VkCommandBuffer, pRefreshObjects: CTypesPointer[VkRefreshObjectListKHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetFragmentShadingRateKHR(commandBuffer: VkCommandBuffer, pFragmentSize: CTypesPointer[VkExtent2D], combinerOps: Array[VkFragmentShadingRateCombinerOpKHR, 2]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetFragmentShadingRateEnumNV(commandBuffer: VkCommandBuffer, shadingRate: VkFragmentShadingRateNV, combinerOps: Array[VkFragmentShadingRateCombinerOpKHR, 2]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetAccelerationStructureBuildSizesKHR(device: VkDevice, buildType: VkAccelerationStructureBuildTypeKHR, pBuildInfo: CTypesPointer[VkAccelerationStructureBuildGeometryInfoKHR], pMaxPrimitiveCounts: CTypesPointer[c_uint32] | None, pSizeInfo: CTypesPointer[VkAccelerationStructureBuildSizesInfoKHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetVertexInputEXT(commandBuffer: VkCommandBuffer, vertexBindingDescriptionCount: int, pVertexBindingDescriptions: CTypesPointer[VkVertexInputBindingDescription2EXT], vertexAttributeDescriptionCount: int, pVertexAttributeDescriptions: CTypesPointer[VkVertexInputAttributeDescription2EXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetColorWriteEnableEXT(commandBuffer: VkCommandBuffer, attachmentCount: int, pColorWriteEnables: CTypesPointer[VkBool32]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetEvent2(commandBuffer: VkCommandBuffer, event: VkEvent, pDependencyInfo: CTypesPointer[VkDependencyInfo]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetEvent2KHR(commandBuffer: VkCommandBuffer, event: VkEvent, pDependencyInfo: CTypesPointer[VkDependencyInfo]) -> None:  # Alias of vkCmdSetEvent2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdResetEvent2(commandBuffer: VkCommandBuffer, event: VkEvent, stageMask: VkPipelineStageFlags2) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdResetEvent2KHR(commandBuffer: VkCommandBuffer, event: VkEvent, stageMask: VkPipelineStageFlags2) -> None:  # Alias of vkCmdResetEvent2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdWaitEvents2(commandBuffer: VkCommandBuffer, eventCount: int, pEvents: CTypesPointer[VkEvent], pDependencyInfos: CTypesPointer[VkDependencyInfo]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdWaitEvents2KHR(commandBuffer: VkCommandBuffer, eventCount: int, pEvents: CTypesPointer[VkEvent], pDependencyInfos: CTypesPointer[VkDependencyInfo]) -> None:  # Alias of vkCmdWaitEvents2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdPipelineBarrier2(commandBuffer: VkCommandBuffer, pDependencyInfo: CTypesPointer[VkDependencyInfo]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdPipelineBarrier2KHR(commandBuffer: VkCommandBuffer, pDependencyInfo: CTypesPointer[VkDependencyInfo]) -> None:  # Alias of vkCmdPipelineBarrier2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkQueueSubmit2(queue: VkQueue, submitCount: int, pSubmits: CTypesPointer[VkSubmitInfo2], fence: VkFence) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkQueueSubmit2KHR(queue: VkQueue, submitCount: int, pSubmits: CTypesPointer[VkSubmitInfo2], fence: VkFence) -> VkResult:  # Alias of vkQueueSubmit2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdWriteTimestamp2(commandBuffer: VkCommandBuffer, stage: VkPipelineStageFlags2, queryPool: VkQueryPool, query: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdWriteTimestamp2KHR(commandBuffer: VkCommandBuffer, stage: VkPipelineStageFlags2, queryPool: VkQueryPool, query: int) -> None:  # Alias of vkCmdWriteTimestamp2
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdWriteBufferMarker2AMD(commandBuffer: VkCommandBuffer, stage: VkPipelineStageFlags2, dstBuffer: VkBuffer, dstOffset: VkDeviceSize, marker: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetQueueCheckpointData2NV(queue: VkQueue, pCheckpointDataCount: CTypesPointer[c_uint32] | None, pCheckpointData: CTypesPointer[VkCheckpointData2NV] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCopyMemoryToImageEXT(device: VkDevice, pCopyMemoryToImageInfo: CTypesPointer[VkCopyMemoryToImageInfoEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCopyImageToMemoryEXT(device: VkDevice, pCopyImageToMemoryInfo: CTypesPointer[VkCopyImageToMemoryInfoEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCopyImageToImageEXT(device: VkDevice, pCopyImageToImageInfo: CTypesPointer[VkCopyImageToImageInfoEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkTransitionImageLayoutEXT(device: VkDevice, transitionCount: int, pTransitions: CTypesPointer[VkHostImageLayoutTransitionInfoEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetCommandPoolMemoryConsumption(device: VkDevice, commandPool: VkCommandPool, commandBuffer: VkCommandBuffer, pConsumption: CTypesPointer[VkCommandPoolMemoryConsumption]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateVideoSessionKHR(device: VkDevice, pCreateInfo: CTypesPointer[VkVideoSessionCreateInfoKHR], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pVideoSession: CTypesPointer[VkVideoSessionKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyVideoSessionKHR(device: VkDevice, videoSession: VkVideoSessionKHR, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateVideoSessionParametersKHR(device: VkDevice, pCreateInfo: CTypesPointer[VkVideoSessionParametersCreateInfoKHR], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pVideoSessionParameters: CTypesPointer[VkVideoSessionParametersKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkUpdateVideoSessionParametersKHR(device: VkDevice, videoSessionParameters: VkVideoSessionParametersKHR, pUpdateInfo: CTypesPointer[VkVideoSessionParametersUpdateInfoKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetEncodedVideoSessionParametersKHR(device: VkDevice, pVideoSessionParametersInfo: CTypesPointer[VkVideoEncodeSessionParametersGetInfoKHR], pFeedbackInfo: CTypesPointer[VkVideoEncodeSessionParametersFeedbackInfoKHR] | None, pDataSize: CTypesPointer[c_size_t] | None, pData: CTypesPointer[None] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyVideoSessionParametersKHR(device: VkDevice, videoSessionParameters: VkVideoSessionParametersKHR, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetVideoSessionMemoryRequirementsKHR(device: VkDevice, videoSession: VkVideoSessionKHR, pMemoryRequirementsCount: CTypesPointer[c_uint32] | None, pMemoryRequirements: CTypesPointer[VkVideoSessionMemoryRequirementsKHR] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkBindVideoSessionMemoryKHR(device: VkDevice, videoSession: VkVideoSessionKHR, bindSessionMemoryInfoCount: int, pBindSessionMemoryInfos: CTypesPointer[VkBindVideoSessionMemoryInfoKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDecodeVideoKHR(commandBuffer: VkCommandBuffer, pDecodeInfo: CTypesPointer[VkVideoDecodeInfoKHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBeginVideoCodingKHR(commandBuffer: VkCommandBuffer, pBeginInfo: CTypesPointer[VkVideoBeginCodingInfoKHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdControlVideoCodingKHR(commandBuffer: VkCommandBuffer, pCodingControlInfo: CTypesPointer[VkVideoCodingControlInfoKHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdEndVideoCodingKHR(commandBuffer: VkCommandBuffer, pEndCodingInfo: CTypesPointer[VkVideoEndCodingInfoKHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdEncodeVideoKHR(commandBuffer: VkCommandBuffer, pEncodeInfo: CTypesPointer[VkVideoEncodeInfoKHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDecompressMemoryNV(commandBuffer: VkCommandBuffer, decompressRegionCount: int, pDecompressMemoryRegions: CTypesPointer[VkDecompressMemoryRegionNV]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDecompressMemoryIndirectCountNV(commandBuffer: VkCommandBuffer, indirectCommandsAddress: VkDeviceAddress, indirectCommandsCountAddress: VkDeviceAddress, stride: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateCuModuleNVX(device: VkDevice, pCreateInfo: CTypesPointer[VkCuModuleCreateInfoNVX], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pModule: CTypesPointer[VkCuModuleNVX]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateCuFunctionNVX(device: VkDevice, pCreateInfo: CTypesPointer[VkCuFunctionCreateInfoNVX], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pFunction: CTypesPointer[VkCuFunctionNVX]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyCuModuleNVX(device: VkDevice, module: VkCuModuleNVX, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyCuFunctionNVX(device: VkDevice, function: VkCuFunctionNVX, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCuLaunchKernelNVX(commandBuffer: VkCommandBuffer, pLaunchInfo: CTypesPointer[VkCuLaunchInfoNVX]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDescriptorSetLayoutSizeEXT(device: VkDevice, layout: VkDescriptorSetLayout, pLayoutSizeInBytes: CTypesPointer[VkDeviceSize]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDescriptorSetLayoutBindingOffsetEXT(device: VkDevice, layout: VkDescriptorSetLayout, binding: int, pOffset: CTypesPointer[VkDeviceSize]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDescriptorEXT(device: VkDevice, pDescriptorInfo: CTypesPointer[VkDescriptorGetInfoEXT], dataSize: int, pDescriptor: CTypesPointer[None]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBindDescriptorBuffersEXT(commandBuffer: VkCommandBuffer, bufferCount: int, pBindingInfos: CTypesPointer[VkDescriptorBufferBindingInfoEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDescriptorBufferOffsetsEXT(commandBuffer: VkCommandBuffer, pipelineBindPoint: VkPipelineBindPoint, layout: VkPipelineLayout, firstSet: int, setCount: int, pBufferIndices: CTypesPointer[c_uint32], pOffsets: CTypesPointer[VkDeviceSize]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBindDescriptorBufferEmbeddedSamplersEXT(commandBuffer: VkCommandBuffer, pipelineBindPoint: VkPipelineBindPoint, layout: VkPipelineLayout, set: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetBufferOpaqueCaptureDescriptorDataEXT(device: VkDevice, pInfo: CTypesPointer[VkBufferCaptureDescriptorDataInfoEXT], pData: CTypesPointer[None]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetImageOpaqueCaptureDescriptorDataEXT(device: VkDevice, pInfo: CTypesPointer[VkImageCaptureDescriptorDataInfoEXT], pData: CTypesPointer[None]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetImageViewOpaqueCaptureDescriptorDataEXT(device: VkDevice, pInfo: CTypesPointer[VkImageViewCaptureDescriptorDataInfoEXT], pData: CTypesPointer[None]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetSamplerOpaqueCaptureDescriptorDataEXT(device: VkDevice, pInfo: CTypesPointer[VkSamplerCaptureDescriptorDataInfoEXT], pData: CTypesPointer[None]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetAccelerationStructureOpaqueCaptureDescriptorDataEXT(device: VkDevice, pInfo: CTypesPointer[VkAccelerationStructureCaptureDescriptorDataInfoEXT], pData: CTypesPointer[None]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkSetDeviceMemoryPriorityEXT(device: VkDevice, memory: VkDeviceMemory, priority: float) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkWaitForPresentKHR(device: VkDevice, swapchain: VkSwapchainKHR, presentId: int, timeout: int) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateBufferCollectionFUCHSIA(device: VkDevice, pCreateInfo: CTypesPointer[VkBufferCollectionCreateInfoFUCHSIA], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pCollection: CTypesPointer[VkBufferCollectionFUCHSIA]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkSetBufferCollectionBufferConstraintsFUCHSIA(device: VkDevice, collection: VkBufferCollectionFUCHSIA, pBufferConstraintsInfo: CTypesPointer[VkBufferConstraintsInfoFUCHSIA]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkSetBufferCollectionImageConstraintsFUCHSIA(device: VkDevice, collection: VkBufferCollectionFUCHSIA, pImageConstraintsInfo: CTypesPointer[VkImageConstraintsInfoFUCHSIA]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyBufferCollectionFUCHSIA(device: VkDevice, collection: VkBufferCollectionFUCHSIA, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetBufferCollectionPropertiesFUCHSIA(device: VkDevice, collection: VkBufferCollectionFUCHSIA, pProperties: CTypesPointer[VkBufferCollectionPropertiesFUCHSIA]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateCudaModuleNV(device: VkDevice, pCreateInfo: CTypesPointer[VkCudaModuleCreateInfoNV], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pModule: CTypesPointer[VkCudaModuleNV]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetCudaModuleCacheNV(device: VkDevice, module: VkCudaModuleNV, pCacheSize: CTypesPointer[c_size_t] | None, pCacheData: CTypesPointer[None] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateCudaFunctionNV(device: VkDevice, pCreateInfo: CTypesPointer[VkCudaFunctionCreateInfoNV], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pFunction: CTypesPointer[VkCudaFunctionNV]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyCudaModuleNV(device: VkDevice, module: VkCudaModuleNV, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyCudaFunctionNV(device: VkDevice, function: VkCudaFunctionNV, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCudaLaunchKernelNV(commandBuffer: VkCommandBuffer, pLaunchInfo: CTypesPointer[VkCudaLaunchInfoNV]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBeginRendering(commandBuffer: VkCommandBuffer, pRenderingInfo: CTypesPointer[VkRenderingInfo]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBeginRenderingKHR(commandBuffer: VkCommandBuffer, pRenderingInfo: CTypesPointer[VkRenderingInfo]) -> None:  # Alias of vkCmdBeginRendering
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdEndRendering(commandBuffer: VkCommandBuffer) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdEndRenderingKHR(commandBuffer: VkCommandBuffer) -> None:  # Alias of vkCmdEndRendering
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDescriptorSetLayoutHostMappingInfoVALVE(device: VkDevice, pBindingReference: CTypesPointer[VkDescriptorSetBindingReferenceVALVE], pHostMapping: CTypesPointer[VkDescriptorSetLayoutHostMappingInfoVALVE]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDescriptorSetHostMappingVALVE(device: VkDevice, descriptorSet: VkDescriptorSet, ppData: CTypesPointer[None]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateMicromapEXT(device: VkDevice, pCreateInfo: CTypesPointer[VkMicromapCreateInfoEXT], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pMicromap: CTypesPointer[VkMicromapEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBuildMicromapsEXT(commandBuffer: VkCommandBuffer, infoCount: int, pInfos: CTypesPointer[VkMicromapBuildInfoEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkBuildMicromapsEXT(device: VkDevice, deferredOperation: VkDeferredOperationKHR, infoCount: int, pInfos: CTypesPointer[VkMicromapBuildInfoEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyMicromapEXT(device: VkDevice, micromap: VkMicromapEXT, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyMicromapEXT(commandBuffer: VkCommandBuffer, pInfo: CTypesPointer[VkCopyMicromapInfoEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCopyMicromapEXT(device: VkDevice, deferredOperation: VkDeferredOperationKHR, pInfo: CTypesPointer[VkCopyMicromapInfoEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyMicromapToMemoryEXT(commandBuffer: VkCommandBuffer, pInfo: CTypesPointer[VkCopyMicromapToMemoryInfoEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCopyMicromapToMemoryEXT(device: VkDevice, deferredOperation: VkDeferredOperationKHR, pInfo: CTypesPointer[VkCopyMicromapToMemoryInfoEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdCopyMemoryToMicromapEXT(commandBuffer: VkCommandBuffer, pInfo: CTypesPointer[VkCopyMemoryToMicromapInfoEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCopyMemoryToMicromapEXT(device: VkDevice, deferredOperation: VkDeferredOperationKHR, pInfo: CTypesPointer[VkCopyMemoryToMicromapInfoEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdWriteMicromapsPropertiesEXT(commandBuffer: VkCommandBuffer, micromapCount: int, pMicromaps: CTypesPointer[VkMicromapEXT], queryType: VkQueryType, queryPool: VkQueryPool, firstQuery: int) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkWriteMicromapsPropertiesEXT(device: VkDevice, micromapCount: int, pMicromaps: CTypesPointer[VkMicromapEXT], queryType: VkQueryType, dataSize: int, pData: CTypesPointer[None], stride: int) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceMicromapCompatibilityEXT(device: VkDevice, pVersionInfo: CTypesPointer[VkMicromapVersionInfoEXT], pCompatibility: CTypesPointer[VkAccelerationStructureCompatibilityKHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetMicromapBuildSizesEXT(device: VkDevice, buildType: VkAccelerationStructureBuildTypeKHR, pBuildInfo: CTypesPointer[VkMicromapBuildInfoEXT], pSizeInfo: CTypesPointer[VkMicromapBuildSizesInfoEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetShaderModuleIdentifierEXT(device: VkDevice, shaderModule: VkShaderModule, pIdentifier: CTypesPointer[VkShaderModuleIdentifierEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetShaderModuleCreateInfoIdentifierEXT(device: VkDevice, pCreateInfo: CTypesPointer[VkShaderModuleCreateInfo], pIdentifier: CTypesPointer[VkShaderModuleIdentifierEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetImageSubresourceLayout2KHR(device: VkDevice, image: VkImage, pSubresource: CTypesPointer[VkImageSubresource2KHR], pLayout: CTypesPointer[VkSubresourceLayout2KHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetImageSubresourceLayout2EXT(device: VkDevice, image: VkImage, pSubresource: CTypesPointer[VkImageSubresource2KHR], pLayout: CTypesPointer[VkSubresourceLayout2KHR]) -> None:  # Alias of vkGetImageSubresourceLayout2KHR
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetPipelinePropertiesEXT(device: VkDevice, pPipelineInfo: CTypesPointer[VkPipelineInfoEXT], pPipelineProperties: CTypesPointer[VkBaseOutStructure]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkExportMetalObjectsEXT(device: VkDevice, pMetalObjectsInfo: CTypesPointer[VkExportMetalObjectsInfoEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetFramebufferTilePropertiesQCOM(device: VkDevice, framebuffer: VkFramebuffer, pPropertiesCount: CTypesPointer[c_uint32] | None, pProperties: CTypesPointer[VkTilePropertiesQCOM] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDynamicRenderingTilePropertiesQCOM(device: VkDevice, pRenderingInfo: CTypesPointer[VkRenderingInfo], pProperties: CTypesPointer[VkTilePropertiesQCOM]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateOpticalFlowSessionNV(device: VkDevice, pCreateInfo: CTypesPointer[VkOpticalFlowSessionCreateInfoNV], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pSession: CTypesPointer[VkOpticalFlowSessionNV]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyOpticalFlowSessionNV(device: VkDevice, session: VkOpticalFlowSessionNV, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkBindOpticalFlowSessionImageNV(device: VkDevice, session: VkOpticalFlowSessionNV, bindingPoint: VkOpticalFlowSessionBindingPointNV, view: VkImageView, layout: VkImageLayout) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdOpticalFlowExecuteNV(commandBuffer: VkCommandBuffer, session: VkOpticalFlowSessionNV, pExecuteInfo: CTypesPointer[VkOpticalFlowExecuteInfoNV]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceFaultInfoEXT(device: VkDevice, pFaultCounts: CTypesPointer[VkDeviceFaultCountsEXT], pFaultInfo: CTypesPointer[VkDeviceFaultInfoEXT] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDepthBias2EXT(commandBuffer: VkCommandBuffer, pDepthBiasInfo: CTypesPointer[VkDepthBiasInfoEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkReleaseSwapchainImagesEXT(device: VkDevice, pReleaseInfo: CTypesPointer[VkReleaseSwapchainImagesInfoEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetDeviceImageSubresourceLayoutKHR(device: VkDevice, pInfo: CTypesPointer[VkDeviceImageSubresourceInfoKHR], pLayout: CTypesPointer[VkSubresourceLayout2KHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkMapMemory2KHR(device: VkDevice, pMemoryMapInfo: CTypesPointer[VkMemoryMapInfoKHR], ppData: CTypesPointer[None] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkUnmapMemory2KHR(device: VkDevice, pMemoryUnmapInfo: CTypesPointer[VkMemoryUnmapInfoKHR]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateShadersEXT(device: VkDevice, createInfoCount: int, pCreateInfos: CTypesPointer[VkShaderCreateInfoEXT], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pShaders: CTypesPointer[VkShaderEXT]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkDestroyShaderEXT(device: VkDevice, shader: VkShaderEXT, pAllocator: CTypesPointer[VkAllocationCallbacks] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetShaderBinaryDataEXT(device: VkDevice, shader: VkShaderEXT, pDataSize: CTypesPointer[c_size_t] | None, pData: CTypesPointer[None] | None) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBindShadersEXT(commandBuffer: VkCommandBuffer, stageCount: int, pStages: CTypesPointer[VkShaderStageFlagBits], pShaders: CTypesPointer[VkShaderEXT] | None) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetScreenBufferPropertiesQNX(device: VkDevice, buffer: CTypesPointer[_screen_buffer], pProperties: CTypesPointer[VkScreenBufferPropertiesQNX]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetExecutionGraphPipelineScratchSizeAMDX(device: VkDevice, executionGraph: VkPipeline, pSizeInfo: CTypesPointer[VkExecutionGraphPipelineScratchSizeAMDX]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetExecutionGraphPipelineNodeIndexAMDX(device: VkDevice, executionGraph: VkPipeline, pNodeInfo: CTypesPointer[VkPipelineShaderStageNodeCreateInfoAMDX], pNodeIndex: CTypesPointer[c_uint32]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCreateExecutionGraphPipelinesAMDX(device: VkDevice, pipelineCache: VkPipelineCache, createInfoCount: int, pCreateInfos: CTypesPointer[VkExecutionGraphPipelineCreateInfoAMDX], pAllocator: CTypesPointer[VkAllocationCallbacks] | None, pPipelines: CTypesPointer[VkPipeline]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdInitializeGraphScratchMemoryAMDX(commandBuffer: VkCommandBuffer, executionGraph: VkPipeline, scratch: VkDeviceAddress, scratchSize: VkDeviceSize) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDispatchGraphAMDX(commandBuffer: VkCommandBuffer, scratch: VkDeviceAddress, scratchSize: VkDeviceSize, pCountInfo: CTypesPointer[VkDispatchGraphCountInfoAMDX]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDispatchGraphIndirectAMDX(commandBuffer: VkCommandBuffer, scratch: VkDeviceAddress, scratchSize: VkDeviceSize, pCountInfo: CTypesPointer[VkDispatchGraphCountInfoAMDX]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdDispatchGraphIndirectCountAMDX(commandBuffer: VkCommandBuffer, scratch: VkDeviceAddress, scratchSize: VkDeviceSize, countInfo: VkDeviceAddress) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBindDescriptorSets2KHR(commandBuffer: VkCommandBuffer, pBindDescriptorSetsInfo: CTypesPointer[VkBindDescriptorSetsInfoKHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdPushConstants2KHR(commandBuffer: VkCommandBuffer, pPushConstantsInfo: CTypesPointer[VkPushConstantsInfoKHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdPushDescriptorSet2KHR(commandBuffer: VkCommandBuffer, pPushDescriptorSetInfo: CTypesPointer[VkPushDescriptorSetInfoKHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdPushDescriptorSetWithTemplate2KHR(commandBuffer: VkCommandBuffer, pPushDescriptorSetWithTemplateInfo: CTypesPointer[VkPushDescriptorSetWithTemplateInfoKHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDescriptorBufferOffsets2EXT(commandBuffer: VkCommandBuffer, pSetDescriptorBufferOffsetsInfo: CTypesPointer[VkSetDescriptorBufferOffsetsInfoEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdBindDescriptorBufferEmbeddedSamplers2EXT(commandBuffer: VkCommandBuffer, pBindDescriptorBufferEmbeddedSamplersInfo: CTypesPointer[VkBindDescriptorBufferEmbeddedSamplersInfoEXT]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkSetLatencySleepModeNV(device: VkDevice, swapchain: VkSwapchainKHR, pSleepModeInfo: CTypesPointer[VkLatencySleepModeInfoNV]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkLatencySleepNV(device: VkDevice, swapchain: VkSwapchainKHR, pSleepInfo: CTypesPointer[VkLatencySleepInfoNV]) -> VkResult:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkSetLatencyMarkerNV(device: VkDevice, swapchain: VkSwapchainKHR, pLatencyMarkerInfo: CTypesPointer[VkSetLatencyMarkerInfoNV]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkGetLatencyTimingsNV(device: VkDevice, swapchain: VkSwapchainKHR, pLatencyMarkerInfo: CTypesPointer[VkGetLatencyMarkerInfoNV]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkQueueNotifyOutOfBandNV(queue: VkQueue, pQueueTypeInfo: CTypesPointer[VkOutOfBandQueueTypeInfoNV]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetRenderingAttachmentLocationsKHR(commandBuffer: VkCommandBuffer, pLocationInfo: CTypesPointer[VkRenderingAttachmentLocationInfoKHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetRenderingInputAttachmentIndicesKHR(commandBuffer: VkCommandBuffer, pInputAttachmentIndexInfo: CTypesPointer[VkRenderingInputAttachmentIndexInfoKHR]) -> None:
        raise VulkanNoLogicalDevice

    @staticmethod
    def vkCmdSetDepthClampRangeEXT(commandBuffer: VkCommandBuffer, depthClampMode: VkDepthClampModeEXT, pDepthClampRange: CTypesPointer[VkDepthClampRangeEXT] | None) -> None:
        raise VulkanNoLogicalDevice
