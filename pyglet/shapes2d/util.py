import math
from typing import List

from pyglet.customtypes import *
from pyglet.extlibs.poly_decomp import polygonQuickDecomp
from pyglet.math import Vec2


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


def is_convex(polygon: List[Point2D]) -> bool:
    """Return ``True`` if a polygon is convex."""
    if len(polygon) <= 4:
        return True
    polygon += [polygon[0], polygon[1]]
    flag = None
    for i in range(len(polygon) - 2):
        u = Vec2(*polygon[i + 1]) - Vec2(*polygon[i])
        v = Vec2(*polygon[i + 2]) - Vec2(*polygon[i])
        # Cross product between Vec2.
        n = math.copysign(1, u[0] * v[1] - u[1] * v[0])
        if flag is None:
            flag = n
        if n != flag:
            return False
    return True


def sat(polygon1: List[Point2D], polygon2: List[Point2D]) -> bool:
    """An algorithm to detect whether two polygons intersect or not.."""

    def _sat(polygon1: List[Point2D], polygon2: List[Point2D]) -> bool:
        # Calculate normals of all edges
        polygon1 += [polygon1[0]]
        polygon2 += [polygon2[0]]
        normals = [
            (Vec2(*polygon1[i]) - Vec2(*polygon1[i - 1]))
            for i in range(1, len(polygon1))
        ]
        normals += [
            (Vec2(*polygon2[i]) - Vec2(*polygon2[i - 1]))
            for i in range(1, len(polygon2))
        ]
        normals = [Vec2(-vec.y, vec.x).normalize() for vec in normals]
        for normal in normals:
            # Get edge projections of polygon1
            proj1 = []
            for point in polygon1:
                proj1.append(normal.dot(Vec2(*point)))
            # Get edge projections of polygon2
            proj2 = []
            for point in polygon2:
                proj2.append(normal.dot(Vec2(*point)))
            if not (max(proj1) > min(proj2) and max(proj2) > min(proj1)):
                return False
        return True

    assert len(polygon1) >= 3 and len(polygon2) >= 3
    if not is_convex(polygon1):
        polygon1 = polygonQuickDecomp(polygon1)
    else:
        polygon1 = [polygon1]
    if not is_convex(polygon2):
        polygon2 = polygonQuickDecomp(polygon2)
    else:
        polygon2 = [polygon2]
    for part1 in polygon1:
        for part2 in polygon2:
            if _sat(part1, part2):
                return True
    return False


__all__ = ("point_in_polygon", "is_convex", "sat")
