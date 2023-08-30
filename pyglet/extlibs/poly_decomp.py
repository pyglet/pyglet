# Copy from https://github.com/wsilva32/poly_decomp.property
# License under MIT.

import math
from typing import List

from pyglet.customtypes import Point2D

def lineInt(l1, l2, precision=0):
    """Compute the intersection between two lines.

    Keyword arguments:
    l1 -- first line
    l2 -- second line
    precision -- precision to check if lines are parallel (default 0)

    Returns:
    The intersection point
    """
    i = [0, 0] # point
    a1 = l1[1][1] - l1[0][1]
    b1 = l1[0][0] - l1[1][0]
    c1 = a1 * l1[0][0] + b1 * l1[0][1]
    a2 = l2[1][1] - l2[0][1]
    b2 = l2[0][0] - l2[1][0]
    c2 = a2 * l2[0][0] + b2 * l2[0][1]
    det = a1 * b2 - a2 * b1
    if not scalar_eq(det, 0, precision): # lines are not parallel
        i[0] = (b2 * c1 - b1 * c2) / det
        i[1] = (a1 * c2 - a2 * c1) / det
    return i

def lineSegmentsIntersect(p1, p2, q1, q2):
    """Checks if two line segments intersect.

    Keyword arguments:
    p1 -- The start vertex of the first line segment.
    p2 -- The end vertex of the first line segment.
    q1 -- The start vertex of the second line segment.
    q2 -- The end vertex of the second line segment.

    Returns:
    True if the two line segments intersect
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    da = q2[0] - q1[0]
    db = q2[1] - q1[1]

    # segments are parallel
    if (da*dy - db*dx) == 0:
        return False

    s = (dx * (q1[1] - p1[1]) + dy * (p1[0] - q1[0])) / (da * dy - db * dx)
    t = (da * (p1[1] - q1[1]) + db * (q1[0] - p1[0])) / (db * dx - da * dy)

    return s >= 0 and s <= 1 and t >= 0 and t <= 1

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

def collinear(a, b, c, thresholdAngle=0):
    """Checks if three points are collinear.

    Keyword arguments:
    a -- First point
    b -- Second point
    c -- Third point
    thresholdAngle -- threshold to consider if points are collinear, in radians (default 0)

    Returns:
    True if points are collinear
    """
    if thresholdAngle == 0:
        return triangleArea(a, b, c) == 0
    else:
        ab = [None] * 2
        bc = [None] * 2

        ab[0] = b[0]-a[0]
        ab[1] = b[1]-a[1]
        bc[0] = c[0]-b[0]
        bc[1] = c[1]-b[1]

        dot = ab[0]*bc[0] + ab[1]*bc[1]
        magA = math.sqrt(ab[0]*ab[0] + ab[1]*ab[1])
        magB = math.sqrt(bc[0]*bc[0] + bc[1]*bc[1])
        angle = math.acos(dot/(magA*magB))
        return angle < thresholdAngle

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

def polygonMakeCCW(polygon):
    """Makes sure that the polygon vertices are ordered counter-clockwise.

    Keyword arguments:
    polygon -- The polygon

    """
    br = 0
    v = polygon

    # find bottom right point
    for i in range(1, len(polygon)):
        if v[i][1] < v[br][1] or (v[i][1] == v[br][1] and v[i][0] > v[br][0]):
            br = i

    # reverse poly if clockwise
    if not isLeft(polygonAt(polygon, br - 1), polygonAt(polygon, br), polygonAt(polygon, br + 1)):
        polygonReverse(polygon)

def polygonReverse(polygon):
    """Reverses the vertices in the polygon.

    Keyword arguments:
    polygon -- The polygon

    """
    polygon.reverse()

def polygonIsReflex(polygon, i):
    """Checks if a point in the polygon is a reflex point.

    Keyword arguments:
    polygon -- The polygon
    i -- index of point to check

    Returns:
    True is point is a reflex point

    """
    return isRight(polygonAt(polygon, i - 1), polygonAt(polygon, i), polygonAt(polygon, i + 1))

def polygonCanSee(polygon, a, b):
    """Checks if two vertices in the polygon can see each other.

    Keyword arguments:
    polygon -- The polygon
    a -- Vertex 1
    b -- Vertex 2

    Returns:
    True if vertices can see each other

    """

    l1 = [None]*2
    l2 = [None]*2

    if isLeftOn(polygonAt(polygon, a + 1), polygonAt(polygon, a), polygonAt(polygon, b)) and isRightOn(polygonAt(polygon, a - 1), polygonAt(polygon, a), polygonAt(polygon, b)):
        return False

    dist = sqdist(polygonAt(polygon, a), polygonAt(polygon, b))
    for i in range(len(polygon)): # for each edge
        if (i + 1) % len(polygon) == a or i == a: # ignore incident edges
            continue

        if isLeftOn(polygonAt(polygon, a), polygonAt(polygon, b), polygonAt(polygon, i + 1)) and isRightOn(polygonAt(polygon, a), polygonAt(polygon, b), polygonAt(polygon, i)): # if diag intersects an edge
            l1[0] = polygonAt(polygon, a)
            l1[1] = polygonAt(polygon, b)
            l2[0] = polygonAt(polygon, i)
            l2[1] = polygonAt(polygon, i + 1)
            p = lineInt(l1, l2)
            if sqdist(polygonAt(polygon, a), p) < dist: # if edge is blocking visibility to b
                return False

    return True

def polygonCopy(polygon, i, j, targetPoly=None):
    """Copies the polygon from vertex i to vertex j to targetPoly.

    Keyword arguments:
    polygon -- The source polygon
    i -- start vertex
    j -- end vertex (inclusive)
    targetPoly -- Optional target polygon

    Returns:
    The resulting copy.

    """
    p = targetPoly or []
    del p[:]
    if i < j:
        # Insert all vertices from i to j
        for k in range(i, j+1):
            p.append(polygon[k])

    else:
        # Insert vertices 0 to j
        for k in range(0, j+1):
            p.append(polygon[k])

        # Insert vertices i to end
        for k in range(i, len(polygon)):
            p.append(polygon[k])

    return p

def polygonGetCutEdges(polygon):
    """Decomposes the polygon into convex pieces.
    Note that this algorithm has complexity O(N^4) and will be very slow for polygons with many vertices.

    Keyword arguments:
    polygon -- The polygon

    Returns:
    A list of edges [[p1,p2],[p2,p3],...] that cut the polygon.

    """
    mins = []
    tmp1 = []
    tmp2 = []
    tmpPoly = []
    nDiags = float('inf')

    for i in range(len(polygon)):
        if polygonIsReflex(polygon, i):
            for j in range(0, len(polygon)):
                if polygonCanSee(polygon, i, j):
                    tmp1 = polygonGetCutEdges(polygonCopy(polygon, i, j, tmpPoly))
                    tmp2 = polygonGetCutEdges(polygonCopy(polygon, j, i, tmpPoly))

                    for k in range(0, len(tmp2)):
                        tmp1.append(tmp2[k])

                    if len(tmp1) < nDiags:
                        mins = tmp1
                        nDiags = len(tmp1)
                        mins.append([polygonAt(polygon, i), polygonAt(polygon, j)])

    return mins

def polygonDecomp(polygon):
    """Decomposes the polygon into one or more convex sub-polygons.

    Keyword arguments:
    polygon -- The polygon

    Returns:
    An array or polygon objects.

    """
    edges = polygonGetCutEdges(polygon)
    if len(edges) > 0:
        return polygonSlice(polygon, edges)
    else:
        return [polygon]

def polygonSlice(polygon, cutEdges):
    """Slices the polygon given one or more cut edges. If given one, this function will return two polygons (false on failure). If many, an array of polygons.

    Keyword arguments:
    polygon -- The polygon
    cutEdges -- A list of edges to cut on, as returned by getCutEdges()

    Returns:
    An array of polygon objects.

    """
    if len(cutEdges) == 0:
        return [polygon]

    if isinstance(cutEdges, list) and len(cutEdges) != 0 and isinstance(cutEdges[0], list) and len(cutEdges[0]) == 2 and isinstance(cutEdges[0][0], list):

        polys = [polygon]

        for i in range(len(cutEdges)):
            cutEdge = cutEdges[i]
            # Cut all polys
            for j in range(len(polys)):
                poly = polys[j]
                result = polygonSlice(poly, cutEdge)
                if result:
                    # Found poly! Cut and quit
                    del polys[j:j+1]
                    polys.extend((result[0], result[1]))
                    break

        return polys
    else:

        # Was given one edge
        cutEdge = cutEdges
        i = polygon.index(cutEdge[0])
        j = polygon.index(cutEdge[1])

        if i != -1 and j != -1:
            return [polygonCopy(polygon, i, j),
                    polygonCopy(polygon, j, i)]
        else:
            return False

def polygonIsSimple(polygon):
    """Checks that the line segments of this polygon do not intersect each other.

    Keyword arguments:
    polygon -- The polygon

    Returns:
    True is polygon is simple (not self-intersecting)

    Todo:
    Should it check all segments with all others?

    """
    path = polygon
    # Check
    for i in range(len(path)-1):
        for j in range(i-1):
            if lineSegmentsIntersect(path[i], path[i+1], path[j], path[j+1]):
                return False

    # Check the segment between the last and the first point to all others
    for i in range(1,len(path)-2):
        if lineSegmentsIntersect(path[0], path[len(path)-1], path[i], path[i+1]):
            return False

    return True

def getIntersectionPoint(p1, p2, q1, q2, delta=0):
    """Gets the intersection point 

    Keyword arguments:
    p1 -- The start vertex of the first line segment.
    p2 -- The end vertex of the first line segment.
    q1 -- The start vertex of the second line segment.
    q2 -- The end vertex of the second line segment.
    delta -- Optional precision to check if lines are parallel (default 0)

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

    if not scalar_eq(det, 0, delta):
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

def polygonRemoveCollinearPoints(polygon, precision=0):
    """Remove collinear points in the polygon.

    Keyword arguments:
    polygon -- The polygon
    precision -- The threshold angle to use when determining whether two edges are collinear. (default is 0)

    Returns:
    The number of points removed

    """
    num = 0
    i = len(polygon) - 1
    while len(polygon) > 3 and i >= 0:
    #(var i=polygon.length-1; polygon.length>3 && i>=0; --i){
        if collinear(polygonAt(polygon, i - 1), polygonAt(polygon, i), polygonAt(polygon, i+1), precision):
            # Remove the middle point
            del polygon[i % len(polygon):(i % len(polygon))+1]
            num += 1
        i -= 1
    return num

def scalar_eq(a, b, precision=0):
    """Check if two scalars are equal.

    Keyword arguments:
    a -- first scalar
    b -- second scalar
    precision -- precision to check equality

    Returns:
    True if scalars are equal
    """
    return abs(a - b) <= precision

__all__ = "polygonQuickDecomp"
