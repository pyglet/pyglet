"""Generate the EGL 1.5 ctypes bindings from ``tools/gen_opengl/egl.xml``."""
from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

from gen_khronos import REPO_ROOT, KhronosWriter, read_extensions, read_profile


GEN_OPENGL_DIR = Path(__file__).parent
XML_FILE = GEN_OPENGL_DIR / "egl.xml"
DEST_PATH = REPO_ROOT / "pyglet" / "libs" / "egl" / "egl.py"
TEMPLATE = GEN_OPENGL_DIR / "egl.template"


EXTENSIONS = [
    "EGL_EXT_device_enumeration",
    "EGL_EXT_device_query",
    "EGL_EXT_platform_base",
    "EGL_EXT_platform_device",
    "EGL_EXT_platform_wayland",
    "EGL_KHR_platform_wayland",
    "EGL_KHR_platform_x11",
    "EGL_EXT_platform_x11",
    "EGL_KHR_platform_gbm",
    "EGL_MESA_platform_gbm",
    "EGL_KHR_create_context",
    "EGL_KHR_surfaceless_context",
    "EGL_KHR_no_config_context",
    "EGL_KHR_create_context_no_error",
    "EGL_KHR_image",
    "EGL_EXT_image_dma_buf_import",
    "EGL_EXT_image_dma_buf_import_modifiers",
    "EGL_KHR_fence_sync",
    "EGL_KHR_wait_sync",
    "EGL_EXT_buffer_age",
    "EGL_KHR_partial_update",
    "EGL_KHR_swap_buffers_with_damage",
    "EGL_KHR_gl_colorspace",
    "EGL_KHR_debug",
]

EGL_TYPES = {
    "khronos_utime_nanoseconds_t": "c_uint64",
    "khronos_stime_nanoseconds_t": "c_int64",
    "khronos_ssize_t": "c_ssize_t",
    "EGLBoolean": "c_uint",
    "EGLenum": "c_uint",
    "EGLAttrib": "c_ssize_t",
    "EGLAttribKHR": "c_ssize_t",
    "EGLClientBuffer": "c_void_p",
    "EGLClientPixmapHI": "c_byte",
    "EGLConfig": "c_void_p",
    "EGLContext": "c_void_p",
    "EGLDisplay": "c_void_p",
    "EGLDeviceEXT": "c_void_p",
    "EGLImage": "c_void_p",
    "EGLImageKHR": "c_void_p",
    "EGLLabelKHR": "c_void_p",
    "EGLNativeFileDescriptorKHR": "c_int",
    "EGLNativeDisplayType": "POINTER(Display)",
    "EGLNativePixmapType": "Pixmap",
    "EGLNativeWindowType": "Window",
    "EGLObjectKHR": "c_void_p",
    "EGLOutputLayerEXT": "c_void_p",
    "EGLOutputPortEXT": "c_void_p",
    "EGLsizeiANDROID": "c_ssize_t",
    "EGLSetBlobFuncANDROID": "CFUNCTYPE(None, c_void_p, EGLsizeiANDROID, c_void_p, EGLsizeiANDROID)",
    "EGLGetBlobFuncANDROID": "CFUNCTYPE(EGLsizeiANDROID, c_void_p, EGLsizeiANDROID, c_void_p, EGLsizeiANDROID)",
    "EGLStreamKHR": "c_void_p",
    "EGLSurface": "c_void_p",
    "EGLSync": "c_void_p",
    "EGLSyncKHR": "c_void_p",
    "EGLSyncNV": "c_void_p",
    "EGLTime": "khronos_utime_nanoseconds_t",
    "EGLTimeKHR": "khronos_utime_nanoseconds_t",
    "EGLTimeNV": "khronos_utime_nanoseconds_t",
    "EGLint": "c_int",
    "EGLnsecsANDROID": "khronos_stime_nanoseconds_t",
    "EGLuint64KHR": "c_uint64",
    "EGLuint64NV": "c_uint64",
    "AHardwareBuffer": "c_byte",
    "wl_buffer": "c_byte",
    "wl_display": "c_byte",
    "wl_resource": "c_byte",
    "EGLDEBUGPROCKHR": "CFUNCTYPE(None, EGLenum, c_char_p, EGLint, EGLLabelKHR, EGLLabelKHR, c_char_p)",
    "__eglMustCastToProperFunctionPointerType": "CFUNCTYPE(None)",
}


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEST_PATH)
    parser.add_argument(
        "--extensions-file",
        action="store_true",
        help="Write extensions to a separate *_ext.py module",
    )
    parser.add_argument(
        "--extra-extensions",
        action="store_true",
        help="Include every unlisted EGL registry extension in the extension module",
    )
    options = parser.parse_args()
    if options.extra_extensions and not options.extensions_file:
        parser.error("--extra-extensions requires --extensions-file")

    KhronosWriter(
        registry=read_profile(
            XML_FILE,
            api="egl",
            version="1.5",
            extensions=() if options.extensions_file else EXTENSIONS,
        ),
        out_module=options.output,
        template=TEMPLATE,
        types=EGL_TYPES,
        link_function="_link_function",
        api_name="EGL",
    ).run()

    if options.extensions_file:
        KhronosWriter(
            registry=read_extensions(
                XML_FILE,
                api="egl",
                extensions=EXTENSIONS,
                include_extra_extensions=options.extra_extensions,
            ),
            out_module=options.output.with_name(
                f"{options.output.stem}_ext{options.output.suffix}"
            ),
            template=TEMPLATE,
            types=EGL_TYPES,
            link_function="_link_function",
            api_name="EGL",
        ).run()


if __name__ == "__main__":
    main()
