import math
from typing import List

from pyglet.customtypes import *
from pyglet.extlibs.poly_decomp import polygonQuickDecomp
from pyglet.math import Vec2


def rotate_point(center: Point2D, point: Point2D, angle: number) -> Point2D:
    prev_angle = math.atan2(point[1] - center[1], point[0] - center[0])
    now_angle = prev_angle + angle
    r = math.dist(point, center)
    return (center[0] + r * math.cos(now_angle), center[1] + r * math.sin(now_angle))


def point_in_polygon(polygon: List[Point2D], point: Point2D) -> bool:
    """Raycasting Algorithm to find out whether a point is in a given polygon.

    Copy from https://www.algorithms-and-technologies.com/point_in_polygon/python
    """
    odd = False
    i = 0
    j = len(polygon) - 1
    while i < len(polygon) - 1:
        i = i + 1
        if ((polygon[i][1] > point[1]) != (polygon[j][1] > point[1])) and (
            point[0]
            < (
                (polygon[j][0] - polygon[i][0])
                * (point[1] - polygon[i][1])
                / (polygon[j][1] - polygon[i][1])
            )
            + polygon[i][0]
        ):
            odd = not odd
        j = i
    return odd


def sat(polygon1: List[Point2D], polygon2: List[Point2D]) -> bool:
    """An algorithm to detect whether two polygons intersect or not.."""
    assert len(polygon1) >= 3 and len(polygon2) >= 3
    if not is_convex(polygon1):
        polygon1 = polygonQuickDecomp(polygon1)
    else:
        polygon1 = [polygon1]
    if not is_convex(polygon2):
        polygon2 = polygonQuickDecomp(polygon2)
    else:
        polygon2 = [polygon2]
    return False


def is_convex(polygon: List[Point2D]) -> bool:
    """Return ``True`` if a polygon is convex."""
    if len(polygon) <= 4:
        return True
    polygon += [polygon[0], polygon[1]]
    flag = None
    for i in range(len(polygon)):
        u = Vec2(*polygon[i + 1]) - Vec2(*polygon[i])
        v = Vec2(*polygon[i + 2]) - Vec2(*polygon[i])
        if flag is None:
            flag = math.copysign(1, u[0] * v[1] - u[1] * v[0])
        n = math.copysign(1, u[0] * v[1] - u[1] * v[0])
        if n != flag:
            return False
    return True


__all__ = ("rotate_point", "point_in_polygon", "sat", "is_convex")
