import math

import pyglet

# Give pyglet a list of folders that contain resources:
pyglet.resource.path = ['../resources']
pyglet.resource.reindex()


def distance(point_1=(0, 0), point_2=(0, 0)):
    """Returns the distance between two points"""
    return math.sqrt((point_1[0] - point_2[0]) ** 2 + (point_1[1] - point_2[1]) ** 2)
