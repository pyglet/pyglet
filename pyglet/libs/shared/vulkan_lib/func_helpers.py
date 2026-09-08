from __future__ import annotations

import ctypes
from ctypes import c_uint32, byref
from typing import TYPE_CHECKING

from pyglet.libs.shared.vulkan_lib import InstanceFunc, DeviceFunc
from pyglet.libs.shared.vulkan_lib import exceptions
from pyglet.libs.shared.vulkan_lib.vulkan_core import VK_SUCCESS, VkExtensionProperties, \
    vkEnumerateInstanceLayerProperties, VkLayerProperties, \
    VkDevice, VkInstance, VkInstanceCreateInfo, vkCreateInstance, VkPhysicalDevice, VkDeviceCreateInfo, \
    VkAllocationCallbacks, VkQueueFamilyProperties, VkSurfaceKHR, VkSurfaceCapabilitiesKHR, \
    VkSurfaceFormatKHR, VkPresentModeKHR, VkSwapchainKHR, VkImage, VkBool32

if TYPE_CHECKING:
    from pyglet.graphics.api.vulkan.instance import VulkanInstance
    from pyglet.libs.shared.vulkan_lib.func import CTypesPointer


def CreateInstance(pCreateInfo: VkInstanceCreateInfo, pAllocator: CTypesPointer[VkAllocationCallbacks] | None = None) -> VkInstance:
    pInstance = VkInstance()
    if result := vkCreateInstance(pCreateInfo, pAllocator, byref(pInstance)) != VK_SUCCESS:
        raise exceptions.get(result)

    return pInstance

def CreateDevice(physicalDevice: VkPhysicalDevice, pCreateInfo: CTypesPointer[VkDeviceCreateInfo], pAllocator: CTypesPointer[VkAllocationCallbacks] | None = None) -> VkDevice:
    pDevice = VkDevice()
    result = InstanceFunc.vkCreateDevice(physicalDevice, byref(pCreateInfo), pAllocator, byref(pDevice))

    if result != VK_SUCCESS:
        raise Exception(result)

    return pDevice

def EnumeratePhysicalDevices(instance: VulkanInstance) -> list[VkPhysicalDevice]:
    pPhysicalDeviceCount = c_uint32()
    result = instance.vkEnumeratePhysicalDevices(instance.vk_instance, byref(pPhysicalDeviceCount), None)
    if result != VK_SUCCESS:
        raise Exception(result)

    pPhysicalDevices = (VkPhysicalDevice * pPhysicalDeviceCount.value)()
    result = instance.vkEnumeratePhysicalDevices(instance.vk_instance, byref(pPhysicalDeviceCount), pPhysicalDevices)
    if result != VK_SUCCESS:
        raise Exception(result)

    return list(pPhysicalDevices)

def EnumerateInstanceLayerProperties() -> list[VkLayerProperties]:
    pPropertyCount = c_uint32()
    print(vkEnumerateInstanceLayerProperties)
    vkEnumerateInstanceLayerProperties(byref(pPropertyCount), None)

    pProperties = (VkLayerProperties * pPropertyCount.value)()
    vkEnumerateInstanceLayerProperties(byref(pPropertyCount), pProperties)

    return pProperties[:]

def EnumerateDeviceExtensionProperties(instance: VulkanInstance, physicalDevice: VkPhysicalDevice, pLayerName: bytes | None) -> list[VkExtensionProperties]:
    pPropertyCount = c_uint32()
    result = instance.vkEnumerateDeviceExtensionProperties(physicalDevice, pLayerName, byref(pPropertyCount), None)
    if result != VK_SUCCESS:
        raise Exception(result)

    pProperties = (VkExtensionProperties * pPropertyCount.value)()
    result = instance.vkEnumerateDeviceExtensionProperties(physicalDevice, pLayerName, byref(pPropertyCount), pProperties)
    if result != VK_SUCCESS:
        raise Exception(result)

    return list(pProperties)

def GetPhysicalDeviceQueueFamilyProperties(physicalDevice: VkPhysicalDevice) -> list[VkQueueFamilyProperties]:
    pQueueFamilyPropertyCount = c_uint32()
    InstanceFunc.vkGetPhysicalDeviceQueueFamilyProperties(physicalDevice, byref(pQueueFamilyPropertyCount), None)

    pQueueFamilyProperties = (VkQueueFamilyProperties * pQueueFamilyPropertyCount.value)()
    InstanceFunc.vkGetPhysicalDeviceQueueFamilyProperties(physicalDevice, byref(pQueueFamilyPropertyCount), pQueueFamilyProperties)

    print(list(pQueueFamilyProperties))
    return list(pQueueFamilyProperties)

def GetPhysicalDeviceSurfaceCapabilitiesKHR(physicalDevice: VkPhysicalDevice, surface: VkSurfaceKHR) -> VkSurfaceCapabilitiesKHR:
    pSurfaceCapabilities = VkSurfaceCapabilitiesKHR()
    if result := InstanceFunc.vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physicalDevice, surface, byref(pSurfaceCapabilities)) != VK_SUCCESS:
        raise Exception(result)

    return pSurfaceCapabilities

def GetPhysicalDeviceSurfaceFormatsKHR(physicalDevice: VkPhysicalDevice, surface: VkSurfaceKHR | None) -> list[VkSurfaceFormatKHR]:
    pSurfaceFormatCount = c_uint32()
    print("ONE?", pSurfaceFormatCount)
    result = InstanceFunc.vkGetPhysicalDeviceSurfaceFormatsKHR(physicalDevice, surface, byref(pSurfaceFormatCount), None)
    if result != VK_SUCCESS:
        raise Exception(result)

    print("TWO?", pSurfaceFormatCount)

    pSurfaceFormats = (VkSurfaceFormatKHR * pSurfaceFormatCount.value)()
    if result := InstanceFunc.vkGetPhysicalDeviceSurfaceFormatsKHR(physicalDevice, surface, byref(pSurfaceFormatCount), pSurfaceFormats) != VK_SUCCESS:
        raise Exception(result)

    return list(pSurfaceFormats)

def GetPhysicalDeviceSurfacePresentModesKHR(physicalDevice: VkPhysicalDevice, surface: VkSurfaceKHR | None) -> list[VkPresentModeKHR]:
    print("YO?")
    pPresentModeCount = c_uint32()
    result = InstanceFunc.vkGetPhysicalDeviceSurfacePresentModesKHR(physicalDevice, surface, byref(pPresentModeCount), None)
    if result != VK_SUCCESS:
        raise Exception(result)

    print("PRESENT MODES?", pPresentModeCount)

    pPresentModes = (VkPresentModeKHR * pPresentModeCount.value)()
    result = InstanceFunc.vkGetPhysicalDeviceSurfacePresentModesKHR(physicalDevice, surface, byref(pPresentModeCount), pPresentModes)
    if result != VK_SUCCESS:
        raise Exception(result)

    return list(pPresentModes)

def GetSwapchainImagesKHR(device: VkDevice, swapchain: VkSwapchainKHR) -> list[VkImage]:
    pSwapchainImageCount = c_uint32()
    result = DeviceFunc.vkGetSwapchainImagesKHR(device, swapchain, byref(pSwapchainImageCount), None)
    if result != VK_SUCCESS:
        raise Exception(result)

    pSwapchainImages = (VkImage * pSwapchainImageCount.value)()
    result = DeviceFunc.vkGetSwapchainImagesKHR(device, swapchain, byref(pSwapchainImageCount), pSwapchainImages)
    if result != VK_SUCCESS:
        raise Exception(result)

    return list(pSwapchainImages)

def GetPhysicalDeviceSurfaceSupportKHR(physicalDevice: VkPhysicalDevice, queueFamilyIndex: int, surface: VkSurfaceKHR) -> bool:
    pSupported = VkBool32()
    if result := InstanceFunc.vkGetPhysicalDeviceSurfaceSupportKHR(physicalDevice, queueFamilyIndex, surface, byref(pSupported)) != VK_SUCCESS:
        raise exceptions.get(result)

    return bool(pSupported.value)