# earcut-python - A earcut triangulation library
#
# The code can be found at:
# https://github.com/joshuaskelly/earcut-python
#
# LICENSE (ISC)
#
# Copyright (c) 2016, Mapbox
#
# Permission to use, copy, modify, and/or distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright notice
# and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
# OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
# TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF
# THIS SOFTWARE.

import math

__all__ = ['earcut', 'deviation', 'flatten']


def earcut(data, holeIndices=None, dim=None):
    dim = dim or 2

    hasHoles = holeIndices and len(holeIndices)
    outerLen =  holeIndices[0] * dim if hasHoles else len(data)
    outerNode = linkedList(data, 0, outerLen, dim, True)
    triangles = []

    if not outerNode:
        return triangles

    minX = None
    minY = None
    maxX = None
    maxY = None
    x = None
    y = None
    size = None

    if hasHoles:
        outerNode = eliminateHoles(data, holeIndices, outerNode, dim)

    # if the shape is not too simple, we'll use z-order curve hash later; calculate polygon bbox
    if (len(data) > 80 * dim):
        minX = maxX = data[0]
        minY = maxY = data[1]

        for i in range(dim, outerLen, dim):
            x = data[i]
            y = data[i + 1]
            if x < minX:
                minX = x
            if y < minY:
                minY = y
            if x > maxX:
                maxX = x
            if y > maxY:
                maxY = y

        # minX, minY and size are later used to transform coords into integers for z-order calculation
        size = max(maxX - minX, maxY - minY)

    earcutLinked(outerNode, triangles, dim, minX, minY, size)

    return triangles


# create a circular doubly linked _list from polygon points in the specified winding order
def linkedList(data, start, end, dim, clockwise):
    i = None
    last = None

    if (clockwise == (signedArea(data, start, end, dim) > 0)):
        for i in range(start, end, dim):
            last = insertNode(i, data[i], data[i + 1], last)

    else:
        for i in reversed(range(start, end, dim)):
            last = insertNode(i, data[i], data[i + 1], last)

    if (last and equals(last, last.next)):
        removeNode(last)
        last = last.next

    return last


# eliminate colinear or duplicate points
def filterPoints(start, end=None):
    if not start:
        return start
    if not end:
        end = start

    p = start
    again = True

    while again or p != end:
        again = False

        if (not p.steiner and (equals(p, p.next) or area(p.prev, p, p.next) == 0)):
            removeNode(p)
            p = end = p.prev
            if (p == p.next):
                return None

            again = True

        else:
            p = p.next

    return end

# main ear slicing loop which triangulates a polygon (given as a linked _list)
def earcutLinked(ear, triangles, dim, minX, minY, size, _pass=None):
    if not ear:
        return

    # interlink polygon nodes in z-order
    if not _pass and size:
        indexCurve(ear, minX, minY, size)

    stop = ear
    prev = None
    next = None

    # iterate through ears, slicing them one by one
    while ear.prev != ear.next:
        prev = ear.prev
        next = ear.next

        if isEarHashed(ear, minX, minY, size) if size else isEar(ear):
            # cut off the triangle
            triangles.append(prev.i // dim)
            triangles.append(ear.i // dim)
            triangles.append(next.i // dim)

            removeNode(ear)

            # skipping the next vertice leads to less sliver triangles
            ear = next.next
            stop = next.next

            continue

        ear = next

        # if we looped through the whole remaining polygon and can't find any more ears
        if ear == stop:
            # try filtering points and slicing again
            if not _pass:
                earcutLinked(filterPoints(ear), triangles, dim, minX, minY, size, 1)

                # if this didn't work, try curing all small self-intersections locally
            elif _pass == 1:
                ear = cureLocalIntersections(ear, triangles, dim)
                earcutLinked(ear, triangles, dim, minX, minY, size, 2)

                # as a last resort, try splitting the remaining polygon into two
            elif _pass == 2:
                splitEarcut(ear, triangles, dim, minX, minY, size)

            break

# check whether a polygon node forms a valid ear with adjacent nodes
def isEar(ear):
    a = ear.prev
    b = ear
    c = ear.next

    if area(a, b, c) >= 0:
        return False # reflex, can't be an ear

    # now make sure we don't have other points inside the potential ear
    p = ear.next.next

    while p != ear.prev:
        if pointInTriangle(a.x, a.y, b.x, b.y, c.x, c.y, p.x, p.y) and area(p.prev, p, p.next) >= 0:
                return False
        p = p.next

    return True

def isEarHashed(ear, minX, minY, size):
    a = ear.prev
    b = ear
    c = ear.next

    if area(a, b, c) >= 0:
        return False # reflex, can't be an ear

    # triangle bbox; min & max are calculated like this for speed
    minTX = (a.x if a.x < c.x else c.x) if a.x < b.x else (b.x if b.x < c.x else c.x)
    minTY = (a.y if a.y < c.y else c.y) if a.y < b.y else (b.y if b.y < c.y else c.y)
    maxTX = (a.x if a.x > c.x else c.x) if a.x > b.x else (b.x if b.x > c.x else c.x)
    maxTY = (a.y if a.y > c.y else c.y) if a.y > b.y else (b.y if b.y > c.y else c.y)

    # z-order range for the current triangle bbox;
    minZ = zOrder(minTX, minTY, minX, minY, size)
    maxZ = zOrder(maxTX, maxTY, minX, minY, size)

    # first look for points inside the triangle in increasing z-order
    p = ear.nextZ

    while p and p.z <= maxZ:
        if p != ear.prev and p != ear.next and pointInTriangle(a.x, a.y, b.x, b.y, c.x, c.y, p.x, p.y) and area(p.prev, p, p.next) >= 0:
            return False
        p = p.nextZ

    # then look for points in decreasing z-order
    p = ear.prevZ

    while p and p.z >= minZ:
        if p != ear.prev and p != ear.next and pointInTriangle(a.x, a.y, b.x, b.y, c.x, c.y, p.x, p.y) and area(p.prev, p, p.next) >= 0:
            return False
        p = p.prevZ

    return True

# go through all polygon nodes and cure small local self-intersections
def cureLocalIntersections(start, triangles, dim):
    do = True
    p = start

    while do or p != start:
        do = False

        a = p.prev
        b = p.next.next

        if not equals(a, b) and intersects(a, p, p.next, b) and locallyInside(a, b) and locallyInside(b, a):
            triangles.append(a.i // dim)
            triangles.append(p.i // dim)
            triangles.append(b.i // dim)

            # remove two nodes involved
            removeNode(p)
            removeNode(p.next)

            p = start = b

        p = p.next

    return p

# try splitting polygon into two and triangulate them independently
def splitEarcut(start, triangles, dim, minX, minY, size):
    # look for a valid diagonal that divides the polygon into two
    do = True
    a = start

    while do or a != start:
        do = False
        b = a.next.next

        while b != a.prev:
            if a.i != b.i and isValidDiagonal(a, b):
                # split the polygon in two by the diagonal
                c = splitPolygon(a, b)

                # filter colinear points around the cuts
                a = filterPoints(a, a.next)
                c = filterPoints(c, c.next)

                # run earcut on each half
                earcutLinked(a, triangles, dim, minX, minY, size)
                earcutLinked(c, triangles, dim, minX, minY, size)
                return

            b = b.next

        a = a.next

# link every hole into the outer loop, producing a single-ring polygon without holes
def eliminateHoles(data, holeIndices, outerNode, dim):
    queue = []
    i = None
    _len = len(holeIndices)
    start = None
    end = None
    _list = None

    for i in range(len(holeIndices)):
        start = holeIndices[i] * dim
        end =  holeIndices[i + 1] * dim if i < _len - 1 else len(data)
        _list = linkedList(data, start, end, dim, False)

        if (_list == _list.next):
            _list.steiner = True

        queue.append(getLeftmost(_list))

    queue = sorted(queue, key=lambda i: i.x)

    # process holes from left to right
    for i in range(len(queue)):
        eliminateHole(queue[i], outerNode)
        outerNode = filterPoints(outerNode, outerNode.next)

    return outerNode

def compareX(a, b):
    return a.x - b.x

# find a bridge between vertices that connects hole with an outer ring and and link it
def eliminateHole(hole, outerNode):
    outerNode = findHoleBridge(hole, outerNode)
    if outerNode:
        b = splitPolygon(outerNode, hole)
        filterPoints(b, b.next)

# David Eberly's algorithm for finding a bridge between hole and outer polygon
def findHoleBridge(hole, outerNode):
    do = True
    p = outerNode
    hx = hole.x
    hy = hole.y
    qx = -math.inf
    m = None

    # find a segment intersected by a ray from the hole's leftmost point to the left;
    # segment's endpoint with lesser x will be potential connection point
    while do or p != outerNode:
        do = False
        if hy <= p.y and hy >= p.next.y and p.next.y - p.y != 0:
            x = p.x + (hy - p.y) * (p.next.x - p.x) / (p.next.y - p.y)

            if x <= hx and x > qx:
                qx = x

                if (x == hx):
                    if hy == p.y:
                        return p
                    if hy == p.next.y:
                        return p.next

                m = p if p.x < p.next.x else p.next

        p = p.next

    if not m:
        return None

    if hx == qx:
        return m.prev # hole touches outer segment; pick lower endpoint

    # look for points inside the triangle of hole point, segment intersection and endpoint;
    # if there are no points found, we have a valid connection;
    # otherwise choose the point of the minimum angle with the ray as connection point

    stop = m
    mx = m.x
    my = m.y
    tanMin = math.inf
    tan = None

    p = m.next

    while p != stop:
        hx_or_qx = hx if hy < my else qx
        qx_or_hx = qx if hy < my else hx

        if hx >= p.x and p.x >= mx and pointInTriangle(hx_or_qx, hy, mx, my, qx_or_hx, hy, p.x, p.y):

            tan = abs(hy - p.y) / (hx - p.x) # tangential

            if (tan < tanMin or (tan == tanMin and p.x > m.x)) and locallyInside(p, hole):
                m = p
                tanMin = tan

        p = p.next

    return m

# interlink polygon nodes in z-order
def indexCurve(start, minX, minY, size):
    do = True
    p = start

    while do or p != start:
        do = False

        if p.z is None:
            p.z = zOrder(p.x, p.y, minX, minY, size)

        p.prevZ = p.prev
        p.nextZ = p.next
        p = p.next

    p.prevZ.nextZ = None
    p.prevZ = None

    sortLinked(p)

# Simon Tatham's linked _list merge sort algorithm
# http:#www.chiark.greenend.org.uk/~sgtatham/algorithms/_listsort.html
def sortLinked(_list):
    do = True
    i = None
    p = None
    q = None
    e = None
    tail = None
    numMerges = None
    pSize = None
    qSize = None
    inSize = 1

    while do or numMerges > 1:
        do = False
        p = _list
        _list = None
        tail = None
        numMerges = 0

        while p:
            numMerges += 1
            q = p
            pSize = 0
            for i in range(inSize):
                pSize += 1
                q = q.nextZ
                if not q:
                    break

            qSize = inSize

            while pSize > 0 or (qSize > 0 and q):

                if pSize == 0:
                    e = q
                    q = q.nextZ
                    qSize -= 1

                elif (qSize == 0 or not q):
                    e = p
                    p = p.nextZ
                    pSize -= 1

                elif (p.z <= q.z):
                    e = p
                    p = p.nextZ
                    pSize -= 1

                else:
                    e = q
                    q = q.nextZ
                    qSize -= 1

                if tail:
                    tail.nextZ = e

                else:
                    _list = e

                e.prevZ = tail
                tail = e

            p = q

        tail.nextZ = None
        inSize *= 2

    return _list


# z-order of a point given coords and size of the data bounding box
def zOrder(x, y, minX, minY, size):
    # coords are transformed into non-negative 15-bit integer range
    x = 32767 * (x - minX) // size
    y = 32767 * (y - minY) // size

    x = (x | (x << 8)) & 0x00FF00FF
    x = (x | (x << 4)) & 0x0F0F0F0F
    x = (x | (x << 2)) & 0x33333333
    x = (x | (x << 1)) & 0x55555555

    y = (y | (y << 8)) & 0x00FF00FF
    y = (y | (y << 4)) & 0x0F0F0F0F
    y = (y | (y << 2)) & 0x33333333
    y = (y | (y << 1)) & 0x55555555

    return x | (y << 1)

# find the leftmost node of a polygon ring
def getLeftmost(start):
    do = True
    p = start
    leftmost = start

    while do or p != start:
        do = False
        if p.x < leftmost.x:
            leftmost = p
        p = p.next

    return leftmost

# check if a point lies within a convex triangle
def pointInTriangle(ax, ay, bx, by, cx, cy, px, py):
    return (cx - px) * (ay - py) - (ax - px) * (cy - py) >= 0 and \
        (ax - px) * (by - py) - (bx - px) * (ay - py) >= 0 and \
        (bx - px) * (cy - py) - (cx - px) * (by - py) >= 0

# check if a diagonal between two polygon nodes is valid (lies in polygon interior)
def isValidDiagonal(a, b):
    return a.next.i != b.i and a.prev.i != b.i and not intersectsPolygon(a, b) and \
        locallyInside(a, b) and locallyInside(b, a) and middleInside(a, b)

# signed area of a triangle
def area(p, q, r):
    return (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)

# check if two points are equal
def equals(p1, p2):
    return p1.x == p2.x and p1.y == p2.y


# check if two segments intersect
def intersects(p1, q1, p2, q2):
    if (equals(p1, q1) and equals(p2, q2)) or (equals(p1, q2) and equals(p2, q1)):
        return True

    return area(p1, q1, p2) > 0 != area(p1, q1, q2) > 0 and \
        area(p2, q2, p1) > 0 != area(p2, q2, q1) > 0

# check if a polygon diagonal intersects any polygon segments
def intersectsPolygon(a, b):
    do = True
    p = a

    while do or p != a:
        do = False
        if (p.i != a.i and p.next.i != a.i and p.i != b.i and p.next.i != b.i and intersects(p, p.next, a, b)):
            return True

        p = p.next

    return False

# check if a polygon diagonal is locally inside the polygon
def locallyInside(a, b):
    if area(a.prev, a, a.next) < 0:
        return  area(a, b, a.next) >= 0 and area(a, a.prev, b) >= 0
    else:
        return area(a, b, a.prev) < 0 or area(a, a.next, b) < 0

# check if the middle point of a polygon diagonal is inside the polygon
def middleInside(a, b):
    do = True
    p = a
    inside = False
    px = (a.x + b.x) / 2
    py = (a.y + b.y) / 2

    while do or p != a:
        do = False
        if ((p.y > py) != (p.next.y > py)) and (px < (p.next.x - p.x) * (py - p.y) / (p.next.y - p.y) + p.x):
            inside = not inside

        p = p.next

    return inside

# link two polygon vertices with a bridge; if the vertices belong to the same ring, it splits polygon into two;
# if one belongs to the outer ring and another to a hole, it merges it into a single ring
def splitPolygon(a, b):
    a2 = Node(a.i, a.x, a.y)
    b2 = Node(b.i, b.x, b.y)
    an = a.next
    bp = b.prev

    a.next = b
    b.prev = a

    a2.next = an
    an.prev = a2

    b2.next = a2
    a2.prev = b2

    bp.next = b2
    b2.prev = bp

    return b2


# create a node and optionally link it with previous one (in a circular doubly linked _list)
def insertNode(i, x, y, last):
    p = Node(i, x, y)

    if not last:
        p.prev = p
        p.next = p

    else:
        p.next = last.next
        p.prev = last
        last.next.prev = p
        last.next = p

    return p

def removeNode(p):
    p.next.prev = p.prev
    p.prev.next = p.next

    if p.prevZ:
        p.prevZ.nextZ = p.nextZ

    if p.nextZ:
        p.nextZ.prevZ = p.prevZ

class Node(object):
    def __init__(self, i, x, y):
    # vertice index in coordinates array
        self.i = i

        # vertex coordinates

        self.x = x
        self.y = y

        # previous and next vertice nodes in a polygon ring
        self.prev = None
        self.next = None

        # z-order curve value
        self.z = None

        # previous and next nodes in z-order
        self.prevZ = None
        self.nextZ = None

        # indicates whether this is a steiner point
        self.steiner = False


# return a percentage difference between the polygon area and its triangulation area;
# used to verify correctness of triangulation
def deviation(data, holeIndices, dim, triangles):
    _len = len(holeIndices)
    hasHoles = holeIndices and len(holeIndices)
    outerLen = holeIndices[0] * dim if hasHoles else len(data)

    polygonArea = abs(signedArea(data, 0, outerLen, dim))

    if hasHoles:
        for i in range(_len):
            start = holeIndices[i] * dim
            end = holeIndices[i + 1] * dim if i < _len - 1 else len(data)
            polygonArea -= abs(signedArea(data, start, end, dim))

    trianglesArea = 0

    for i in range(0, len(triangles), 3):
        a = triangles[i] * dim
        b = triangles[i + 1] * dim
        c = triangles[i + 2] * dim
        trianglesArea += abs(
            (data[a] - data[c]) * (data[b + 1] - data[a + 1]) -
            (data[a] - data[b]) * (data[c + 1] - data[a + 1]))

    if polygonArea == 0 and trianglesArea == 0:
        return 0

    return abs((trianglesArea - polygonArea) / polygonArea)


def signedArea(data, start, end, dim):
    sum = 0
    j = end - dim

    for i in range(start, end, dim):
        sum += (data[j] - data[i]) * (data[i + 1] + data[j + 1])
        j = i

    return sum


# turn a polygon in a multi-dimensional array form (e.g. as in GeoJSON) into a form Earcut accepts
def flatten(data):
    dim = len(data[0][0])
    result = {
        'vertices': [],
        'holes': [],
        'dimensions': dim
    }
    holeIndex = 0

    for i in range(len(data)):
        for j in range(len(data[i])):
            for d in range(dim):
                result['vertices'].append(data[i][j][d])

        if i > 0:
            holeIndex += len(data[i - 1])
            result['holes'].append(holeIndex)

    return result

def unflatten(data):
    result = []

    for i in range(0, len(data), 3):
        result.append(tuple(data[i:i + 3]))

    return result
