"""UIKit for iOS."""
from __future__ import annotations

import pyglet.lib

UITouchTypeDirect = 0
UITouchTypeIndirect = 1
UITouchTypePencil = 2  # also UITouchTypeStylus
UITouchTypeIndirectPointer = 3

uikit = pyglet.lib.load_library(framework='UIKit')
quartzcore = pyglet.lib.load_library(framework='QuartzCore')
