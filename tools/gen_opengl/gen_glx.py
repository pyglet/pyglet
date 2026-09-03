"""Generate the GLX 1.4 ctypes bindings from ``tools/gen_opengl/glx.xml``."""
from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

from gen_khronos import REPO_ROOT, KhronosWriter, read_extensions, read_profile


GEN_OPENGL_DIR = Path(__file__).parent
XML_FILE = GEN_OPENGL_DIR / "glx.xml"
DEST_PATH = REPO_ROOT / "pyglet" / "libs" / "linux" / "glx" / "glx.py"
TEMPLATE = GEN_OPENGL_DIR / "glx.template"

EXTENSIONS = [
    "GLX_ARB_create_context",
    "GLX_ARB_create_context_profile",
    "GLX_EXT_create_context_es2_profile",
    "GLX_ARB_create_context_robustness",
    "GLX_ARB_fbconfig_float",
    "GLX_EXT_swap_control",
    "GLX_MESA_swap_control",
    "GLX_SGI_swap_control",
    "GLX_EXT_swap_control_tear",
    "GLX_OML_sync_control",
    "GLX_SGI_video_sync",
    "GLX_EXT_import_context",
    "GLX_MESA_query_renderer",
    "GLX_NV_multigpu_context",
    "GLX_NV_swap_group",
]

GLX_TYPES = {
    "Bool": "c_int",
    "Display": "Display",
    "Font": "Font",
    "GLbitfield": "c_uint",
    "GLboolean": "c_ubyte",
    "GLenum": "c_uint",
    "GLfloat": "c_float",
    "GLint": "c_int",
    "GLintptr": "c_ssize_t",
    "GLsizei": "c_int",
    "GLsizeiptr": "c_ssize_t",
    "GLXContext": "c_void_p",
    "GLXContextID": "XID",
    "GLXDrawable": "XID",
    "GLXFBConfig": "c_void_p",
    "GLXFBConfigID": "XID",
    "GLXPbuffer": "XID",
    "GLXPixmap": "XID",
    "GLXWindow": "XID",
    "GLubyte": "c_ubyte",
    "GLuint": "c_uint",
    "GLvoid": "None",
    "int32_t": "c_int32",
    "int64_t": "c_int64",
    "Pixmap": "Pixmap",
    "Window": "Window",
    "XVisualInfo": "XVisualInfo",
    "__GLXextFuncPtr": "CFUNCTYPE(None)",
}


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEST_PATH)
    parser.add_argument("--extensions-file", action="store_true",
                        help="Write extensions to a separate *_ext.py module")
    parser.add_argument("--extra-extensions", action="store_true",
                        help="Include every unlisted GLX registry extension in the extension module.")
    options = parser.parse_args()
    if options.extra_extensions and not options.extensions_file:
        parser.error("--extra-extensions requires --extensions-file")

    KhronosWriter(
        registry=read_profile(XML_FILE, api="glx", version="1.4",
                              extensions=() if options.extensions_file else EXTENSIONS),
        out_module=options.output,
        template=TEMPLATE,
        types=GLX_TYPES,
        link_function="_link_function",
        api_name="GLX",
    ).run()

    if options.extensions_file:
        KhronosWriter(
            registry=read_extensions(XML_FILE, api="glx", extensions=EXTENSIONS,
                                     include_extra_extensions=options.extra_extensions),
            out_module=options.output.with_name(f"{options.output.stem}_ext{options.output.suffix}"),
            template=TEMPLATE,
            types=GLX_TYPES,
            link_function="_link_function",
            api_name="GLX",
        ).run()


if __name__ == "__main__":
    main()
