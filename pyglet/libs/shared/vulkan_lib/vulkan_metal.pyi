from pyglet.libs.shared.vulkan_lib.vulkan_core import VkFlags, VkInstance, VkAllocationCallbacks, VkSurfaceKHR, \
    VkStructureType, VkResult, VkDevice, VkQueue, VkDeviceMemory, VkImageView, VkImage, VkBufferView, \
    VkImageAspectFlagBits, VkSemaphore, VkEvent
from ctypes import c_void_p, POINTER, Structure

CAMetalLayer: c_void_p
MTLDevice_id: c_void_p        # Metal Device
MTLCommandQueue_id: c_void_p  # Metal Command Queue
MTLBuffer_id: c_void_p        # Metal Buffer
MTLTexture_id: c_void_p       # Metal Texture
MTLSharedEvent_id: c_void_p   # Metal Shared Event
IOSurfaceRef: c_void_p

VULKAN_METAL_H_: int = 1
VK_EXT_METAL_SURFACE_SPEC_VERSION: int = 1
VK_EXT_METAL_SURFACE_EXTENSION_NAME: str = "VK_EXT_metal_surface"
VkMetalSurfaceCreateFlagsEXT: VkFlags
def vkCreateMetalSurfaceEXT(instance: VkInstance, pCreateInfo: POINTER(VkMetalSurfaceCreateInfoEXT), pAllocator: POINTER(VkAllocationCallbacks), pSurface: POINTER(VkSurfaceKHR)) -> VkResult:
    ...

VK_EXT_METAL_OBJECTS_SPEC_VERSION: int = 2
VK_EXT_METAL_OBJECTS_EXTENSION_NAME: str = "VK_EXT_metal_objects"

VkExportMetalObjectTypeFlagBitsEXT: int
VK_EXPORT_METAL_OBJECT_TYPE_METAL_DEVICE_BIT_EXT: int = 0x00000001
VK_EXPORT_METAL_OBJECT_TYPE_METAL_COMMAND_QUEUE_BIT_EXT: int = 0x00000002
VK_EXPORT_METAL_OBJECT_TYPE_METAL_BUFFER_BIT_EXT: int = 0x00000004
VK_EXPORT_METAL_OBJECT_TYPE_METAL_TEXTURE_BIT_EXT: int = 0x00000008
VK_EXPORT_METAL_OBJECT_TYPE_METAL_IOSURFACE_BIT_EXT: int = 0x00000010
VK_EXPORT_METAL_OBJECT_TYPE_METAL_SHARED_EVENT_BIT_EXT: int = 0x00000020
VK_EXPORT_METAL_OBJECT_TYPE_FLAG_BITS_MAX_ENUM_EXT: int = 0x7FFFFFFF
VkExportMetalObjectTypeFlagsEXT: VkFlags
def vkExportMetalObjectsEXT(device: VkDevice, pMetalObjectsInfo: POINTER(VkExportMetalObjectsInfoEXT)) -> None:
    ...

class VkMetalSurfaceCreateInfoEXT(Structure):
    sType: VkStructureType
    pNext: c_void_p
    flags: VkMetalSurfaceCreateFlagsEXT
    pLayer: POINTER(CAMetalLayer)

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 flags: VkMetalSurfaceCreateFlagsEXT | None = None,
                 pLayer: POINTER(CAMetalLayer) | None = None,
    ) -> None: ...

class VkExportMetalObjectCreateInfoEXT(Structure):
    sType: VkStructureType
    pNext: c_void_p
    exportObjectType: VkExportMetalObjectTypeFlagBitsEXT

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 exportObjectType: VkExportMetalObjectTypeFlagBitsEXT | None = None,
    ) -> None: ...

class VkExportMetalObjectsInfoEXT(Structure):
    sType: VkStructureType
    pNext: c_void_p

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
    ) -> None: ...

class VkExportMetalDeviceInfoEXT(Structure):
    sType: VkStructureType
    pNext: c_void_p
    mtlDevice: MTLDevice_id

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 mtlDevice: MTLDevice_id | None = None,
    ) -> None: ...

class VkExportMetalCommandQueueInfoEXT(Structure):
    sType: VkStructureType
    pNext: c_void_p
    queue: VkQueue
    mtlCommandQueue: MTLCommandQueue_id

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 queue: VkQueue | None = None,
                 mtlCommandQueue: MTLCommandQueue_id | None = None,
    ) -> None: ...

class VkExportMetalBufferInfoEXT(Structure):
    sType: VkStructureType
    pNext: c_void_p
    memory: VkDeviceMemory
    mtlBuffer: MTLBuffer_id

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 memory: VkDeviceMemory | None = None,
                 mtlBuffer: MTLBuffer_id | None = None,
    ) -> None: ...

class VkImportMetalBufferInfoEXT(Structure):
    sType: VkStructureType
    pNext: c_void_p
    mtlBuffer: MTLBuffer_id

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 mtlBuffer: MTLBuffer_id | None = None,
    ) -> None: ...

class VkExportMetalTextureInfoEXT(Structure):
    sType: VkStructureType
    pNext: c_void_p
    image: VkImage
    imageView: VkImageView
    bufferView: VkBufferView
    plane: VkImageAspectFlagBits
    mtlTexture: MTLTexture_id

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 image: VkImage | None = None,
                 imageView: VkImageView | None = None,
                 bufferView: VkBufferView | None = None,
                 plane: VkImageAspectFlagBits | None = None,
                 mtlTexture: MTLTexture_id | None = None,
    ) -> None: ...

class VkImportMetalTextureInfoEXT(Structure):
    sType: VkStructureType
    pNext: c_void_p
    plane: VkImageAspectFlagBits
    mtlTexture: MTLTexture_id

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 plane: VkImageAspectFlagBits | None = None,
                 mtlTexture: MTLTexture_id | None = None,
    ) -> None: ...

class VkExportMetalIOSurfaceInfoEXT(Structure):
    sType: VkStructureType
    pNext: c_void_p
    image: VkImage
    ioSurface: IOSurfaceRef

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 image: VkImage | None = None,
                 ioSurface: IOSurfaceRef | None = None,
    ) -> None: ...

class VkImportMetalIOSurfaceInfoEXT(Structure):
    sType: VkStructureType
    pNext: c_void_p
    ioSurface: IOSurfaceRef

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 ioSurface: IOSurfaceRef | None = None,
    ) -> None: ...

class VkExportMetalSharedEventInfoEXT(Structure):
    sType: VkStructureType
    pNext: c_void_p
    semaphore: VkSemaphore
    event: VkEvent
    mtlSharedEvent: MTLSharedEvent_id

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 semaphore: VkSemaphore | None = None,
                 event: VkEvent | None = None,
                 mtlSharedEvent: MTLSharedEvent_id | None = None,
    ) -> None: ...

class VkImportMetalSharedEventInfoEXT(Structure):
    sType: VkStructureType
    pNext: c_void_p
    mtlSharedEvent: MTLSharedEvent_id

    def __init__(self,
                 sType: VkStructureType | None = None,
                 pNext: c_void_p | None = None,
                 mtlSharedEvent: MTLSharedEvent_id | None = None,
    ) -> None: ...

