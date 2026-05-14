"""Get environment information useful for debugging.

Intended usage is to create a file for bug reports, e.g.::

    python -m pyglet.info > info.txt

"""
from __future__ import annotations
# ruff: noqa: T201, PLW0603, BLE001, SLF001

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterable

from pyglet.enums import GraphicsAPI

if TYPE_CHECKING:
    from pyglet.graphics.api.base import SurfaceInfo
    from pyglet.graphics.api.gl.context import OpenGLSurfaceContext

_first_heading: bool = True
_printed_extensions_hint: bool = False
_EXTENSION_PREVIEW_LIMIT = 12


def _heading(heading: str) -> None:
    global _first_heading
    if not _first_heading:
        print()
    else:
        _first_heading = False
    print(heading)
    print("-" * 78)


def _show_full_extensions() -> bool:
    return "-extensions" in sys.argv


def _dump_extensions(name: str, extensions: Iterable[str]) -> None:
    global _printed_extensions_hint

    extension_list = sorted(set(extensions))
    count = len(extension_list)
    print(f"{name}: {count} total")
    if not extension_list:
        return

    if _show_full_extensions():
        for extension in extension_list:
            print(" ", extension)
        return

    preview = ", ".join(extension_list[:_EXTENSION_PREVIEW_LIMIT])
    suffix = " ..." if count > _EXTENSION_PREVIEW_LIMIT else ""
    print(f"{name}.sample: {preview}{suffix}")
    if not _printed_extensions_hint:
        print("extensions hint: pass -extensions to include full extension lists")
        _printed_extensions_hint = True


def _is_opengl_backend(backend: GraphicsAPI) -> bool:
    return backend in (
        GraphicsAPI.OPENGL,
        GraphicsAPI.OPENGL_2,
        GraphicsAPI.OPENGL_ES_2,
        GraphicsAPI.OPENGL_ES_3,
    )


def dump_platform() -> None:
    """Dump OS specific."""
    import platform  # noqa: PLC0415

    print("platform:", platform.platform())
    print("release: ", platform.release())
    print("version: ", platform.version())
    print("machine: ", platform.machine())
    print("processor:", platform.processor())


def dump_python() -> None:
    """Dump Python version and environment to stdout."""
    import platform  # noqa: PLC0415

    print("implementation:", platform.python_implementation())
    print("sys.version:", sys.version)
    print("sys.maxint:", sys.maxsize)
    print("sys.argv:", sys.argv)
    print('os.getcwd():', os.getcwd())
    for key, value in os.environ.items():
        if key.startswith("PYGLET_"):
            print(f"os.environ['{key}']: {value}")


def dump_pyglet() -> None:
    """Dump pyglet version and options."""
    import pyglet  # noqa: PLC0415

    print("pyglet.version:", pyglet.version)
    print("pyglet.compat_platform:", pyglet.compat_platform)
    print("pyglet.__file__:", pyglet.__file__)
    for key, value in pyglet.options.items():
        print(f"pyglet.options.{key} = {value!r}")


def dump_window() -> None:
    """Dump display, window, and screen info."""
    import pyglet.window  # noqa: PLC0415

    window = pyglet.window.Window(visible=False)
    try:
        display = window.display
        print("display:", repr(display))
        print("window:", repr(window))
        print("window.get_size():", window.get_size())
        print("window.get_framebuffer_size():", window.get_framebuffer_size())
        print("window.get_pixel_ratio():", window.get_pixel_ratio())

        screens = display.get_screens()
        for i, screen in enumerate(screens):
            print(f"screens[{i}]: {screen!r}")
        print("window.context:", repr(window.context))
    finally:
        window.close()


def dump_backend() -> None:
    """Dump active backend details and selected surface config."""
    import pyglet  # noqa: PLC0415
    import pyglet.window  # noqa: PLC0415
    from pyglet.graphics.api import core  # noqa: PLC0415

    window = pyglet.window.Window(visible=False)
    try:
        print("configured backend option:", pyglet.options.backend)
        print("active context:", repr(window.context))

        if _is_opengl_backend(pyglet.options.backend) and (
            (not core.have_version(3) and pyglet.options.backend in (GraphicsAPI.OPENGL, GraphicsAPI.OPENGL_ES_3))
            or (
                not core.have_version(2)
                and pyglet.options.backend in (GraphicsAPI.OPENGL_2, GraphicsAPI.OPENGL_ES_2)
            )
        ):
            print(f"Insufficient OpenGL version: {core.info.get_version_string()}")
            return

        _heading("backend.selected_surface_config")
        print("Selected surface config attributes (chosen by backend/system):")
        for key, value in window.config.attributes.items():
            print(f"selected_config['{key}'] = {value!r}")

        _heading("backend.graphics_api")
        dump_graphics_api(window.context)

        _heading("backend.platform_api")
        dump_backend_platform_api(window.context)
    finally:
        window.close()


def dump_graphics_api(context: OpenGLSurfaceContext | None = None) -> None:
    """Dump active graphics API info for the given context."""
    if context is None:
        import pyglet.window  # noqa: PLC0415

        window = pyglet.window.Window(visible=False)
        try:
            dump_graphics_api(window.context)
        finally:
            window.close()
        return

    info: SurfaceInfo = context.info
    print("info.version_string:", info.get_version_string())
    print("info.version:", info.get_version())
    print("info.vendor:", info.get_vendor())
    print("info.renderer:", info.get_renderer())
    print("info.api:", info.get_opengl_api())
    print("info.shading_language_version:", info.shading_language_version)
    print("info.max_texture_size:", info.MAX_TEXTURE_SIZE)
    print("info.max_texture_image_units:", info.MAX_TEXTURE_IMAGE_UNITS)
    print("info.max_combined_texture_image_units:", info.MAX_COMBINED_TEXTURE_IMAGE_UNITS)
    print("info.max_array_texture_layers:", info.MAX_ARRAY_TEXTURE_LAYERS)
    print("info.max_uniform_buffer_bindings:", info.MAX_UNIFORM_BUFFER_BINDINGS)
    print("info.max_uniform_block_size:", info.MAX_UNIFORM_BLOCK_SIZE)
    print("info.max_vertex_attribs:", info.MAX_VERTEX_ATTRIBS)
    _dump_extensions("info.extensions", info.get_extensions())


def dump_backend_glx(context: OpenGLSurfaceContext | None = None) -> None:
    """Dump GLX info."""
    import pyglet  # noqa: PLC0415

    if not pyglet.compat_platform.startswith("linux"):
        print("GLX not applicable on this platform.")
        return

    if context is None:
        import pyglet.window  # noqa: PLC0415

        window = pyglet.window.Window(visible=False)
        try:
            dump_backend_glx(window.context)
        finally:
            window.close()
        return

    platform_info = context.info.platform_info
    if platform_info is None:
        print("GLX info unavailable for this context.")
        return

    print("context.is_direct():", context.is_direct())
    if not platform_info.have_version(1, 1):
        print("Version: < 1.1")
        return

    print("backend.platform.glx.server_vendor:", platform_info.get_server_vendor())
    print("backend.platform.glx.server_version:", platform_info.get_server_version())
    _dump_extensions("backend.platform.glx.server_extensions", platform_info.get_server_extensions())
    print("backend.platform.glx.client_vendor:", platform_info.get_client_vendor())
    print("backend.platform.glx.client_version:", platform_info.get_client_version())
    _dump_extensions("backend.platform.glx.client_extensions", platform_info.get_client_extensions())
    _dump_extensions("backend.platform.glx.extensions", platform_info.get_extensions(context))


def dump_backend_wgl(context: OpenGLSurfaceContext | None = None) -> None:
    """Dump WGL info."""
    import pyglet  # noqa: PLC0415

    if not pyglet.compat_platform.startswith("win"):
        print("WGL not applicable on this platform.")
        return

    if context is None:
        import pyglet.window  # noqa: PLC0415

        window = pyglet.window.Window(visible=False)
        try:
            dump_backend_wgl(window.context)
        finally:
            window.close()
        return

    platform_info = context.info.platform_info
    if platform_info is None:
        print("WGL info unavailable for this context.")
        return

    _dump_extensions("backend.platform.wgl.extensions", platform_info.get_extensions(context))


def dump_backend_platform_api(context: OpenGLSurfaceContext) -> None:
    """Dump platform-specific OpenGL details for the active backend."""
    import pyglet  # noqa: PLC0415

    if not _is_opengl_backend(pyglet.options.backend):
        print(f"Skipping platform GL info for backend: {pyglet.options.backend}")
        return

    if pyglet.compat_platform.startswith("linux"):
        dump_backend_glx(context)
    elif pyglet.compat_platform.startswith("win"):
        dump_backend_wgl(context)
    elif pyglet.compat_platform == "darwin":
        print("Cocoa context platform API details are not currently exposed.")
    else:
        print(f"No platform API handler for platform: {pyglet.compat_platform}")


def dump_gl(context: OpenGLSurfaceContext | None = None) -> None:
    """Backward-compatible wrapper for :func:`dump_graphics_api`."""
    dump_graphics_api(context)


def dump_glx(context: OpenGLSurfaceContext | None = None) -> None:
    """Backward-compatible wrapper for :func:`dump_backend_glx`."""
    dump_backend_glx(context)


def dump_wgl(context: OpenGLSurfaceContext | None = None) -> None:
    """Backward-compatible wrapper for :func:`dump_backend_wgl`."""
    dump_backend_wgl(context)


def dump_gl_platform(context: OpenGLSurfaceContext) -> None:
    """Backward-compatible wrapper for :func:`dump_backend_platform_api`."""
    dump_backend_platform_api(context)


def dump_media() -> None:
    """Dump pyglet.media info."""
    import pyglet.media  # noqa: PLC0415

    audio_driver = pyglet.media.get_audio_driver()
    print("audio driver:", audio_driver)
    print("audio driver type:", type(audio_driver).__name__ if audio_driver else None)
    dump_ffmpeg()
    dump_al()
    dump_media_decoders()


def dump_ffmpeg() -> None:
    """Dump FFmpeg info."""
    import pyglet  # noqa: PLC0415

    pyglet.options.search_local_libs = True
    import pyglet.media  # noqa: PLC0415

    print("ffmpeg.available:", pyglet.media.have_ffmpeg())
    if pyglet.media.have_ffmpeg():
        from pyglet.media.codecs.ffmpeg import get_version  # noqa: PLC0415

        print("ffmpeg.version:", get_version())
    else:
        print("ffmpeg.version:", None)


def dump_al() -> None:
    """Dump OpenAL info."""
    try:
        from pyglet.media.drivers import openal  # noqa: PLC0415
    except Exception:
        print("openal.available:", False)
        return

    print("openal.available:", True)
    print("openal.library:", openal.lib_openal._lib)

    driver = openal.create_audio_driver()
    print("openal.version: {}.{}".format(*driver.get_version()))
    _dump_extensions("openal.extensions", driver.get_extensions())


def dump_media_decoders() -> None:
    """Dump available media decoders."""
    from pyglet.media import codecs  # noqa: PLC0415

    decoders = codecs.get_decoders()
    print("media.decoders.total:", len(decoders))
    for i, decoder in enumerate(decoders):
        decoder_name = f"{decoder.__class__.__module__}.{decoder.__class__.__name__}"
        capabilities = ", ".join(decoder.get_media_capabilities()) or "unknown"
        print(f"media.decoder[{i}]: {decoder_name}")
        print(f"media.decoder[{i}].capabilities: {capabilities}")


def dump_wintab() -> None:
    """Dump WinTab info."""
    try:
        from pyglet.input.win32 import wintab  # noqa: PLC0415
    except Exception:
        print("WinTab not available.")
        return

    interface_name = wintab.get_interface_name()
    impl_version = wintab.get_implementation_version()
    spec_version = wintab.get_spec_version()

    print(
        f"WinTab: {interface_name} {impl_version >> 8}.{impl_version & 0xff} "
        f"(Spec {spec_version >> 8}.{spec_version & 0xff})",
    )


def _try_dump(heading: str, func: Callable[[], None]) -> None:
    _heading(heading)
    try:
        func()
    except Exception:
        import traceback  # noqa: PLC0415

        traceback.print_exc()


def dump() -> None:
    """Dump all information to stdout."""
    import pyglet  # noqa: PLC0415

    _try_dump("Platform", dump_platform)
    _try_dump("Python", dump_python)
    _try_dump("pyglet", dump_pyglet)
    _try_dump("pyglet.window", dump_window)
    _try_dump("pyglet.graphics.backend", dump_backend)
    _try_dump("pyglet.media", dump_media)
    if pyglet.compat_platform.startswith("win"):
        _try_dump("pyglet.input.wintab", dump_wintab)


if __name__ == "__main__":
    dump()
