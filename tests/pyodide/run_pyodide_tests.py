"""Build and run pyglet's Pyodide test suite in Chromium."""
from __future__ import annotations

import argparse
from pathlib import Path

from browser_harness import resolve_path, run_webgl_check, serve_directory
from project_builder import build_pyodide_project, zip_folder

DEFAULT_TEST_DIR = "tests"
DEFAULT_OUTPUT_DIR = ".pyodide_test_build"
DEFAULT_PYGLET_FOLDER = "pyglet"
TEST_SUPPORT_FILES = ("index.html", "script.js")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run unit, platform, and WebGL integration tests inside Pyodide.",
    )
    parser.add_argument("--test-dir", default=DEFAULT_TEST_DIR, help="Path to pyglet's tests directory.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Generated browser project directory.")
    parser.add_argument("--pyglet-folder", default=DEFAULT_PYGLET_FOLDER, help="Path to the pyglet source package.")
    parser.add_argument("--host", default="127.0.0.1", help="Host for the temporary HTTP server.")
    parser.add_argument("--port", type=int, default=0, help="Server port; 0 selects a free port.")
    parser.add_argument("--timeout-seconds", type=int, default=300, help="Timeout waiting for pytest to finish.")
    parser.add_argument("--settle-seconds", type=int, default=1, help="Wait for late browser errors after pytest.")
    parser.add_argument("--clean", action="store_true", help="Delete the generated project before rebuilding it.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    runner_dir = Path(__file__).resolve().parent
    repo_root = runner_dir.parents[1]
    test_dir = resolve_path(args.test_dir, repo_root).resolve()
    output_dir = resolve_path(args.output_dir, repo_root).resolve()
    pyglet_folder = resolve_path(args.pyglet_folder, repo_root).resolve()
    runner = Path(__file__).resolve().with_name("pytest_runner.py")

    if not test_dir.is_dir():
        raise FileNotFoundError(f"Test directory not found: {test_dir}")

    build_pyodide_project(
        script_path=runner.parent,
        script_filename=runner.name,
        resource_list=[],
        pyglet_folder=pyglet_folder,
        output_dir=output_dir,
        clean=args.clean,
        support_files=TEST_SUPPORT_FILES,
        support_dir=runner.parent,
    )
    zip_folder(
        test_dir,
        output_dir / "tests.zip",
        exclude_paths=(
            output_dir,
            runner_dir,
        ),
    )

    with serve_directory(output_dir, args.host, args.port) as server:
        selected_port = server.server_address[1]
        url = f"http://{args.host}:{selected_port}/index.html"
        print(f"Running Pyodide pytest suite at: {url}")
        run_webgl_check(
            url,
            timeout_seconds=args.timeout_seconds,
            settle_seconds=args.settle_seconds,
            success_prefix="Pytest Exit Code: 0",
        )


if __name__ == "__main__":
    main()
