"""Get environment information useful for debugging.

Intended usage is to create a file for bug reports, e.g.::

    python -m pyglet.info > info.txt

Graphics API and version support can be tested in isolated subprocesses::

    python -m pyglet.info --probe-graphics > info.txt

One specific configuration can also be requested::

    python -m pyglet.info --backend gles3 --version 3.1

"""
from __future__ import annotations
# ruff: noqa: T201, PLW0603, BLE001, SLF001

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterable

from pyglet.enums import GraphicsAPI

if TYPE_CHECKING:
    from pyglet.graphics.api.base import SurfaceInfo
    from pyglet.graphics.api.gl.context import OpenGLSurfaceContext

_first_heading: bool = True
_printed_extensions_hint: bool = False
_EXTENSION_PREVIEW_LIMIT = 12
_GRAPHICS_WORKER_PREFIX = "PYGLET_GRAPHICS_PROBE="
_GRAPHICS_PROBES = (
    # A versionless desktop request lets the driver select its preferred modern context.
    (GraphicsAPI.OPENGL, None),
    (GraphicsAPI.OPENGL, (3, 3)),
    (GraphicsAPI.OPENGL_ES_3, (3, 2)),
    (GraphicsAPI.OPENGL_ES_3, (3, 1)),
    (GraphicsAPI.OPENGL_ES_3, (3, 0)),
    (GraphicsAPI.OPENGL_2, (2, 1)),
    (GraphicsAPI.OPENGL_2, (2, 0)),
    (GraphicsAPI.OPENGL_ES_2, (2, 0)),
)


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


def _show_verbose_errors() -> bool:
    return "--verbose" in sys.argv


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


def _graphics_api_family(api: GraphicsAPI | str) -> str:
    api = GraphicsAPI(api)
    if api in (GraphicsAPI.OPENGL, GraphicsAPI.OPENGL_2):
        return "desktop"
    if api in (GraphicsAPI.OPENGL_ES_2, GraphicsAPI.OPENGL_ES_3):
        return "es"
    return api.value


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
    print('os.getcwd():', Path.cwd())
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


def _dump_window(window: Any) -> None:
    """Dump an already-created window without taking ownership of it."""
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


def dump_window(window: Any | None = None) -> None:
    """Dump display, window, and screen info."""
    import pyglet.window  # noqa: PLC0415

    owns_window = window is None
    window = window or pyglet.window.Window(visible=False)
    try:
        _dump_window(window)
    finally:
        if owns_window:
            window.close()


def _dump_backend(window: Any) -> None:
    """Dump backend details from an already-created window."""
    import pyglet  # noqa: PLC0415
    from pyglet.graphics.api import core  # noqa: PLC0415

    print("status: available")
    print("configured backend option:", pyglet.options.backend)
    print("active context:", repr(window.context))

    if _is_opengl_backend(pyglet.options.backend):
        actual_api = window.context.info.get_opengl_api()
        if _graphics_api_family(actual_api) != _graphics_api_family(pyglet.options.backend):
            print(f"WARNING: requested {pyglet.options.backend}, but the driver returned {actual_api}.")

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


def dump_backend(window: Any | None = None) -> None:
    """Dump active backend details and selected surface config."""
    import pyglet.window  # noqa: PLC0415

    owns_window = window is None
    window = window or pyglet.window.Window(visible=False)
    try:
        _dump_backend(window)
    finally:
        if owns_window:
            window.close()


def _requested_graphics_details(config: Any | None) -> tuple[Any, Any, Any]:
    """Return the requested backend and version without creating a context."""
    import pyglet  # noqa: PLC0415

    backend = pyglet.options.backend
    requested = getattr(config, backend, None) if config is not None else None
    if requested is None:
        from pyglet.graphics.api import get_default_configs  # noqa: PLC0415

        try:
            defaults = get_default_configs()
        except Exception:
            defaults = ()
        requested = defaults[0] if defaults else None

    return backend, getattr(requested, "major_version", None), getattr(requested, "minor_version", None)


def _print_graphics_failure(exc: Exception, config: Any | None) -> None:
    """Print a useful, redirect-safe summary for graphics initialization errors."""
    backend, major, minor = _requested_graphics_details(config)
    print("status: context creation failed")
    print("requested backend:", backend)
    if major is not None:
        print(f"requested version: {major}.{minor or 0}")
    print(f"exception: {type(exc).__name__}: {exc}")
    print("This request failing does not necessarily mean that graphics are unavailable.")
    print("Run 'python -m pyglet.info --probe-graphics' to test other supported configurations.")
    print("Pass --verbose to include the full traceback.")
    if _show_verbose_errors():
        import traceback  # noqa: PLC0415

        traceback.print_exc(file=sys.stdout)


def _print_dump_failure(exc: Exception) -> None:
    print("status: diagnostic collection failed")
    print(f"exception: {type(exc).__name__}: {exc}")
    if _show_verbose_errors():
        import traceback  # noqa: PLC0415

        traceback.print_exc(file=sys.stdout)


def dump_window_and_backend(config: Any | None = None) -> None:
    """Create one diagnostic window and use it for all graphics output."""
    import pyglet.window  # noqa: PLC0415

    _heading("pyglet.window")
    try:
        window = pyglet.window.Window(visible=False, config=config)
    except Exception as exc:
        _print_graphics_failure(exc, config)
        _heading("pyglet.graphics.backend")
        print("status: unavailable because diagnostic context creation failed")
        return

    try:
        try:
            _dump_window(window)
        except Exception as exc:
            _print_dump_failure(exc)
        _heading("pyglet.graphics.backend")
        try:
            _dump_backend(window)
        except Exception as exc:
            _print_dump_failure(exc)
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
    for feature, available in vars(info.features).items():
        print(f"info.features.{feature}:", available)
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
    except Exception as exc:
        _print_dump_failure(exc)


def _make_graphics_config(backend: GraphicsAPI, version: tuple[int, int] | None) -> Any:
    """Build a conservative config for a single graphics probe."""
    import pyglet  # noqa: PLC0415

    config = pyglet.config.Config()
    backend_config = getattr(config, backend)
    if version is None:
        backend_config.major_version = backend_config.minor_version = None
    else:
        backend_config.major_version, backend_config.minor_version = version
    backend_config.double_buffer = True
    backend_config.depth_size = 16
    return config


def _graphics_probe_worker(backend_name: str, version_text: str) -> int:
    """Create one context and emit a machine-readable result for the parent."""
    import pyglet  # noqa: PLC0415

    backend = GraphicsAPI(backend_name)
    version = None if version_text == "default" else _parse_version(version_text)
    result: dict[str, Any] = {
        "backend": backend.value,
        "requested_version": list(version) if version is not None else None,
        "success": False,
    }
    window = None
    try:
        pyglet.options.backend = backend
        pyglet.options.debug_api = False
        config = _make_graphics_config(backend, version)
        import pyglet.window  # noqa: PLC0415

        window = pyglet.window.Window(visible=False, config=config)
        info = window.context.info
        actual_api = info.get_opengl_api()
        if _graphics_api_family(actual_api) != _graphics_api_family(backend):
            result.update(
                error_type="GraphicsAPIMismatch",
                error=f"requested {backend.value}, but the driver returned {actual_api}",
                actual_api=str(actual_api),
                actual_version=list(info.get_version()),
            )
        else:
            from pyglet.graphics.api import get_default_shader  # noqa: PLC0415
            from pyglet.shapes import get_default_shader as get_default_shapes_shader  # noqa: PLC0415

            get_default_shader()
            get_default_shapes_shader()
            result.update(
                success=True,
                actual_api=str(actual_api),
                actual_version=list(info.get_version()),
                version_string=info.get_version_string(),
                renderer=info.get_renderer(),
                features=vars(info.features),
            )
    except Exception as exc:
        result.update(error_type=type(exc).__name__, error=str(exc))
    finally:
        if window is not None:
            window.close()

    print(_GRAPHICS_WORKER_PREFIX + json.dumps(result, sort_keys=True))
    return 0


def _parse_graphics_worker_output(output: str) -> dict[str, Any] | None:
    for line in reversed(output.splitlines()):
        if line.startswith(_GRAPHICS_WORKER_PREFIX):
            try:
                return json.loads(line.removeprefix(_GRAPHICS_WORKER_PREFIX))
            except json.JSONDecodeError:
                return None
    return None


def _run_graphics_probe(backend: GraphicsAPI, version: tuple[int, int] | None) -> dict[str, Any]:
    """Run one probe in a clean interpreter to isolate backend global state."""
    env = os.environ.copy()
    env["PYGLET_BACKEND"] = backend.value
    env["PYGLET_DEBUG_API"] = "false"
    command = (
        sys.executable,
        "-m",
        "pyglet.info",
        "--graphics-worker",
        backend.value,
        _format_graphics_probe_version(version),
    )
    try:
        completed = subprocess.run(  # noqa: S603
            command,
            capture_output=True,
            check=False,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        return {
            "backend": backend.value,
            "requested_version": list(version) if version is not None else None,
            "success": False,
            "error_type": "TimeoutExpired",
            "error": "probe did not finish within 15 seconds",
        }

    result = _parse_graphics_worker_output(completed.stdout)
    if result is not None:
        return result

    error = completed.stderr.strip() or completed.stdout.strip() or f"worker exited with code {completed.returncode}"
    return {
        "backend": backend.value,
        "requested_version": list(version) if version is not None else None,
        "success": False,
        "error_type": "WorkerError",
        "error": error.splitlines()[-1],
    }


def dump_graphics_probe() -> None:
    """Probe pyglet graphics backends and versions in isolated processes."""
    _heading("Graphics capability probe")
    print("Each request is tested in a separate process. Please wait...")
    print(f"{'Backend':<9} {'Request':<9} {'Result':<9} {'Actual API/version or error'}")
    print(f"{'-' * 7:<9} {'-' * 7:<9} {'-' * 7:<9} {'-' * 37}")

    results = [_run_graphics_probe(backend, version) for backend, version in _GRAPHICS_PROBES]
    for result in results:
        backend = result["backend"]
        requested = _format_graphics_probe_version(result["requested_version"])
        if result["success"]:
            actual = ".".join(str(part) for part in result["actual_version"])
            details = f"{result['actual_api']} {actual} ({result['renderer']})"
            status = "success"
        else:
            details = f"{result.get('error_type', 'Error')}: {result.get('error', 'unknown error')}"
            status = "failed"
        print(f"{backend:<9} {requested:<9} {status:<9} {details}")

    successful = [result for result in results if result["success"]]
    if successful:
        suggested = max(successful, key=_graphics_probe_priority)
        requested = _format_graphics_probe_version(suggested["requested_version"])
        print()
        print(f"recommended request: {suggested['backend']} {requested}")
        command = f"python -m pyglet.info --backend {suggested['backend']}"
        if suggested["requested_version"] is not None:
            command += f" --version {requested}"
        print(f"suggested info command: {command}")
    else:
        print()
        print("No probed pyglet graphics configuration created a context.")


def _graphics_probe_priority(result: dict[str, Any]) -> tuple[int, int]:
    """Prefer pyglet's modern desktop backend, then modern GLES, then legacy backends."""
    backend = GraphicsAPI(result["backend"])
    version = result["requested_version"]
    if backend == GraphicsAPI.OPENGL:
        if version is None:
            return 500, 0
        return 400, version[0] * 10 + version[1]
    if backend == GraphicsAPI.OPENGL_ES_3:
        return 300, version[0] * 10 + version[1]
    if backend == GraphicsAPI.OPENGL_2:
        return 200, version[0] * 10 + version[1]
    if backend == GraphicsAPI.OPENGL_ES_2:
        return 100, version[0] * 10 + version[1]
    return 0, 0


def _format_graphics_probe_version(version: tuple[int, int] | list[int] | None) -> str:
    """Return a human- and worker-readable graphics probe request version."""
    return "default" if version is None else ".".join(str(part) for part in version)


def dump(graphics_config: Any | None = None) -> None:
    """Dump all information to stdout."""
    import pyglet  # noqa: PLC0415

    _try_dump("Platform", dump_platform)
    _try_dump("Python", dump_python)
    _try_dump("pyglet", dump_pyglet)
    dump_window_and_backend(graphics_config)
    _try_dump("pyglet.media", dump_media)
    if pyglet.compat_platform.startswith("win"):
        _try_dump("pyglet.input.wintab", dump_wintab)


def _parse_version(value: str) -> tuple[int, int]:
    try:
        major, minor = value.split(".", 1)
        return int(major), int(minor)
    except (ValueError, TypeError) as exc:
        import argparse  # noqa: PLC0415

        raise argparse.ArgumentTypeError("version must be in MAJOR.MINOR form, for example 3.1") from exc


def main(argv: list[str] | None = None) -> int:
    """Run the environment report or an isolated graphics probe worker."""
    import argparse  # noqa: PLC0415
    import pyglet  # noqa: PLC0415

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-extensions", action="store_true", help="include complete extension lists")
    parser.add_argument("--verbose", action="store_true", help="include tracebacks for diagnostic failures")
    parser.add_argument("--backend", choices=[api.value for api in GraphicsAPI], help="backend for the main report")
    parser.add_argument("--version", type=_parse_version, help="graphics version for the main report (MAJOR.MINOR)")
    parser.add_argument(
        "--probe-graphics",
        action="store_true",
        help="test supported OpenGL and OpenGL ES configurations in isolated processes",
    )
    parser.add_argument("--graphics-worker", nargs=2, metavar=("BACKEND", "VERSION"), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.graphics_worker:
        return _graphics_probe_worker(*args.graphics_worker)

    if args.version and not args.backend:
        parser.error("--version requires --backend")

    graphics_config = None
    if args.backend:
        backend = GraphicsAPI(args.backend)
        pyglet.options.backend = backend
        if args.version:
            if not _is_opengl_backend(backend):
                parser.error("--version is supported only for OpenGL and OpenGL ES backends")
            graphics_config = _make_graphics_config(backend, args.version)

    dump(graphics_config)
    if args.probe_graphics:
        dump_graphics_probe()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
