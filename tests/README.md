# Test organization

Follow these rules when adding or changing tests, including tests written by AI
agents. Check the existing tests and fixtures before creating a new file.

## Unit tests and integration tests

- Put isolated tests in `tests/unit/`. These test logic without calling real
  operating system services, native platform APIs, graphics contexts, audio
  drivers, or other external runtime resources. Use mocks or stubs where needed,
  and check that imports and fixtures do not initialize real resources either.
- Tests that access those resources belong in the relevant folder under
  `tests/integration/`, even if they test only one method. For example, native
  platform calls belong in `platform/` or `libs/`, real window behavior in
  `window/`, graphics operations in `graphics/`, and audio driver behavior in
  `media/`. Follow the existing organization for the component being tested.
- Tests requiring human interaction or visual judgment belong in
  `tests/interactive/`.

Placement depends on what the test actually uses, including setup and fixtures.
A small test is not automatically a unit test, and mocking one dependency does
not make a test isolated if another dependency still calls the OS or a driver.

## Graphics tests

- Tests making backend-specific API calls belong under
  `tests/integration/graphics/<api>/`, such as `opengl/`, `gl2/`, or `webgl/`.
  This includes tests that call backend APIs during setup, verification, or
  cleanup.
- Keep backend-agnostic graphics integration tests directly in
  `tests/integration/graphics/`. Exercise the shared pyglet graphics interfaces
  without calling a particular backend's API.
- Pure graphics-related logic that needs no real graphics context or driver can
  still be tested in `tests/unit/`.

A test passing on desktop OpenGL or GL2 does not imply that it works on GLES2,
GLES3, or WebGL. Restrict tests to the APIs they actually support. Backend folder
placement and runtime restrictions serve different purposes; use both when
appropriate.

## Platform and graphics restrictions

Use the decorators in [annotations.py](annotations.py) where applicable:

- `@require_platform(...)` to run only on supported platforms.
- `@skip_platform(...)` to exclude specific platforms.
- `@require_graphics_api(...)` to run only with supported graphics backends.
- `@skip_graphics_api(...)` to exclude specific graphics backends.

Use `Platform` constants and `GraphicsAPIGroups` when their members match the
test's requirements, or pass explicit backend names. For example:

```python
from tests.annotations import Platform, require_graphics_api, skip_platform


@skip_platform(Platform.EMSCRIPTEN)
@require_graphics_api(['gl2'])
def test_gl2_specific_behavior():
    ...
```

Apply shared restrictions to a class or module when appropriate. Skip known
unsupported configurations explicitly; do not catch arbitrary failures and turn
them into skips. When adding shared integration coverage, check that the intended
runners actually collect it, including the explicit selection in
`tests/pyodide/pytest_runner.py` when browser coverage is relevant.

## Keep test files focused

Group tests by the class or module they exercise. Prefer extending an existing
test file over creating a separate file for each regression or individual test.
Create a new file only when it gives the suite a useful, distinct home for the
coverage.

Larger modules may be split by behavior when there are many tests, the behaviors
are sufficiently different, or they require distinct custom fixtures. Keep those
splits deliberate and their names descriptive. Reuse suitable fixtures and keep
specialized fixtures close to the tests that need them. Always release windows,
contexts, drivers, and other resources, including when an assertion fails.
