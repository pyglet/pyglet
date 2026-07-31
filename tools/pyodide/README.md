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

## Automated WebGL tests

The files in `test_runner/` are internal test infrastructure. They copy
`tests/webgl/test_*.py` into a temporary browser project and run pytest inside
Pyodide against a real WebGL2 canvas in headless Chromium.

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

Run the WebGL suite from the repository root:

```console
python tools/pyodide/test_runner/run_webgl_tests.py --clean
```

Use `--test-dir` to point at another directory containing `test_*.py` files.
The first run needs network access to download Pyodide and its `pillow` and
`pytest` packages. Browser output is forwarded to the terminal, and a non-zero
pytest exit code fails the command.

The normal `pytest tests` command does not collect `tests/webgl`; those modules
depend on the browser-only `js` module.
