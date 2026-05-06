from __future__ import annotations

import os.path
import re
import xml.dom.minidom

import pyglet
from pyglet.enums import BlendFactor, GeometryMode
from pyglet.graphics import Group, Shader, ShaderGroup, ShaderProgram
from pyglet.graphics.api.base import SurfaceContext
from pyglet.graphics.api.gl import (
    GL_DONT_CARE,
    GL_LINE_SMOOTH,
    GL_LINE_SMOOTH_HINT,
    glDisable,
    glEnable,
    glHint,
)
from pyglet.graphics.state import State


_VERTEX_SOURCE = """#version 330 core
in vec2 position;

uniform WindowBlock
{
    mat4 projection;
    mat4 view;
} window;

void main()
{
    gl_Position = window.projection * window.view * vec4(position, 0.0, 1.0);
}
"""

_FRAGMENT_SOURCE = """#version 330 core
out vec4 final_color;

void main()
{
    final_color = vec4(1.0, 0.0, 0.0, 1.0);
}
"""


class LineSmoothState(State):
    sets_state = True
    unsets_state = True

    def set_state(self, ctx: SurfaceContext) -> None:
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_DONT_CARE)

    def unset_state(self, ctx: SurfaceContext) -> None:
        glDisable(GL_LINE_SMOOTH)


class Curve:
    PATH_RE = re.compile(r'([MLHVCSQTAZ])([^MLHVCSQTAZ]*)', re.IGNORECASE)
    INT = r'([+-]?\d+)'
    FLOAT = r'(?:[\s,]*)([+-]?\d+(?:\.\d+)?)'

    HANDLERS = {}

    def handle(self, rx, types, HANDLERS=HANDLERS):
        def register(function):
            HANDLERS[self] = (rx and re.compile(rx), function, types)
            return function

        return register

    def __init__(self, spec):
        self.start = None
        self.current = None
        self.last_control = None
        self.min_x = self.min_y = self.max_x = self.max_y = None
        self.segments = []

        for cmd, value in self.PATH_RE.findall(spec):
            if not cmd:
                continue
            rx, handler, types = self.HANDLERS[cmd.upper()]
            if rx is None:
                handler(self, cmd)
                continue
            v = []
            for fields in rx.findall(value):
                if not isinstance(fields, tuple):
                    fields = (fields,)
                v.append([types[i](e) for i, e in enumerate(fields)])
            handler(self, cmd, v)

    def _determine_rect(self, x, y):
        y = -y
        if self.min_x is None:
            self.min_x = self.max_x = x
            self.min_y = self.max_y = y
            return
        if self.min_x > x:
            self.min_x = x
        elif self.max_x < x:
            self.max_x = x
        if self.min_y > y:
            self.min_y = y
        elif self.max_y < y:
            self.max_y = y

    def _append_line(self, x1, y1, x2, y2):
        self.segments.append((x1, -y1, x2, -y2))
        self._determine_rect(x1, y1)
        self._determine_rect(x2, y2)

    @handle('M', FLOAT * 2, (float, float))
    def moveto(self, cmd, points):
        points = [list(map(float, point)) for point in points]
        if not points:
            return
        self.start = self.current = points[0]
        self.last_control = None
        if len(points) > 1:
            self.lineto({'m': 'l', 'M': 'L'}[cmd], points[1:])

    @handle('L', FLOAT * 2, (float, float))
    def lineto(self, cmd, points):
        if self.current is None:
            return
        for point in points:
            cx, cy = self.current
            x, y = list(map(float, point))
            self._append_line(cx, cy, x, y)
            self.current = (x, y)
        self.last_control = None

    @handle('H', FLOAT, (float,))
    def horizontal_lineto(self, cmd, xvals):
        if self.current is None or not xvals:
            return
        cx, cy = self.current
        x = float(xvals[-1][0])
        self._append_line(cx, cy, x, cy)
        self.current = (x, cy)
        self.last_control = None

    @handle('V', FLOAT, (float,))
    def vertical_lineto(self, cmd, yvals):
        if self.current is None or not yvals:
            return
        cx, cy = self.current
        y = float(yvals[-1][0])
        self._append_line(cx, cy, cx, y)
        self.current = (cx, y)
        self.last_control = None

    @handle('Z', None, None)
    def closepath(self, cmd):
        if self.current is None or self.start is None:
            return
        cx, cy = self.current
        sx, sy = self.start
        self._append_line(cx, cy, sx, sy)
        self.current = self.start
        self.last_control = None

    @handle('C', FLOAT * 6, (float,) * 6)
    def curveto(self, cmd, control_points):
        if self.current is None:
            return
        last = None
        for entry in control_points:
            x1, y1, x2, y2, x, y = list(map(float, entry))
            cx, cy = self.current
            self.last_control = (x2, y2)
            self.current = (x, y)
            t = 0.0
            while t <= 1.0001:
                a = t
                a2 = a**2
                a3 = a**3
                b = 1 - t
                b2 = b**2
                b3 = b**3
                px = cx * b3 + 3 * x1 * b2 * a + 3 * x2 * b * a2 + x * a3
                py = cy * b3 + 3 * y1 * b2 * a + 3 * y2 * b * a2 + y * a3
                if last is not None:
                    self._append_line(last[0], last[1], px, py)
                last = (px, py)
                t += 0.01

    @handle('S', FLOAT * 4, (float,) * 4)
    def smooth_curveto(self, cmd, control_points):
        if self.current is None:
            return
        if self.last_control is None:
            self.last_control = self.current

        last = None
        for entry in control_points:
            x2, y2, x, y = list(map(float, entry))
            cx, cy = self.current
            lcx, lcy = self.last_control
            x1, y1 = cx + (cx - lcx), cy + (cy - lcy)

            self.last_control = (x2, y2)
            self.current = (x, y)

            t = 0.0
            while t <= 1.0001:
                a = t
                a2 = a**2
                a3 = a**3
                b = 1 - t
                b2 = b**2
                b3 = b**3
                px = cx * b3 + 3 * x1 * b2 * a + 3 * x2 * b * a2 + x * a3
                py = cy * b3 + 3 * y1 * b2 * a + 3 * y2 * b * a2 + y * a3
                if last is not None:
                    self._append_line(last[0], last[1], px, py)
                last = (px, py)
                t += 0.01

    @handle('Q', FLOAT * 4, (float,) * 4)
    def quadratic_curveto(self, cmd, control_points):
        raise NotImplementedError('not implemented')

    @handle('T', FLOAT * 2, (float,) * 2)
    def smooth_quadratic_curveto(self, cmd, control_points):
        raise NotImplementedError('not implemented')

    @handle('A', FLOAT * 3 + INT * 2 + FLOAT * 2, (float,) * 3 + (int,) * 2 + (float,) * 2)
    def elliptical_arc(self, cmd, parameters):
        raise NotImplementedError('not implemented')


class SVG:
    def __init__(self, filename, rect=None):
        self._rect = rect
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.translate_x = 0.0
        self.translate_y = 0.0

        self.batch = pyglet.graphics.Batch()
        self.shader = ShaderProgram(Shader(_VERTEX_SOURCE, "vertex"), Shader(_FRAGMENT_SOURCE, "fragment"))

        shader_group = ShaderGroup(self.shader)
        self.line_group = Group(parent=shader_group)
        self.line_group.set_blend(BlendFactor.SRC_ALPHA, BlendFactor.ONE_MINUS_SRC_ALPHA)
        self.line_group.add_state(LineSmoothState())

        dom = xml.dom.minidom.parse(filename)
        svg_tag = dom.documentElement
        if svg_tag.tagName != 'svg':
            raise ValueError(f'document is <{svg_tag.tagName}> instead of <svg>')

        self.objects = []
        for group_tag in svg_tag.getElementsByTagName('g'):
            for path_tag in group_tag.getElementsByTagName('path'):
                self.objects.append(Curve(path_tag.getAttribute('d')))

        self.min_x = min(o.min_x for o in self.objects if o.min_x is not None)
        self.max_x = max(o.max_x for o in self.objects if o.max_x is not None)
        self.min_y = min(o.min_y for o in self.objects if o.min_y is not None)
        self.max_y = max(o.max_y for o in self.objects if o.max_y is not None)

        if rect is None:
            self._rect = (
                self.min_x,
                self.min_y,
                self.max_x - self.min_x,
                self.max_y - self.min_y,
            )

        self.drawables = []
        self._build_vertex_lists()
        self.rect = self._rect

    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self, new_rect):
        self._rect = new_rect
        self.translate_x, self.translate_y, rw, rh = new_rect
        width = self.max_x - self.min_x
        height = self.max_y - self.min_y
        self.scale_x = abs(rw / width) if width else 1.0
        self.scale_y = abs(rh / height) if height else 1.0
        self._update_vertices()

    def _build_vertex_lists(self):
        for curve in self.objects:
            if not curve.segments:
                continue
            positions = []
            for x1, y1, x2, y2 in curve.segments:
                positions.extend((x1, y1, x2, y2))
            vertex_list = self.shader.vertex_list(
                len(positions) // 2,
                GeometryMode.LINES,
                self.batch,
                self.line_group,
                position=('f', positions),
            )
            self.drawables.append((curve, vertex_list))

    def _update_vertices(self):
        for curve, vertex_list in self.drawables:
            transformed = []
            for x1, y1, x2, y2 in curve.segments:
                transformed.extend((
                    (x1 - self.min_x) * self.scale_x + self.translate_x,
                    (y1 - self.min_y) * self.scale_y + self.translate_y,
                    (x2 - self.min_x) * self.scale_x + self.translate_x,
                    (y2 - self.min_y) * self.scale_y + self.translate_y,
                ))
            vertex_list.position[:] = transformed

    def draw(self):
        self.batch.draw()


window = pyglet.window.Window(width=600, height=300, resizable=True)

dirname = os.path.dirname(__file__)
svg = SVG(os.path.join(dirname, 'hello_world.svg'), rect=(0, 0, 600, 300))


@window.event
def on_draw():
    window.clear()
    svg.draw()


@window.event
def on_resize(w, h):
    svg.rect = (0, 0, w, h)


pyglet.app.run()
