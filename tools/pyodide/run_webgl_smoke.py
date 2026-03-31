from __future__ import annotations

import argparse
import functools
import http.server
import socketserver
import threading
from contextlib import contextmanager
from pathlib import Path

from gen_pyodide_project import generate_pyodide_project

DEFAULT_SCRIPT = "tools/pyodide/example.py"
DEFAULT_RESOURCE = "examples/resources/pyglet.png"
DEFAULT_OUTPUT_DIR = "tools/pyodide/.smoke_build"
DEFAULT_PYGLET_FOLDER = "pyglet"


def resolve_path(path: str, base: Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else (base / candidate)


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        return


@contextmanager
def serve_directory(path: Path, host: str, port: int):
    handler_class = functools.partial(QuietHTTPRequestHandler, directory=str(path))
    server = ReusableTCPServer((host, port), handler_class)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def load_playwright():
    try:
        from playwright.sync_api import TimeoutError as playwright_timeout_error
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - runtime dependency check.
        raise SystemExit(
            "Missing dependency: playwright. Install with `pip install playwright` and then run "
            "`python -m playwright install chromium`."
        ) from exc
    return sync_playwright, playwright_timeout_error


def run_webgl_smoke(url: str, timeout_seconds: int, settle_seconds: int) -> None:
    errors: list[str] = []
    sync_playwright, playwright_timeout_error = load_playwright()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--use-gl=angle", "--use-angle=swiftshader"],
        )
        page = browser.new_page()

        page.on(
            "console",
            lambda msg: errors.append(f"console.error: {msg.text.strip()}") if msg.type == "error" else None,
        )
        page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))

        response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_seconds * 1000)
        if response is None:
            errors.append("No HTTP response from the smoke test page.")
        elif response.status >= 400:
            errors.append(f"Unexpected HTTP status for smoke test page: {response.status}")

        try:
            page.wait_for_function(
                """() => {
                    const output = document.getElementById("output");
                    if (!output) return false;
                    const text = (output.innerText || "").trim();
                    return text.startsWith("Pyglet Version:") || text.startsWith("Error loading script:");
                }""",
                timeout=timeout_seconds * 1000,
            )
        except playwright_timeout_error:
            errors.append("Timed out waiting for Pyodide output to report success/error.")

        output_text = page.evaluate(
            '() => (document.getElementById("output")?.innerText || "").trim()',
        )
        if output_text.startswith("Error loading script:"):
            errors.append(output_text)
        elif not output_text.startswith("Pyglet Version:"):
            errors.append(f"Unexpected output text: {output_text!r}")

        context_state = page.evaluate(
            """() => {
                const canvas = document.getElementById("pygletCanvas");
                if (!canvas) return "missing-canvas";
                return canvas.getContext("webgl2") ? "webgl2-ok" : "missing-webgl2";
            }""",
        )
        if context_state != "webgl2-ok":
            errors.append(f"WebGL context check failed: {context_state}")

        if settle_seconds > 0:
            page.wait_for_timeout(settle_seconds * 1000)

        browser.close()

    if errors:
        unique_errors = list(dict.fromkeys(errors))
        details = "\n- ".join(unique_errors)
        raise RuntimeError(f"WebGL smoke test failed:\n- {details}")

    print("WebGL smoke test passed.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Pyodide example and run a headless WebGL smoke test against it.",
    )
    parser.add_argument("--script", default=DEFAULT_SCRIPT, help="Python script to run in browser.")
    parser.add_argument(
        "--resource",
        dest="resources",
        action="append",
        default=None,
        help="Resource file to include. Can be passed multiple times.",
    )
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory for generated project.")
    parser.add_argument("--pyglet-folder", default=DEFAULT_PYGLET_FOLDER, help="Path to pyglet source folder.")
    parser.add_argument("--host", default="127.0.0.1", help="Host for the local HTTP server.")
    parser.add_argument("--port", type=int, default=0, help="Port for local HTTP server. Use 0 for auto-select.")
    parser.add_argument("--timeout-seconds", type=int, default=180, help="Timeout waiting for page readiness.")
    parser.add_argument("--settle-seconds", type=int, default=3, help="Extra wait time for late async errors.")
    parser.add_argument("--clean", action="store_true", help="Delete output directory before generating files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]

    script = resolve_path(args.script, repo_root).resolve()
    output_dir = resolve_path(args.output_dir, repo_root).resolve()
    pyglet_folder = resolve_path(args.pyglet_folder, repo_root).resolve()
    resource_paths = args.resources if args.resources is not None else [DEFAULT_RESOURCE]
    resources = [str(resolve_path(path, repo_root).resolve()) for path in resource_paths]

    generate_pyodide_project(
        script_path=script.parent,
        script_filename=script.name,
        resource_list=resources,
        pyglet_folder=pyglet_folder,
        pyodide_folder=output_dir,
        launch_browser_after=False,
        port=args.port,
        clean=args.clean,
    )

    with serve_directory(output_dir, args.host, args.port) as server:
        selected_port = server.server_address[1]
        url = f"http://{args.host}:{selected_port}/index.html?script={script.stem}"
        print(f"Running WebGL smoke test at: {url}")
        run_webgl_smoke(url, timeout_seconds=args.timeout_seconds, settle_seconds=args.settle_seconds)


if __name__ == "__main__":
    main()
