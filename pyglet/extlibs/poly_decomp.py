# Polygon decomposition helpers.
# Copied from https://github.com/wsilva32/poly_decomp.py
#
# LICENSE (MIT)
#
# Copyright (c) 2016 Will Silva
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import math
from typing import List

from pyglet.customtypes import Point2D

def triangleArea(a, b, c):
    """Calculates the area of a triangle spanned by three points.
    Note that the area will be negative if the points are not given in counter-clockwise order.

    Keyword arguments:
    a -- First point
    b -- Second point
    c -- Third point

    Returns:
    Area of triangle
    """
    return ((b[0] - a[0])*(c[1] - a[1]))-((c[0] - a[0])*(b[1] - a[1]))

def isLeft(a, b, c):
    return triangleArea(a, b, c) > 0

def isLeftOn(a, b, c):
    return triangleArea(a, b, c) >= 0

def isRight(a, b, c):
    return triangleArea(a, b, c) < 0

def isRightOn(a, b, c):
    return triangleArea(a, b, c) <= 0

def sqdist(a, b):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    return dx * dx + dy * dy

def polygonAt(polygon, i):
    """Gets a vertex at position i on the polygon.
    It does not matter if i is out of bounds.

    Keyword arguments:
    polygon -- The polygon
    i -- Position desired on the polygon

    Returns:
    Vertex at position i
    """
    s = len(polygon)
    return polygon[i % s]

def polygonAppend(polygon, poly, start, end):
    """Grabs points at indicies `start` to `end` from `poly`
    and appends them to `polygon`

    Keyword arguments:
    polygon -- The destination polygon
    poly -- The source polygon
    start -- Starting source index
    end -- Ending source index (not included in the slice)

    """
    for i in range(start, end):
        polygon.append(poly[i])

def polygonIsReflex(polygon, i):
    """Checks if a point in the polygon is a reflex point.

    Keyword arguments:
    polygon -- The polygon
    i -- index of point to check

    Returns:
    True is point is a reflex point

    """
    return isRight(polygonAt(polygon, i - 1), polygonAt(polygon, i), polygonAt(polygon, i + 1))

def getIntersectionPoint(p1, p2, q1, q2):
    """Gets the intersection point 

    Keyword arguments:
    p1 -- The start vertex of the first line segment.
    p2 -- The end vertex of the first line segment.
    q1 -- The start vertex of the second line segment.
    q2 -- The end vertex of the second line segment.

    Returns:
    The intersection point.

    """
    a1 = p2[1] - p1[1]
    b1 = p1[0] - p2[0]
    c1 = (a1 * p1[0]) + (b1 * p1[1])
    a2 = q2[1] - q1[1]
    b2 = q1[0] - q2[0]
    c2 = (a2 * q1[0]) + (b2 * q1[1])
    det = (a1 * b2) - (a2 * b1)

    if not math.isclose(det, 0):
        return [((b2 * c1) - (b1 * c2)) / det, ((a1 * c2) - (a2 * c1)) / det]
    else:
        return [0, 0]

def polygonQuickDecomp(
        polygon: List[Point2D],
        result=None,
        reflexVertices=None,
        steinerPoints=None,
        delta=25,
        maxlevel=256,
        level=0) -> List[List[Point2D]]:
    """Quickly decompose the Polygon into convex sub-polygons.

    Keyword arguments:
    polygon -- The polygon to decompose
    result -- Stores result of decomposed polygon, passed recursively
    reflexVertices -- 
    steinerPoints --
    delta -- Currently unused
    maxlevel -- The maximum allowed level of recursion
    level -- The current level of recursion

    Returns:
    List of decomposed convex polygons

    """
    if result is None:
        result = []
    reflexVertices = reflexVertices or []
    steinerPoints = steinerPoints or []

    upperInt = [0, 0]
    lowerInt = [0, 0]
    p = [0, 0]         # Points
    upperDist = 0
    lowerDist = 0
    d = 0
    closestDist = 0 # scalars
    upperIndex = 0
    lowerIndex = 0
    closestIndex = 0 # integers
    lowerPoly = []
    upperPoly = [] # polygons
    poly = polygon
    v = polygon

    if len(v) < 3:
        return result

    level += 1
    if level > maxlevel:
        return result

    for i in range(len(polygon)):
        if polygonIsReflex(poly, i):
            reflexVertices.append(poly[i])
            upperDist = float('inf')
            lowerDist = float('inf')

            for j in range(len(polygon)):
                if isLeft(polygonAt(poly, i - 1), polygonAt(poly, i), polygonAt(poly, j)) and isRightOn(polygonAt(poly, i - 1), polygonAt(poly, i), polygonAt(poly, j - 1)): # if line intersects with an edge
                    p = getIntersectionPoint(polygonAt(poly, i - 1), polygonAt(poly, i), polygonAt(poly, j), polygonAt(poly, j - 1)) # find the point of intersection
                    if isRight(polygonAt(poly, i + 1), polygonAt(poly, i), p): # make sure it's inside the poly
                        d = sqdist(poly[i], p)
                        if d < lowerDist: # keep only the closest intersection
                            lowerDist = d
                            lowerInt = p
                            lowerIndex = j

                if isLeft(polygonAt(poly, i + 1), polygonAt(poly, i), polygonAt(poly, j + 1)) and isRightOn(polygonAt(poly, i + 1), polygonAt(poly, i), polygonAt(poly, j)):
                    p = getIntersectionPoint(polygonAt(poly, i + 1), polygonAt(poly, i), polygonAt(poly, j), polygonAt(poly, j + 1))
                    if isLeft(polygonAt(poly, i - 1), polygonAt(poly, i), p):
                        d = sqdist(poly[i], p)
                        if d < upperDist:
                            upperDist = d
                            upperInt = p
                            upperIndex = j

            # if there are no vertices to connect to, choose a point in the middle
            if lowerIndex == (upperIndex + 1) % len(polygon):
                #print("Case 1: Vertex("+str(i)+"), lowerIndex("+str(lowerIndex)+"), upperIndex("+str(upperIndex)+"), poly.size("+str(len(polygon))+")")
                p[0] = (lowerInt[0] + upperInt[0]) / 2
                p[1] = (lowerInt[1] + upperInt[1]) / 2
                steinerPoints.append(p)

                if i < upperIndex:
                    #lowerPoly.insert(lowerPoly.end(), poly.begin() + i, poly.begin() + upperIndex + 1)
                    polygonAppend(lowerPoly, poly, i, upperIndex+1)
                    lowerPoly.append(p)
                    upperPoly.append(p)
                    if lowerIndex != 0:
                        #upperPoly.insert(upperPoly.end(), poly.begin() + lowerIndex, poly.end())
                        polygonAppend(upperPoly, poly, lowerIndex, len(poly))

                    #upperPoly.insert(upperPoly.end(), poly.begin(), poly.begin() + i + 1)
                    polygonAppend(upperPoly, poly, 0, i+1)
                else:
                    if i != 0:
                        #lowerPoly.insert(lowerPoly.end(), poly.begin() + i, poly.end())
                        polygonAppend(lowerPoly, poly, i, len(poly))

                    #lowerPoly.insert(lowerPoly.end(), poly.begin(), poly.begin() + upperIndex + 1)
                    polygonAppend(lowerPoly, poly, 0, upperIndex+1)
                    lowerPoly.append(p)
                    upperPoly.append(p)
                    #upperPoly.insert(upperPoly.end(), poly.begin() + lowerIndex, poly.begin() + i + 1)
                    polygonAppend(upperPoly, poly, lowerIndex, i+1)

            else:
                # connect to the closest point within the triangle
                #print("Case 2: Vertex("+str(i)+"), closestIndex("+str(closestIndex)+"), poly.size("+str(len(polygon))+")\n")

                if lowerIndex > upperIndex:
                    upperIndex += len(polygon)

                closestDist = float('inf')

                if upperIndex < lowerIndex:
                    return result

                for j in range(lowerIndex, upperIndex+1):
                    if isLeftOn(polygonAt(poly, i - 1), polygonAt(poly, i), polygonAt(poly, j)) and isRightOn(polygonAt(poly, i + 1), polygonAt(poly, i), polygonAt(poly, j)):
                        d = sqdist(polygonAt(poly, i), polygonAt(poly, j))
                        if d < closestDist:
                            closestDist = d
                            closestIndex = j % len(polygon)

                if i < closestIndex:
                    polygonAppend(lowerPoly, poly, i, closestIndex+1)
                    if closestIndex != 0:
                        polygonAppend(upperPoly, poly, closestIndex, len(v))

                    polygonAppend(upperPoly, poly, 0, i+1)
                else:
                    if i != 0:
                        polygonAppend(lowerPoly, poly, i, len(v))

                    polygonAppend(lowerPoly, poly, 0, closestIndex+1)
                    polygonAppend(upperPoly, poly, closestIndex, i+1)

            # solve smallest poly first
            if len(lowerPoly) < len(upperPoly):
                polygonQuickDecomp(lowerPoly, result, reflexVertices, steinerPoints, delta, maxlevel, level)
                polygonQuickDecomp(upperPoly, result, reflexVertices, steinerPoints, delta, maxlevel, level)
            else:
                polygonQuickDecomp(upperPoly, result, reflexVertices, steinerPoints, delta, maxlevel, level)
                polygonQuickDecomp(lowerPoly, result, reflexVertices, steinerPoints, delta, maxlevel, level)

            return result

    result.append(polygon)

    return result

__all__ = "polygonQuickDecomp"
