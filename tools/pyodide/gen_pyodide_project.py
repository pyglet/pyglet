"""Build a browser-runnable project from the Pyodide user example.

This zips the pyglet source directory and selected resource files, then writes them to
a browser-ready output folder.
"""
from __future__ import annotations

import argparse
import os
import shutil
import socket
import webbrowser
import zipfile
from pathlib import Path
from typing import Sequence

# ==== Edit the below options
PYODIDE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PYODIDE_DIR.parents[1]
USER_EXAMPLE_DIR = PYODIDE_DIR / "user_example"

SCRIPT_PATH = USER_EXAMPLE_DIR
SCRIPT_FILENAME = "example.py"

# Resources you want to include with your script (relative from script_path)
RESOURCE_LIST = [
    str(REPO_ROOT / "examples/resources/pyglet.png"),
]

# The target path of the pyglet directory.
PYGLET_FOLDER = REPO_ROOT / "pyglet"

# The folder with your pyodide output.
PYODIDE_FOLDER = USER_EXAMPLE_DIR / ".build"

# Port to use for HTTP (by default, 8000)
PORT = 8000

# Launches default browser after this runs.
LAUNCH_BROWSER_AFTER = True

# ===========================================

ZIP_FILENAME = "pyglet.zip"
ZIP_RESOURCE_FILENAME = "resources.zip"
SOURCE_FILES = ("index.html", "script.js", "dev_style.css")
TEMPLATE_DIR = USER_EXAMPLE_DIR


def _resolve(path: str | Path, base: Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else (base / candidate)


def zip_list(path_list: list[str], filename: Path, script_path: Path) -> None:
    with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filepath in path_list:
            resource = Path(filepath)
            if resource.is_absolute():
                path = resource
            else:
                path = (script_path / resource).resolve()
                if not path.exists():
                    path = (Path.cwd() / resource).resolve()
            if not path.exists():
                raise FileNotFoundError(f"Resource file not found: {path}")
            zipf.write(path, path.name)
    print(f"Zipped {len(path_list)} resource files -> {filename}")


def zip_folder(folder: Path, zip_filename: Path) -> None:
    folder_name = folder.name
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder):
            for file in files:
                file_path = Path(root) / file
                arcname = Path(folder_name) / file_path.relative_to(folder)
                zipf.write(file_path, arcname.as_posix())
    print(f"Zipped {folder} -> {zip_filename}")


def copy_script(script_path: Path, script_filename: str, output_folder: Path) -> None:
    src = (script_path / script_filename).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Script file not found: {src}")
    dst = output_folder / script_filename
    shutil.copyfile(src, dst)
    print(f"{script_filename} copied to {dst}")


def copy_support_files(
        output_folder: Path,
        source_files: Sequence[str] = SOURCE_FILES,
        source_dir: Path = TEMPLATE_DIR,
) -> None:
    for name in source_files:
        src = source_dir / name
        dst = output_folder / name
        shutil.copyfile(src, dst)
        print(f"{name} copied to {dst}")


def is_server_running(port: int = PORT, host: str = "localhost") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((host, port)) == 0


def launch_browser(script: str, port: int = PORT, host: str = "localhost") -> None:
    url = f"http://{host}:{port}/index.html?script={Path(script).stem}"
    print(f"Opening browser to {url}")
    webbrowser.open(url)


def generate_pyodide_project(
        *,
        script_path: str | Path = SCRIPT_PATH,
        script_filename: str = SCRIPT_FILENAME,
        resource_list: list[str] | None = None,
        pyglet_folder: str | Path = PYGLET_FOLDER,
        pyodide_folder: str | Path = PYODIDE_FOLDER,
        launch_browser_after: bool = LAUNCH_BROWSER_AFTER,
        port: int = PORT,
        clean: bool = False,
        support_files: Sequence[str] = SOURCE_FILES,
        support_dir: str | Path = TEMPLATE_DIR,
) -> Path:
    cwd = Path.cwd()
    script_path_obj = _resolve(script_path, cwd).resolve()
    pyglet_folder_obj = _resolve(pyglet_folder, cwd).resolve()
    pyodide_folder_obj = _resolve(pyodide_folder, cwd).resolve()
    support_dir_obj = _resolve(support_dir, cwd).resolve()

    if not script_path_obj.exists():
        raise FileNotFoundError(f"Script path not found: {script_path_obj}")
    if not pyglet_folder_obj.exists():
        raise FileNotFoundError(f"Pyglet folder not found: {pyglet_folder_obj}")

    if clean and pyodide_folder_obj.exists():
        shutil.rmtree(pyodide_folder_obj)

    pyodide_folder_obj.mkdir(parents=True, exist_ok=True)

    resources = list(resource_list) if resource_list is not None else list(RESOURCE_LIST)
    zip_folder(pyglet_folder_obj, pyodide_folder_obj / ZIP_FILENAME)
    zip_list(resources, pyodide_folder_obj / ZIP_RESOURCE_FILENAME, script_path_obj)
    copy_script(script_path_obj, script_filename, pyodide_folder_obj)
    copy_support_files(pyodide_folder_obj, support_files, support_dir_obj)

    if port > 0:
        if not is_server_running(port):
            print(f"HTTP server not detected on {port}.")
        else:
            print(f"HTTP server already running on {port}.")
    else:
        print("HTTP server check skipped (port <= 0).")

    if launch_browser_after:
        launch_browser(script_filename, port=port)

    return pyodide_folder_obj


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the browser-runnable Pyodide user example.")
    parser.add_argument("--script-path", default=SCRIPT_PATH, help="Directory containing the Python script.")
    parser.add_argument("--script-filename", default=SCRIPT_FILENAME, help="Python script to copy into output.")
    parser.add_argument(
        "--resource",
        dest="resources",
        action="append",
        default=None,
        help="Resource file to include in resources.zip. May be passed multiple times.",
    )
    parser.add_argument("--pyglet-folder", default=PYGLET_FOLDER, help="Path to pyglet package folder.")
    parser.add_argument("--pyodide-folder", default=PYODIDE_FOLDER, help="Output folder to write browser files.")
    parser.add_argument("--port", type=int, default=PORT, help="Port to check/open browser on.")
    parser.add_argument("--clean", action="store_true", help="Delete output folder before generating files.")
    parser.add_argument(
        "--launch-browser",
        action="store_true",
        dest="launch_browser_after",
        default=LAUNCH_BROWSER_AFTER,
        help="Launch browser after generation.",
    )
    parser.add_argument(
        "--no-launch-browser",
        action="store_false",
        dest="launch_browser_after",
        help="Do not launch browser after generation.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    resources = args.resources if args.resources is not None else list(RESOURCE_LIST)
    generate_pyodide_project(
        script_path=args.script_path,
        script_filename=args.script_filename,
        resource_list=resources,
        pyglet_folder=args.pyglet_folder,
        pyodide_folder=args.pyodide_folder,
        launch_browser_after=args.launch_browser_after,
        port=args.port,
        clean=args.clean,
    )
