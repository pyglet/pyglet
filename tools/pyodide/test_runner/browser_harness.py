from __future__ import annotations

import functools
import http.server
import socketserver
import threading
from contextlib import contextmanager
from pathlib import Path


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


def run_webgl_check(
        url: str,
        timeout_seconds: int,
        settle_seconds: int,
        success_prefix: str = "Pyglet Version:",
) -> None:
    errors: list[str] = []
    sync_playwright, playwright_timeout_error = load_playwright()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--use-gl=angle", "--use-angle=swiftshader"],
        )
        page = browser.new_page()

        def handle_console(msg) -> None:
            text = msg.text.strip()
            if text:
                print(f"browser.{msg.type}: {text}")
            if msg.type == "error":
                errors.append(f"console.error: {text}")

        page.on("console", handle_console)
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
                    return text !== "Loading...";
                }""",
                timeout=timeout_seconds * 1000,
            )
        except playwright_timeout_error:
            errors.append("Timed out waiting for Pyodide output to report success/error.")

        output_text = page.evaluate(
            '() => (document.getElementById("output")?.innerText || "").trim()',
        )
        if output_text.startswith("Error loading"):
            errors.append(output_text)
        elif not output_text.startswith(success_prefix):
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
        raise RuntimeError(f"WebGL browser check failed:\n- {details}")

    print("WebGL browser check passed.")
