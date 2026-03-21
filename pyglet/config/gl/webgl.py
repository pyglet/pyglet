from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import asdict
from pyglet.config import SurfaceConfig, WebGLConfig

if TYPE_CHECKING:
    from pyglet.window import BaseWindow, Any


def match(config: WebGLConfig, window: BaseWindow) -> WebGLSurfaceConfig:
    return WebGLSurfaceConfig(window, config, None)


class WebGLSurfaceConfig(SurfaceConfig):
    def __init__(self, window: BaseWindow, config: WebGLConfig, handle=None):
        for name, value in asdict(config).items():
            setattr(self, name, value)
        super().__init__(window, config, handle)

    def attributes(self) -> dict[str, Any]:
        # Only return the WebGL specific attributes
        return asdict(self.config)
