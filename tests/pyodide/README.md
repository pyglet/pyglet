# Automated Pyodide tests

This directory contains the internal browser-test infrastructure. It copies the
normal `tests/` package, including `tests/data`, into a temporary browser
project and runs pytest inside Pyodide with a real WebGL2 canvas in headless
Chromium. The selected suite includes:

- Backend-agnostic tests from `tests/unit/`.
- Backend-agnostic top-level tests from `tests/integration/graphics/`.
- WebGL-specific tests from `tests/integration/graphics/webgl/`.
- Browser-platform tests from `tests/integration/platform/pyodide/`.

Backend-specific OpenGL and GL2 subdirectories, native OS integration tests,
and application/event-loop integration tests are not selected in the Pyodide
run. The browser owns Pyodide's asynchronous event loop, so repeatedly starting
and stopping it is intentionally outside this suite's current scope.

The supported Pyodide version is recorded as `pyglet.PYODIDE_VERSION`. It
includes [`pytest` as a loadable package](https://pyodide.org/en/stable/usage/packages-in-pyodide.html).
Pyodide also maintains
[`pytest-pyodide`](https://pyodide.org/en/stable/development/testing.html) for
host-side browser fixtures. This runner retains Playwright because pyglet
already used it for its WebGL browser check.

Install the local test driver once:

```console
python -m pip install playwright
python -m playwright install chromium
```

Run the Pyodide suite from the repository root:

```console
python tests/pyodide/run_pyodide_tests.py --clean
```

Use `--test-dir` to point at another complete pyglet tests directory.
The first run needs network access to download Pyodide and its `pillow` and
`pytest` packages. Browser output is forwarded to the terminal, and a non-zero
pytest exit code fails the command.

The normal `pytest tests` command does not collect directories named `webgl`;
those modules depend on the browser-only `js` module. Pyodide platform tests
are selected explicitly by the browser runner.
