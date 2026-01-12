from __future__ import annotations

import dataclasses

from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Sequence
    from pyglet.model import Model
    from pyglet.graphics import Batch, Group
    from pyglet.enums import GeometryMode


class Scene:
    """A high level container for one or more Nodes.

    The Scene contains a list of 0 or more Nodes. The Nodes
    themselves may contain 'child' Nodes. The Node list can
    be accessed directly. Alternatively, the Scene instance
    can be iterated over. This will recursively yield all
    Nodes and their child Nodes. For example::

        for node in scene_instance:
            ...

    will yield::

        yield NodeA
            yield ChildA
            yield ChildB
        yield NodeB
        etc.

    """

    def __init__(self, nodes: list[Node] | None = None) -> None:
        self.nodes = nodes or []

    def __iter__(self):
        """Recursively iterate over all Nodes and their children."""
        for parent_node in self.nodes:
            yield parent_node
            for child_node in parent_node.children:
                yield child_node

    def create_models(self, batch: Batch, group: Group | None = None) -> list[Model]:
        """Decoder subclasses are currently responsible for generating Model objects.

        Once base classes are fully defined, the decoders should not create GPU resources
        themselves. Instead, the final VertexLists, etc. can be created here.
        """
        vertex_lists = []
        groups = []
        for node in self.nodes:
            material = node.mesh.primitives[0].material

        raise NotImplementedError(f"{self.__class__.__name__} does not implement this method.")

    def __repr__(self):
        return f"{self.__class__.__name__}(nodes={len(self.nodes)})"


class Node:
    """Container for one or more sub-objects, such as Meshes."""
    def __init__(self, mesh: Mesh | None = None, skin: Skin | None = None,
                 camera: Camera | None = None, children: list[Node] | None = None) -> None:
        self.mesh = mesh
        self.skin = skin
        self.camera = camera
        self.children = children or []

    def __repr__(self):
        return (f"{self.__class__.__name__}"
                f"(mesh={self.mesh}, skin={self.skin}, camera={self.camera}, children={len(self.children)})")


class Mesh:
    """Object containing vertex and related data."""
    def __init__(self, primitives: list[Primitive] | None = None, name: str = "unknown") -> None:
        self.primitives = primitives or []
        self.name = name

    def __repr__(self):
        return f"Mesh(name='{self.name}', primitives={len(self.primitives)})"


@dataclasses.dataclass
class Attribute:
    name: str
    fmt: str
    type: str
    count: int
    array: Sequence

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', fmt={self.fmt}, type={self.type}, count={self.count})"


class Primitive:
    """Geometry to be rendered, with optional material."""
    def __init__(self, attributes: list[Attribute], indices: Sequence[int] | None,
                 mode: GeometryMode, material: Material | None = None) -> None:
        self.attributes = attributes
        self.indices = indices
        self.mode = mode
        self.material = material

    def __repr__(self):
        return f"Primitive(attributes={list(self.attributes)}, mode={self.mode})"


class Material(ABC):
    """Base class for Material types"""


@dataclasses.dataclass(frozen=True)
class SimpleMaterial(Material):
    name: str = "default",
    diffuse: tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0)
    ambient: tuple[float, float, float, float] = (0.2, 0.2, 0.2, 1.0)
    specular: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    emission: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    shininess: float = 20
    texture_name: str | None = None


class PBRMaterial(Material):
    def __init__(self):
        # TODO: implement this as a dataclass
        pass


class Camera:
    def __init__(self, camera_type: str, aspect: float, yfov: float,
                 xmag: float, ymag: float, zfar: float, znear: float) -> None:
        self.type = camera_type
        # Perspective
        self.aspect_ratio = aspect
        self.yfov = yfov
        # Orthographic
        self.xmag = xmag
        self.ymag = ymag
        # Shared
        self.zfar = zfar
        self.znear = znear

    def __repr__(self):
        return f"Camera(type='{self.type}')"


class Skin:
    def __init__(self) -> None:
        # TODO: implement this class
        pass
