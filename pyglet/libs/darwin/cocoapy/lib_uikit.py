"""UIKit for iOS."""
from __future__ import annotations

import pyglet.lib

uikit = pyglet.lib.load_library(framework='UIKit')
quartzcore = pyglet.lib.load_library(framework='QuartzCore')
