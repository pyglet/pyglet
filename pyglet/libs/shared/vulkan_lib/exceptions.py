from pyglet.libs.shared.vulkan_lib.vulkan_core import VK_NOT_READY, VK_TIMEOUT, VK_EVENT_SET, VK_EVENT_RESET, VK_INCOMPLETE, \
    VK_ERROR_OUT_OF_HOST_MEMORY, VK_ERROR_OUT_OF_DEVICE_MEMORY, VK_ERROR_INITIALIZATION_FAILED, VK_ERROR_DEVICE_LOST, \
    VK_ERROR_MEMORY_MAP_FAILED, VK_ERROR_LAYER_NOT_PRESENT, VK_ERROR_EXTENSION_NOT_PRESENT, \
    VK_ERROR_FEATURE_NOT_PRESENT, VK_ERROR_INCOMPATIBLE_DRIVER, VK_ERROR_TOO_MANY_OBJECTS, \
    VK_ERROR_FORMAT_NOT_SUPPORTED, VK_ERROR_FRAGMENTED_POOL, VK_ERROR_SURFACE_LOST_KHR, \
    VK_ERROR_NATIVE_WINDOW_IN_USE_KHR, VK_ERROR_OUT_OF_DATE_KHR, VK_ERROR_INCOMPATIBLE_DISPLAY_KHR, \
    VK_ERROR_INVALID_SHADER_NV, VK_ERROR_OUT_OF_POOL_MEMORY, VK_ERROR_INVALID_EXTERNAL_HANDLE, VK_ERROR_FRAGMENTATION, \
    VK_ERROR_INVALID_DEVICE_ADDRESS_EXT, VK_ERROR_INVALID_OPAQUE_CAPTURE_ADDRESS, \
    VK_ERROR_FULL_SCREEN_EXCLUSIVE_MODE_LOST_EXT, VK_ERROR_VALIDATION_FAILED_EXT, VK_ERROR_COMPRESSION_EXHAUSTED_EXT, \
    VK_ERROR_IMAGE_USAGE_NOT_SUPPORTED_KHR, VK_ERROR_VIDEO_PICTURE_LAYOUT_NOT_SUPPORTED_KHR, \
    VK_ERROR_VIDEO_PROFILE_OPERATION_NOT_SUPPORTED_KHR, VK_ERROR_VIDEO_PROFILE_FORMAT_NOT_SUPPORTED_KHR, \
    VK_ERROR_VIDEO_PROFILE_CODEC_NOT_SUPPORTED_KHR, VK_ERROR_VIDEO_STD_VERSION_NOT_SUPPORTED_KHR, \
    VK_ERROR_INVALID_VIDEO_STD_PARAMETERS_KHR, VK_ERROR_NOT_PERMITTED_KHR, VK_ERROR_NOT_ENOUGH_SPACE_KHR, \
    VK_ERROR_UNKNOWN


class VulkanException(Exception):
    """Base exception for all Vulkan errors."""
    default_message = "An unknown Vulkan error has occurred.\nAn unknown exception type, invalid use of arguments such as pointers, or memory corruption. {}"

    def __init__(self, *args):
        if args:
            self.message = self.default_message.format(*args)
        else:
            self.message = self.default_message
        super().__init__(self.message)


class VulkanNoInstance(VulkanException):
    default_message = "A Vulkan instance has not yet been created. Create one before using this."


class VulkanNoLogicalDevice(VulkanException):
    default_message = "A logical device has not yet been created. Create one before using this."


class VulkanNotReadyException(VulkanException):
    default_message = "A fence or query has not yet completed."


class VulkanTimeoutException(VulkanException):
    default_message = "A wait operation has not completed in the specified time."


class VulkanEventSetException(VulkanException):
    default_message = "An event is signaled."


class VulkanEventResetException(VulkanException):
    default_message = "An event is unsignaled."


class VulkanIncompleteException(VulkanException):
    default_message = "A return array was too small for the result."


class VulkanOutOfHostMemoryException(VulkanException):
    default_message = "A host memory allocation has failed."


class VulkanOutOfDeviceMemoryException(VulkanException):
    default_message = "A device memory allocation has failed."


class VulkanInitializationFailedException(VulkanException):
    default_message = "Initialization of an object could not be completed for implementation-specific reasons."


class VulkanDeviceLostException(VulkanException):
    default_message = "The logical or physical device has been lost.\nSee: https://registry.khronos.org/vulkan/specs/1.3-extensions/html/vkspec.html#devsandqueues-lost-device"


class VulkanMemoryMapFailedException(VulkanException):
    default_message = "Mapping of a memory object has failed."


class VulkanLayerNotPresentException(VulkanException):
    default_message = "A requested layer is not present or could not be loaded."


class VulkanExtensionNotPresentException(VulkanException):
    default_message = "A requested extension is not supported."


class VulkanFeatureNotPresentException(VulkanException):
    default_message = "A requested feature is not supported."


class VulkanIncompatibleDriverException(VulkanException):
    default_message = "The requested version of Vulkan is not supported by the driver or is otherwise incompatible for implementation-specific reasons."


class VulkanTooManyObjectsException(VulkanException):
    default_message = "Too many objects of the type have already been created."


class VulkanFormatNotSupportedException(VulkanException):
    default_message = "A requested format is not supported on this device."


class VulkanFragmentedPoolException(VulkanException):
    default_message = (
        "A pool allocation has failed due to fragmentation of the pool’s memory. "
        "This must only be returned if no attempt to allocate host or device memory was made to accommodate the new allocation. "
        "This should be returned in preference to VK_ERROR_OUT_OF_POOL_MEMORY, but only if the implementation is certain "
        "that the pool allocation failure was due to fragmentation."
    )


class VulkanSurfaceLostKHRException(VulkanException):
    default_message = "A surface is no longer available."


class VulkanNativeWindowInUseKHRException(VulkanException):
    default_message = "The requested window is already in use by Vulkan or another API in a manner which prevents it from being used again."


class VulkanOutOfDateKHRException(VulkanException):
    default_message = (
        "A surface has changed in such a way that it is no longer compatible with the swapchain, "
        "and further presentation requests using the swapchain will fail. Applications must query the new surface properties "
        "and recreate their swapchain if they wish to continue presenting to the surface."
    )


class VulkanIncompatibleDisplayKHRException(VulkanException):
    default_message = "The display used by a swapchain does not use the same presentable image layout, or is incompatible in a way that prevents sharing an image."


class VulkanInvalidShaderNVException(VulkanException):
    default_message = "One or more shaders failed to compile or link. More details are reported back to the application via VK_EXT_debug_report if enabled."


class VulkanOutOfPoolMemoryException(VulkanException):
    default_message = (
        "A pool memory allocation has failed. This must only be returned if no attempt to allocate host or device memory was made to accommodate the new allocation. "
        "If the failure was definitely due to fragmentation of the pool, VK_ERROR_FRAGMENTED_POOL should be returned instead."
    )


class VulkanInvalidExternalHandleException(VulkanException):
    default_message = "An external handle is not a valid handle of the specified type."


class VulkanFragmentationException(VulkanException):
    default_message = "A descriptor pool creation has failed due to fragmentation."


class VulkanInvalidDeviceAddressException(VulkanException):
    default_message = "A buffer creation failed because the requested address is not available."


class VulkanInvalidOpaqueCaptureAddressException(VulkanException):
    default_message = (
        "A buffer creation or memory allocation failed because the requested address is not available. "
        "A shader group handle assignment failed because the requested shader group handle information is no longer valid."
    )


class VulkanFullScreenExclusiveModeLostEXTException(VulkanException):
    default_message = (
        "An operation on a swapchain created with VK_FULL_SCREEN_EXCLUSIVE_APPLICATION_CONTROLLED_EXT failed "
        "as it did not have exclusive full-screen access. This may occur due to implementation-dependent reasons, outside of the application’s control."
    )


class VulkanValidationFailedEXTException(VulkanException):
    default_message = "A command failed because invalid usage was detected by the implementation or a validation-layer."


class VulkanCompressionExhaustedEXTException(VulkanException):
    default_message = (
        "An image creation failed because internal resources required for compression are exhausted. "
        "This must only be returned when fixed-rate compression is requested."
    )


class VulkanImageUsageNotSupportedKHRException(VulkanException):
    default_message = "The requested VkImageUsageFlags are not supported."


class VulkanVideoPictureLayoutNotSupportedKHRException(VulkanException):
    default_message = "The requested video picture layout is not supported."


class VulkanVideoProfileOperationNotSupportedKHRException(VulkanException):
    default_message = "A video profile operation specified via VkVideoProfileInfoKHR::videoCodecOperation is not supported."


class VulkanVideoProfileFormatNotSupportedKHRException(VulkanException):
    default_message = "Format parameters in a requested VkVideoProfileInfoKHR chain are not supported."


class VulkanVideoProfileCodecNotSupportedKHRException(VulkanException):
    default_message = "Codec-specific parameters in a requested VkVideoProfileInfoKHR chain are not supported."


class VulkanVideoStdVersionNotSupportedKHRException(VulkanException):
    default_message = "The specified video Std header version is not supported."


class VulkanInvalidVideoStdParametersKHRException(VulkanException):
    default_message = (
        "The specified Video Std parameters do not adhere to the syntactic or semantic requirements of the used video compression standard, "
        "or values derived from parameters according to the rules defined by the used video compression standard do not adhere to the capabilities "
        "of the video compression standard or the implementation."
    )


class VulkanNotPermittedKHRException(VulkanException):
    default_message = (
        "The driver implementation has denied a request to acquire a priority above the default priority (VK_QUEUE_GLOBAL_PRIORITY_MEDIUM_EXT) "
        "because the application does not have sufficient privileges."
    )


class VulkanNotEnoughSpaceKHRException(VulkanException):
    default_message = "The application did not provide enough space to return all the required data."


class VulkanUnknownException(VulkanException):
    default_message = (
        "An unknown error has occurred; either the application has provided invalid input, or an implementation failure has occurred."
    )

VULKAN_EXCEPTIONS = {
    # General Errors
    VK_NOT_READY: VulkanNotReadyException,
    VK_TIMEOUT: VulkanTimeoutException,
    VK_EVENT_SET: VulkanEventSetException,
    VK_EVENT_RESET: VulkanEventResetException,
    VK_INCOMPLETE: VulkanIncompleteException,
    VK_ERROR_OUT_OF_HOST_MEMORY: VulkanOutOfHostMemoryException,
    VK_ERROR_OUT_OF_DEVICE_MEMORY: VulkanOutOfDeviceMemoryException,
    VK_ERROR_INITIALIZATION_FAILED: VulkanInitializationFailedException,
    VK_ERROR_DEVICE_LOST: VulkanDeviceLostException,
    VK_ERROR_MEMORY_MAP_FAILED: VulkanMemoryMapFailedException,
    VK_ERROR_LAYER_NOT_PRESENT: VulkanLayerNotPresentException,
    VK_ERROR_EXTENSION_NOT_PRESENT: VulkanExtensionNotPresentException,
    VK_ERROR_FEATURE_NOT_PRESENT: VulkanFeatureNotPresentException,
    VK_ERROR_INCOMPATIBLE_DRIVER: VulkanIncompatibleDriverException,
    VK_ERROR_TOO_MANY_OBJECTS: VulkanTooManyObjectsException,
    VK_ERROR_FORMAT_NOT_SUPPORTED: VulkanFormatNotSupportedException,
    VK_ERROR_FRAGMENTED_POOL: VulkanFragmentedPoolException,
    VK_ERROR_SURFACE_LOST_KHR: VulkanSurfaceLostKHRException,
    VK_ERROR_NATIVE_WINDOW_IN_USE_KHR: VulkanNativeWindowInUseKHRException,
    VK_ERROR_OUT_OF_DATE_KHR: VulkanOutOfDateKHRException,
    VK_ERROR_INCOMPATIBLE_DISPLAY_KHR: VulkanIncompatibleDisplayKHRException,
    VK_ERROR_INVALID_SHADER_NV: VulkanInvalidShaderNVException,
    VK_ERROR_OUT_OF_POOL_MEMORY: VulkanOutOfPoolMemoryException,
    VK_ERROR_INVALID_EXTERNAL_HANDLE: VulkanInvalidExternalHandleException,
    VK_ERROR_FRAGMENTATION: VulkanFragmentationException,
    VK_ERROR_INVALID_DEVICE_ADDRESS_EXT: VulkanInvalidDeviceAddressException,
    VK_ERROR_INVALID_OPAQUE_CAPTURE_ADDRESS: VulkanInvalidOpaqueCaptureAddressException,
    VK_ERROR_FULL_SCREEN_EXCLUSIVE_MODE_LOST_EXT: VulkanFullScreenExclusiveModeLostEXTException,
    VK_ERROR_VALIDATION_FAILED_EXT: VulkanValidationFailedEXTException,
    VK_ERROR_COMPRESSION_EXHAUSTED_EXT: VulkanCompressionExhaustedEXTException,
    VK_ERROR_IMAGE_USAGE_NOT_SUPPORTED_KHR: VulkanImageUsageNotSupportedKHRException,
    VK_ERROR_VIDEO_PICTURE_LAYOUT_NOT_SUPPORTED_KHR: VulkanVideoPictureLayoutNotSupportedKHRException,
    VK_ERROR_VIDEO_PROFILE_OPERATION_NOT_SUPPORTED_KHR: VulkanVideoProfileOperationNotSupportedKHRException,
    VK_ERROR_VIDEO_PROFILE_FORMAT_NOT_SUPPORTED_KHR: VulkanVideoProfileFormatNotSupportedKHRException,
    VK_ERROR_VIDEO_PROFILE_CODEC_NOT_SUPPORTED_KHR: VulkanVideoProfileCodecNotSupportedKHRException,
    VK_ERROR_VIDEO_STD_VERSION_NOT_SUPPORTED_KHR: VulkanVideoStdVersionNotSupportedKHRException,
    VK_ERROR_INVALID_VIDEO_STD_PARAMETERS_KHR: VulkanInvalidVideoStdParametersKHRException,
    VK_ERROR_NOT_PERMITTED_KHR: VulkanNotPermittedKHRException,
    VK_ERROR_NOT_ENOUGH_SPACE_KHR: VulkanNotEnoughSpaceKHRException,
    VK_ERROR_UNKNOWN: VulkanUnknownException,
}

def get(error: int) -> VulkanException:
    return VULKAN_EXCEPTIONS.get(error, VulkanException)
