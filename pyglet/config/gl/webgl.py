from __future__ import annotations

from typing import Any, TYPE_CHECKING
from dataclasses import asdict
from pyglet.config import SurfaceConfig, WebGLUserConfig

if TYPE_CHECKING:
    from pyglet.window.emscripten import EmscriptenWindow


def match(config: WebGLUserConfig, window: EmscriptenWindow) -> WebGLSurfaceConfig:
    return WebGLSurfaceConfig(window, config, None)


class WebGLSurfaceConfig(SurfaceConfig['EmscriptenWindow']):
    config: WebGLUserConfig

    def __init__(self, window: EmscriptenWindow, config: WebGLUserConfig, handle: Any = None) -> None:
        for name, value in asdict(config).items():
            setattr(self, name, value)
        super().__init__(window, config, handle)

    @property
    def attributes(self) -> dict[str, Any]:
        # Only return the WebGL specific attributes
        return asdict(self.config)
