# Pyglet Pyodide example

This is a minimal browser project built with pyglet's web-packaging tool.
The `pyproject.toml` configuration requires Python 3.11 or newer, which
includes the standard-library TOML reader. With Python 3.10, install the
optional reader first:

```console
python -m pip install tomli
```

From the pyglet source checkout, build it with:

```console
python tools/web.py --project tools/web_example/pyproject.toml build
```

Or build it and serve the result locally:

```console
python tools/web.py --project tools/web_example/pyproject.toml serve --open
```

The generated application is written to `dist/`. It includes the application
source, pyglet, the Pyodide launcher, and pyglet's Emscripten bridge.

`web/` is copied to the output unchanged. This example's `web/index.html` and
`web/dev_style.css` show how to customize the page; the index must load
`pyglet-web.js`. Add application assets under `resources` in `pyproject.toml`.

Each `sources` and `resources` entry may be a file, a glob, or a directory.
Directories are included recursively. For example:

```toml
sources = ["example.py", "game"]
resources = ["assets", "levels/**/*.json"]
```

This includes every file below `game/` and `assets/`, as well as JSON files
below `levels/`. Source and resource files are placed in `application.zip` at
their project-relative paths; `web/` files instead remain normal browser files.

A recommended project layout is:

```text
my-game/
├── pyproject.toml
├── main.py
├── game/                 # additional Python modules
│   └── state.py
├── assets/               # pyglet resources: images, audio, data, shaders
│   ├── images/
│   └── sounds/
└── web/                  # browser-owned files: HTML, CSS, JS, fonts
    ├── index.html
    ├── style.css
    └── fonts/
        └── game.woff2
```

The matching configuration is:

```toml
[tool.pyglet.web]
entrypoint = "main.py"
sources = ["main.py", "game"]
resources = ["assets"]

[[tool.pyglet.web.fonts]]
name = "Game Font"
path = "fonts/game.woff2"
```

Here, `assets/` is packaged for Python resource loading, while `web/` is
copied directly into the browser build. Font paths are relative to `web/`.

To preload a browser font, place it below `web/` and add a
`[[tool.pyglet.web.fonts]]` table with its family name and web-relative path.
The launcher waits for every configured font before it starts `example.py`.

You can also use the tool without a `pyproject.toml`. First change from the
repository root into this example directory, then provide the same values as
command-line options:

```console
cd tools/web_example
python ../web.py --entrypoint example.py --output dist --source example.py build
python ../web.py --entrypoint example.py --output dist --source example.py serve --open
```

Repeat `--source` and `--resource` for each additional source or asset pattern.
