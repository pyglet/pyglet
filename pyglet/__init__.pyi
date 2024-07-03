
from dataclasses import dataclass

from . import app as app
from . import canvas as canvas
from . import clock as clock
from . import customtypes as customtypes
from . import event as event
from . import font as font
from . import gl as gl
from . import graphics as graphics
from . import gui as gui
from . import image as image
from . import input as input
from . import lib as lib
from . import math as math
from . import media as media
from . import model as model
from . import resource as resource
from . import shapes as shapes
from . import sprite as sprite
from . import text as text
from . import window as window

version: str
MIN_PYTHON_VERSION: tuple[int, int]
MIN_PYTHON_VERSION_STR: str
compat_platform: str
env: str
value: str

@dataclass
class Options:
    ...

options: Options
