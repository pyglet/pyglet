"""Build the browser project used by the Pyodide test runner."""
from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path
from typing import Sequence


PYGLET_ZIP_FILENAME = "pyglet.zip"
RESOURCES_ZIP_FILENAME = "resources.zip"


def _resolve(path: str | Path, base: Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else base / candidate


def zip_list(path_list: Sequence[str], filename: Path, base_dir: Path) -> None:
    with zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for filepath in path_list:
            resource = _resolve(filepath, base_dir).resolve()
            if not resource.exists():
                raise FileNotFoundError(f"Resource file not found: {resource}")
            zip_file.write(resource, resource.name)
    print(f"Zipped {len(path_list)} resource files -> {filename}")


def zip_folder(folder: Path, zip_filename: Path, exclude_paths: Sequence[Path] = ()) -> None:
    folder_name = folder.name
    excluded = {path.resolve() for path in exclude_paths}
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, directories, files in os.walk(folder):
            root_path = Path(root).resolve()
            directories[:] = [
                directory
                for directory in directories
                if (root_path / directory).resolve() not in excluded
            ]
            if root_path in excluded:
                continue
            for file in files:
                file_path = Path(root) / file
                arcname = Path(folder_name) / file_path.relative_to(folder)
                zip_file.write(file_path, arcname.as_posix())
    print(f"Zipped {folder} -> {zip_filename}")


def build_pyodide_project(
        *,
        script_path: Path,
        script_filename: str,
        resource_list: Sequence[str],
        pyglet_folder: Path,
        output_dir: Path,
        clean: bool,
        support_files: Sequence[str],
        support_dir: Path,
) -> Path:
    script_path = script_path.resolve()
    pyglet_folder = pyglet_folder.resolve()
    output_dir = output_dir.resolve()
    support_dir = support_dir.resolve()

    if not script_path.is_dir():
        raise FileNotFoundError(f"Script path not found: {script_path}")
    if not pyglet_folder.is_dir():
        raise FileNotFoundError(f"Pyglet folder not found: {pyglet_folder}")

    if clean and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    zip_folder(pyglet_folder, output_dir / PYGLET_ZIP_FILENAME)
    emscripten_javascript = pyglet_folder / "libs" / "emscripten" / "pyglet_emscripten.js"
    if not emscripten_javascript.is_file():
        message = f"Emscripten JavaScript module not found: {emscripten_javascript}"
        raise FileNotFoundError(message)
    shutil.copyfile(emscripten_javascript, output_dir / emscripten_javascript.name)
    zip_list(resource_list, output_dir / RESOURCES_ZIP_FILENAME, script_path)

    script = script_path / script_filename
    if not script.is_file():
        raise FileNotFoundError(f"Script file not found: {script}")
    shutil.copyfile(script, output_dir / script_filename)
    print(f"{script_filename} copied to {output_dir / script_filename}")

    for filename in support_files:
        source = support_dir / filename
        if not source.is_file():
            raise FileNotFoundError(f"Support file not found: {source}")
        shutil.copyfile(source, output_dir / filename)
        print(f"{filename} copied to {output_dir / filename}")

    return output_dir
