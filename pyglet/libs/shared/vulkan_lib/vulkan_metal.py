from __future__ import annotations

from ctypes import c_void_p, POINTER, CFUNCTYPE, c_int32

from . import define_struct
from .vulkan_core import VkFlags, VkStructureType, VkResult, VkInstance, VkAllocationCallbacks, VkSurfaceKHR, VkQueue, \
    VkDeviceMemory, VkImage, VkImageView, VkBufferView, VkImageAspectFlagBits, VkSemaphore, VkEvent, VkDevice

CAMetalLayer = c_void_p

MTLDevice_id = c_void_p        # Metal Device
MTLCommandQueue_id = c_void_p  # Metal Command Queue
MTLBuffer_id = c_void_p        # Metal Buffer
MTLTexture_id = c_void_p       # Metal Texture
MTLSharedEvent_id = c_void_p   # Metal Shared Event
IOSurfaceRef = c_void_p

VULKAN_METAL_H_: int = 1

VK_EXT_METAL_SURFACE_SPEC_VERSION: int = 1
VK_EXT_METAL_SURFACE_EXTENSION_NAME: str = "VK_EXT_metal_surface"
VkMetalSurfaceCreateFlagsEXT: type[VkFlags] = VkFlags
VkMetalSurfaceCreateInfoEXT = define_struct('VkMetalSurfaceCreateInfoEXT',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('flags', VkMetalSurfaceCreateFlagsEXT),
    ('pLayer', c_void_p),  # POINTER(CAMetalLayer)
)

PFN_vkCreateMetalSurfaceEXT = CFUNCTYPE(VkResult, VkInstance, POINTER(VkMetalSurfaceCreateInfoEXT), POINTER(VkAllocationCallbacks), POINTER(VkSurfaceKHR))

VK_EXT_METAL_OBJECTS_SPEC_VERSION: int = 2
VK_EXT_METAL_OBJECTS_EXTENSION_NAME: str = "VK_EXT_metal_objects"

VkExportMetalObjectTypeFlagBitsEXT = c_int32
VK_EXPORT_METAL_OBJECT_TYPE_METAL_DEVICE_BIT_EXT: int = 0x00000001
VK_EXPORT_METAL_OBJECT_TYPE_METAL_COMMAND_QUEUE_BIT_EXT: int = 0x00000002
VK_EXPORT_METAL_OBJECT_TYPE_METAL_BUFFER_BIT_EXT: int = 0x00000004
VK_EXPORT_METAL_OBJECT_TYPE_METAL_TEXTURE_BIT_EXT: int = 0x00000008
VK_EXPORT_METAL_OBJECT_TYPE_METAL_IOSURFACE_BIT_EXT: int = 0x00000010
VK_EXPORT_METAL_OBJECT_TYPE_METAL_SHARED_EVENT_BIT_EXT: int = 0x00000020
VK_EXPORT_METAL_OBJECT_TYPE_FLAG_BITS_MAX_ENUM_EXT: int = 0x7FFFFFFF
VkExportMetalObjectTypeFlagsEXT: type[VkFlags] = VkFlags
VkExportMetalObjectCreateInfoEXT = define_struct('VkExportMetalObjectCreateInfoEXT',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('exportObjectType', VkExportMetalObjectTypeFlagBitsEXT),
)

VkExportMetalObjectsInfoEXT = define_struct('VkExportMetalObjectsInfoEXT',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
)

VkExportMetalDeviceInfoEXT = define_struct('VkExportMetalDeviceInfoEXT',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('mtlDevice', MTLDevice_id),
)

VkExportMetalCommandQueueInfoEXT = define_struct('VkExportMetalCommandQueueInfoEXT',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('queue', VkQueue),
    ('mtlCommandQueue', MTLCommandQueue_id),
)

VkExportMetalBufferInfoEXT = define_struct('VkExportMetalBufferInfoEXT',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('memory', VkDeviceMemory),
    ('mtlBuffer', MTLBuffer_id),
)

VkImportMetalBufferInfoEXT = define_struct('VkImportMetalBufferInfoEXT',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('mtlBuffer', MTLBuffer_id),
)

VkExportMetalTextureInfoEXT = define_struct('VkExportMetalTextureInfoEXT',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('image', VkImage),
    ('imageView', VkImageView),
    ('bufferView', VkBufferView),
    ('plane', VkImageAspectFlagBits),
    ('mtlTexture', MTLTexture_id),
)

VkImportMetalTextureInfoEXT = define_struct('VkImportMetalTextureInfoEXT',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('plane', VkImageAspectFlagBits),
    ('mtlTexture', MTLTexture_id),
)

VkExportMetalIOSurfaceInfoEXT = define_struct('VkExportMetalIOSurfaceInfoEXT',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('image', VkImage),
    ('ioSurface', IOSurfaceRef),
)

VkImportMetalIOSurfaceInfoEXT = define_struct('VkImportMetalIOSurfaceInfoEXT',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('ioSurface', IOSurfaceRef),
)

VkExportMetalSharedEventInfoEXT = define_struct('VkExportMetalSharedEventInfoEXT',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('semaphore', VkSemaphore),
    ('event', VkEvent),
    ('mtlSharedEvent', MTLSharedEvent_id),
)

VkImportMetalSharedEventInfoEXT = define_struct('VkImportMetalSharedEventInfoEXT',
    ('sType', VkStructureType),
    ('pNext', c_void_p),
    ('mtlSharedEvent', MTLSharedEvent_id),
)

PFN_vkExportMetalObjectsEXT = CFUNCTYPE(None, VkDevice, POINTER(VkExportMetalObjectsInfoEXT))
InstanceFunctions = (
  ("vkCreateMetalSurfaceEXT", PFN_vkCreateMetalSurfaceEXT),
)

DeviceFunctions = (
  ("vkExportMetalObjectsEXT", PFN_vkExportMetalObjectsEXT),
)

LoaderFunctions = (
)

