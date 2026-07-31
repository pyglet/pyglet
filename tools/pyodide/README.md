# Pyodide tooling

This directory has two intentionally separate uses:

```text
tools/pyodide/
├── user_example/   # Small example intended for pyglet users
└── test_runner/    # Automated Playwright and pytest infrastructure
```

`gen_pyodide_project.py` is the shared packaging helper. It copies the selected
Python entry point and HTML/JavaScript support files into a browser-runnable
build directory.

## User example

The files in `user_example/` demonstrate how to load pyglet and an application
into Pyodide. They contain no pytest or CI behavior.

From the repository root, generate the example and serve it locally:

```console
python tools/pyodide/gen_pyodide_project.py --clean --no-launch-browser
python -m http.server 8000 --directory tools/pyodide/user_example/.build
```

Then open <http://localhost:8000/>. Edit `user_example/example.py` to experiment
with another pyglet application. Additional resource files can be included by
passing `--resource` once for each file.

## Automated Pyodide tests

The files in `test_runner/` are internal test infrastructure. They copy the
normal `tests/` package, including `tests/data`, into a temporary browser
project and run pytest inside Pyodide with a real WebGL2 canvas in headless
Chromium. The selected suite includes:

- Backend-agnostic tests from `tests/unit/`.
- Backend-agnostic top-level tests from `tests/integration/graphics/`.
- WebGL-specific tests from `tests/integration/graphics/webgl/`.
- Browser-platform tests from `tests/integration/platform/pyodide/`.

Backend-specific OpenGL and GL2 subdirectories, native OS integration tests,
and application/event-loop integration tests are not selected in the Pyodide
run. The browser owns Pyodide's asynchronous event loop, so repeatedly starting
and stopping it is intentionally outside this suite's current scope.

Pyodide 0.27.7 includes
[`pytest` as a loadable package](https://pyodide.org/en/0.27.7/usage/packages-in-pyodide.html).
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
python tools/pyodide/test_runner/run_pyodide_tests.py --clean
```

Use `--test-dir` to point at another complete pyglet tests directory.
The first run needs network access to download Pyodide and its `pillow` and
`pytest` packages. Browser output is forwarded to the terminal, and a non-zero
pytest exit code fails the command.

The normal `pytest tests` command does not collect directories named `webgl`;
those modules depend on the browser-only `js` module. Pyodide platform tests
are selected explicitly by the browser runner.
