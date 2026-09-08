"""Generate the WGL 1.0 ctypes bindings from ``tools/gen_opengl/wgl.xml``."""
from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

from gen_khronos import REPO_ROOT, KhronosWriter, read_extensions, read_profile


GEN_OPENGL_DIR = Path(__file__).parent
XML_FILE = GEN_OPENGL_DIR / "wgl.xml"
DEST_PATH = REPO_ROOT / "pyglet" / "libs" / "win32" / "wgl.py"
TEMPLATE = GEN_OPENGL_DIR / "wgl.template"

# Extensions to output.
EXTENSIONS = [
    "WGL_ARB_create_context",
    "WGL_ARB_create_context_profile",
    "WGL_ARB_extensions_string",
    "WGL_EXT_extensions_string",
    "WGL_ARB_pixel_format",
    "WGL_EXT_create_context_es2_profile",
    "WGL_EXT_swap_control",
    "WGL_EXT_swap_control_tear",  # Adaptive vsync?
    "WGL_ARB_multisample",
    "WGL_ARB_framebuffer_sRGB",
    "WGL_NV_DX_interop",
    "WGL_NV_DX_interop2",
    "WGL_NV_gpu_affinity",
    "WGL_AMD_gpu_association",
]

WGL_TYPES = {
    "BOOL": "BOOL",
    "COLORREF": "COLORREF",
    "DWORD": "DWORD",
    "FLOAT": "FLOAT",
    "GLbitfield": "c_uint",
    "GLenum": "c_uint",
    "GLint": "c_int",
    "GLsizei": "c_int",
    "GLuint": "c_uint",
    "HANDLE": "HANDLE",
    "HDC": "HDC",
    "HENHMETAFILE": "HENHMETAFILE",
    "HGPUNV": "HGPUNV",
    "HGLRC": "HANDLE",
    "INT": "c_int",
    "LAYERPLANEDESCRIPTOR": "LAYERPLANEDESCRIPTOR",
    "LPCSTR": "LPCSTR",
    "LPGLYPHMETRICSFLOAT": "LPGLYPHMETRICSFLOAT",
    "PIXELFORMATDESCRIPTOR": "PIXELFORMATDESCRIPTOR",
    "PGPU_DEVICE": "PGPU_DEVICE",
    "PROC": "CFUNCTYPE(c_int)",
    "UINT": "UINT",
    "VOID": "None",
}

# These are from gdi32, not opengl.
WGL_EXCLUDED_COMMANDS = {
    "ChoosePixelFormat",
    "DescribePixelFormat",
    "GetEnhMetaFilePixelFormat",
    "GetPixelFormat",
    "SetPixelFormat",
    "SwapBuffers",
}


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEST_PATH)
    parser.add_argument("--extensions-file", action="store_true",
                        help="Write extensions to a separate *_ext.py module")
    parser.add_argument("--extra-extensions", action="store_true",
                        help="include every unlisted WGL registry extension in the extension module")
    options = parser.parse_args()
    if options.extra_extensions and not options.extensions_file:
        parser.error("--extra-extensions requires --extensions-file")

    KhronosWriter(
        registry=read_profile(XML_FILE, api="wgl", version="1.0",
                              extensions=() if options.extensions_file else EXTENSIONS),
        out_module=options.output,
        template=TEMPLATE,
        types=WGL_TYPES,
        link_function="_link_function",
        api_name="WGL",
        function_class="WGLFunctionsARB",
        function_subclass="WGLFunctions",
        exclude_commands=WGL_EXCLUDED_COMMANDS,
    ).run()

    if options.extensions_file:
        KhronosWriter(
            registry=read_extensions(XML_FILE, api="wgl", extensions=EXTENSIONS,
                                     include_extra_extensions=options.extra_extensions),
            out_module=options.output.with_name(f"{options.output.stem}_ext{options.output.suffix}"),
            template=TEMPLATE,
            types=WGL_TYPES,
            link_function="_link_function",
            api_name="WGL",
            exclude_commands=WGL_EXCLUDED_COMMANDS,
        ).run()


if __name__ == "__main__":
    main()
