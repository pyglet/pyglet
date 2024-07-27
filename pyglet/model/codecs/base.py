from __future__ import annotations


class Scene:
    nodes: list[Node]
    """Container for one or more Node objects."""


class Node:
    """Container for one or more sub-objects, such as Meshes."""


class Mesh:
    """Object containing vertex and related data."""
