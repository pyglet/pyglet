# ruff: noqa: INP001
"""Build and serve a pyglet application for Pyodide."""
from __future__ import annotations

import argparse
import ast
import functools
import http.server
import json
import shutil
import socketserver
import sys
import webbrowser
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

try:
    import tomllib
except ImportError:  # Python 3.10 has no TOML parser in the standard library.
    try:
        import tomli as tomllib  # Use this is someone still wants to use it in 3.10
    except ImportError:
        tomllib = None  # type: ignore[assignment]

PYODIDE_VERSION = "0.29.4"
DEFAULT_PYODIDE_URL = f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VERSION}/full/pyodide.mjs"
RESOURCE_METHODS = {
    "add_font", "animation", "attributed", "audio", "file", "html", "image",
    "scene", "shader", "text", "texture", "video",
}


@dataclass(frozen=True)
class WebProject:
    """Declarative inputs for one web build."""

    root: Path
    entrypoint: Path
    output: Path
    resources: tuple[str, ...]
    sources: tuple[str, ...]
    web: Path | None
    fonts: tuple[WebFont, ...]
    title: str = "pyglet application"
    pyodide_url: str = DEFAULT_PYODIDE_URL


@dataclass(frozen=True)
class WebFont:
    """A font loaded by the browser before the Python application starts."""

    name: str
    path: Path
    url: str
    descriptors: dict[str, str]


@dataclass(frozen=True)
class DiscoveredAsset:
    name: str
    source: Path
    line: int


def load_project(
    project_file: str | Path = "pyproject.toml",
    *,
    entrypoint: str | None = None,
    output: str | None = None,
    resources: Sequence[str] | None = None,
    sources: Sequence[str] | None = None,
    title: str | None = None,
) -> WebProject:
    """Load ``[tool.pyglet.web]`` and apply command-line overrides."""
    project_path = Path(project_file).resolve()
    data: dict[str, Any] = {}
    if project_path.is_file():
        if tomllib is None:
            if entrypoint is None:
                raise RuntimeError(
                    "Reading pyproject.toml requires Python 3.11 or newer, or the optional 'tomli' package. "
                    "Install it with 'python -m pip install tomli', or pass project inputs through command-line "
                    "options.",
                )
        else:
            with project_path.open("rb") as file:
                data = tomllib.load(file).get("tool", {}).get("pyglet", {}).get("web", {})
    elif entrypoint is None:
        message = f"Project configuration not found: {project_path}"
        raise FileNotFoundError(message)

    root = project_path.parent
    entrypoint_value = entrypoint or data.get("entrypoint")
    if not entrypoint_value:
        raise ValueError("Set tool.pyglet.web.entrypoint or pass --entrypoint.")

    entrypoint_path = _inside_root(root, root / entrypoint_value, "entrypoint")
    if not entrypoint_path.is_file():
        message = f"Entrypoint not found: {entrypoint_path}"
        raise FileNotFoundError(message)

    output_path = (root / (output or data.get("output", "dist/web"))).resolve()
    if output_path == root:
        raise ValueError("The web output directory cannot be the project root.")
    resource_patterns = (
        tuple(resources) if resources is not None else _string_sequence(data.get("resources", ()), "resources")
    )
    source_patterns = (
        tuple(sources) if sources is not None else _string_sequence(data.get("sources", ("**/*.py",)), "sources")
    )
    web = _web_directory(root, data.get("web", "web"), output_path)
    fonts = _load_fonts(data.get("fonts", ()), root, web)
    return WebProject(
        root=root,
        entrypoint=entrypoint_path,
        output=output_path,
        resources=resource_patterns,
        sources=source_patterns,
        web=web,
        fonts=fonts,
        title=title or str(data.get("title", entrypoint_path.stem)),
        pyodide_url=str(data.get("pyodide_url", DEFAULT_PYODIDE_URL)),
    )


def build(project: WebProject) -> Path:
    """Build a self-contained directory that can be served over HTTP."""
    project.output.mkdir(parents=True, exist_ok=True)

    source_files = _expand_patterns(project.root, project.sources, project.output)
    source_files.add(project.entrypoint)
    resource_files = _expand_patterns(project.root, project.resources, project.output)
    application_files = source_files | resource_files

    custom_index = _copy_web_files(project.web, project.output)
    _write_zip(project.output / "application.zip", project.root, application_files)
    _write_pyglet_zip(project.output / "pyglet.zip")
    _copy_emscripten_javascript(project.output / "pyglet_emscripten.js")

    manifest = {
        "entrypoint": project.entrypoint.relative_to(project.root).as_posix(),
        "resources": sorted(path.relative_to(project.root).as_posix() for path in resource_files),
        "sources": sorted(path.relative_to(project.root).as_posix() for path in source_files),
    }
    (project.output / "pyglet-web.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf8")
    if not custom_index:
        (project.output / "index.html").write_text(_render_html(project.title), encoding="utf8")
    (project.output / "pyglet-web.js").write_text(_render_javascript(project, manifest["entrypoint"]), encoding="utf8")
    return project.output


def discover(project: WebProject) -> list[DiscoveredAsset]:
    """Find literal ``pyglet.resource`` calls as non-authoritative build hints.

    Dynamic names and resources reached only through unexamined code paths
    cannot be proven this way. The configured ``resources`` patterns remain
    the authoritative build input.
    """
    results: list[DiscoveredAsset] = []
    for source in sorted(_expand_patterns(project.root, project.sources, project.output) | {project.entrypoint}):
        try:
            tree = ast.parse(source.read_text(encoding="utf8"), filename=str(source))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            function = node.func
            if not isinstance(function, ast.Attribute) or function.attr not in RESOURCE_METHODS:
                continue
            owner = function.value
            direct_resource = isinstance(owner, ast.Name) and owner.id == "resource"
            pyglet_resource = (
                isinstance(owner, ast.Attribute)
                and owner.attr == "resource"
                and isinstance(owner.value, ast.Name)
                and owner.value.id == "pyglet"
            )
            if not (direct_resource or pyglet_resource):
                continue
            first_argument = node.args[0]
            if isinstance(first_argument, ast.Constant) and isinstance(first_argument.value, str):
                results.append(DiscoveredAsset(first_argument.value, source, node.lineno))
    return results


def _string_sequence(value: object, field: str) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, list | tuple):
        message = f"tool.pyglet.web.{field} must be an array of strings."
        raise TypeError(message)
    if not all(isinstance(item, str) for item in value):
        message = f"tool.pyglet.web.{field} must contain only strings."
        raise TypeError(message)
    return tuple(value)


def _web_directory(root: Path, value: object, output: Path) -> Path | None:
    if not isinstance(value, str):
        raise TypeError("tool.pyglet.web.web must be a relative directory path.")
    if Path(value).is_absolute() or ".." in Path(value).parts:
        message = f"The web directory must be relative and remain inside the project: {value!r}"
        raise ValueError(message)
    directory = _inside_root(root, root / value, "web directory")
    if not directory.exists():
        return None
    if not directory.is_dir():
        message = f"The web directory is not a directory: {directory}"
        raise NotADirectoryError(message)
    if directory == output or output in directory.parents:
        raise ValueError("The web directory cannot be inside the web output directory.")
    return directory


def _load_fonts(value: object, root: Path, web: Path | None) -> tuple[WebFont, ...]:
    if value == ():
        return ()
    if web is None:
        raise ValueError("tool.pyglet.web.fonts requires a web directory.")
    if not isinstance(value, list | tuple):
        raise TypeError("tool.pyglet.web.fonts must be an array of tables.")

    fonts: list[WebFont] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            message = f"tool.pyglet.web.fonts[{index}] must be a table."
            raise TypeError(message)
        name = item.get("name")
        path_value = item.get("path")
        if not isinstance(name, str) or not name:
            message = f"tool.pyglet.web.fonts[{index}].name must be a non-empty string."
            raise TypeError(message)
        if not isinstance(path_value, str) or not path_value:
            message = f"tool.pyglet.web.fonts[{index}].path must be a non-empty string."
            raise TypeError(message)
        if Path(path_value).is_absolute() or ".." in Path(path_value).parts:
            message = f"Font paths must be relative to the web directory: {path_value!r}"
            raise ValueError(message)
        path = _inside_root(root, web / path_value, "font")
        if not path.is_file():
            message = f"Font not found: {path}"
            raise FileNotFoundError(message)
        descriptors = {key: descriptor for key, descriptor in item.items() if key not in {"name", "path"}}
        if not all(isinstance(key, str) and isinstance(descriptor, str) for key, descriptor in descriptors.items()):
            message = f"tool.pyglet.web.fonts[{index}] descriptors must be strings."
            raise TypeError(message)
        fonts.append(WebFont(name, path, path.relative_to(web).as_posix(), descriptors))
    return tuple(fonts)


def _inside_root(root: Path, path: Path, description: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exception:
        message = f"The {description} must be inside the project root: {resolved}"
        raise ValueError(message) from exception
    return resolved


def _expand_patterns(root: Path, patterns: Sequence[str], output: Path) -> set[Path]:
    files: set[Path] = set()
    output = output.resolve()
    for pattern in patterns:
        if Path(pattern).is_absolute() or ".." in Path(pattern).parts:
            message = f"Build patterns must be relative and remain inside the project: {pattern!r}"
            raise ValueError(message)
        for match in root.glob(pattern):
            candidates: Iterable[Path] = match.rglob("*") if match.is_dir() else (match,)
            for candidate in candidates:
                if not candidate.is_file() or _is_ignored(candidate, root, output):
                    continue
                files.add(_inside_root(root, candidate, "build input"))
    return files


def _is_ignored(path: Path, root: Path, output: Path) -> bool:
    resolved = path.resolve()
    if resolved == output or output in resolved.parents:
        return True
    relative_parts = resolved.relative_to(root.resolve()).parts
    return any(part in {"__pycache__", ".git", ".venv", "venv"} for part in relative_parts)


def _write_zip(filename: Path, root: Path, files: Iterable[Path]) -> None:
    with zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path, path.relative_to(root).as_posix())


def _copy_web_files(web: Path | None, output: Path) -> bool:
    """Copy user-owned browser files and return whether they provided an index."""
    if web is None:
        return False
    for source in web.rglob("*"):
        if not source.is_file():
            continue
        destination = output / source.relative_to(web)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    return (web / "index.html").is_file()


def _write_pyglet_zip(filename: Path) -> None:
    package_root = _pyglet_package_root()
    files = (
        path for path in package_root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}
    )
    with zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, (Path("pyglet") / path.relative_to(package_root)).as_posix())


def _copy_emscripten_javascript(filename: Path) -> None:
    """Copy pyglet's reusable browser bridge into a generated web project."""
    source = _pyglet_package_root() / "libs" / "emscripten" / "pyglet_emscripten.js"
    if not source.is_file():
        message = f"pyglet's Emscripten JavaScript module was not found: {source}"
        raise FileNotFoundError(message)
    shutil.copyfile(source, filename)


def _pyglet_package_root() -> Path:
    """Return the pyglet package shipped beside this source-checkout tool."""
    package_root = Path(__file__).resolve().parents[1] / "pyglet"
    if package_root.is_dir():
        return package_root
    message = f"pyglet package directory was not found: {package_root}"
    raise FileNotFoundError(message)


def _render_html(title: str) -> str:
    escaped_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
</head>
<body>
  <canvas id="pygletCanvas"></canvas>
  <pre id="pygletStatus">Loading…</pre>
  <script type="module" src="pyglet-web.js"></script>
</body>
</html>
"""


def _render_javascript(project: WebProject, entrypoint: str) -> str:
    pyodide_url = json.dumps(project.pyodide_url)
    entrypoint_json = json.dumps(entrypoint)
    fonts_json = json.dumps([
        {"name": font.name, "path": font.url, "descriptors": font.descriptors}
        for font in project.fonts
    ])
    return f"""import {{ loadPyodide }} from {pyodide_url};
import {{ installPygletEmscripten }} from "./pyglet_emscripten.js";

const status = document.getElementById("pygletStatus");

function setStatus(message) {{
  if (status) status.textContent = message;
}}

async function download(pyodide, url, destination) {{
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Failed to download ${{url}}: HTTP ${{response.status}}`);
  pyodide.FS.writeFile(destination, new Uint8Array(await response.arrayBuffer()));
}}

async function preloadFonts(fonts) {{
  await Promise.all(fonts.map(async font => {{
    const source = `url(${{JSON.stringify(font.path)}})`;
    const loaded = new FontFace(font.name, source, font.descriptors);
    await loaded.load();
    document.fonts.add(loaded);
    await document.fonts.load(`16px ${{JSON.stringify(font.name)}}`);
  }}));
}}

async function main() {{
  const entrypoint = {entrypoint_json};
  const fonts = {fonts_json};
  const pyodide = await loadPyodide();
  await installPygletEmscripten(pyodide);
  await preloadFonts(fonts);

  await download(pyodide, "pyglet.zip", "/pyglet.zip");
  await download(pyodide, "application.zip", "/application.zip");
  await pyodide.runPythonAsync(`
import os
import runpy
import sys
import zipfile

with zipfile.ZipFile("/pyglet.zip") as archive:
    archive.extractall("/")
with zipfile.ZipFile("/application.zip") as archive:
    archive.extractall("/app")

os.chdir("/app")
sys.path.insert(0, "/")
sys.path.insert(0, "/app")
runpy.run_path("/app/" + ${{JSON.stringify(entrypoint)}}, run_name="__main__")
  `);
  setStatus("");
}}

main().catch(error => {{
  console.error(error);
  setStatus(error?.stack || String(error));
}});
"""


class _Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def serve(directory: Path, host: str = "127.0.0.1", port: int = 8000, *, open_browser: bool = False) -> None:
    """Serve a built web project until interrupted."""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    with _Server((host, port), handler) as server:
        selected_port = server.server_address[1]
        url = f"http://{host}:{selected_port}/"
        print(f"Serving {directory} at {url}")  # noqa: T201
        if open_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")  # noqa: T201


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python tools/web.py", description=__doc__)
    parser.add_argument("--project", default="pyproject.toml", help="Project configuration file.")
    parser.add_argument("--entrypoint", help="Override the configured entrypoint.")
    parser.add_argument("--output", help="Override the configured output directory.")
    parser.add_argument("--resource", action="append", dest="resources", help="Resource glob; may be repeated.")
    parser.add_argument("--source", action="append", dest="sources", help="Python source glob; may be repeated.")
    parser.add_argument("--title", help="Override the generated page title.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build", help="Build the browser project.")
    discover_parser = subparsers.add_parser("discover", help="Report literal resource references.")
    discover_parser.add_argument("--missing", action="store_true", help="Only show references absent from the build.")
    serve_parser = subparsers.add_parser("serve", help="Build and serve the browser project.")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)
    serve_parser.add_argument("--open", action="store_true", dest="open_browser")
    serve_parser.add_argument("--no-build", action="store_true")
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    """Run the ``pyglet-web`` command-line tool."""
    args = _parser().parse_args(arguments)
    try:
        project = load_project(
            args.project,
            entrypoint=args.entrypoint,
            output=args.output,
            resources=args.resources,
            sources=args.sources,
            title=args.title,
        )
        if args.command == "build":
            output = build(project)
            print(f"Built web project: {output}")  # noqa: T201
        elif args.command == "serve":
            if not args.no_build:
                build(project)
            serve(project.output, args.host, args.port, open_browser=args.open_browser)
        else:
            packaged = _expand_patterns(project.root, project.resources, project.output)
            for asset in discover(project):
                candidate = (project.root / asset.name).resolve()
                if args.missing and candidate in packaged:
                    continue
                marker = "packaged" if candidate in packaged else "not declared"
                source = asset.source.relative_to(project.root)
                print(f"{asset.name} ({marker}) - {source}:{asset.line}")  # noqa: T201
    except (FileNotFoundError, OSError, RuntimeError, TypeError, ValueError) as exception:
        print(f"web.py: error: {exception}", file=sys.stderr)  # noqa: T201
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
