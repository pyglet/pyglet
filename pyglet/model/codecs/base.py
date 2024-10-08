from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Sequence
    from pyglet.model import Model
    from pyglet.graphics import Batch, Group


class Scene(ABC):
    """A high level container for one or more Node objects."""

    def __init__(self, nodes: list[Node] | None = None) -> None:
        self.nodes = nodes or []

    # TODO: test and implement:
    # def __iter__(self):
    #     """Iterate over all Nodes and their children (if existing)."""
    #     for top_node in self.nodes:
    #         for node in top_node:
    #             yield node

    def create_models(self, batch: Batch, group: Group | None = None) -> list[Model]:
        """TBD"""
        raise NotImplementedError(f"{self.__class__.__name__} does not implement this method.")

    def __repr__(self):
        return f"{self.__class__.__name__}(nodes={self.nodes})"


class Node:
    """Container for one or more sub-objects, such as Meshes."""
    def __init__(self, nodes: list[Node] | None = None, meshes: list[Mesh] | None = None,
                 skins: list[Skin] | None = None, cameras: list[Camera] | None = None) -> None:
        self.nodes = nodes or []
        self.meshes = meshes or []
        self.skins = skins or []
        self.cameras = cameras or []

    # TODO: test and implement:
    # def __iter__(self):
    #     yield self
    #     for child_node in self.nodes:
    #         yield child_node

    def __repr__(self):
        return (f"Node(nested_nodes={len(self.nodes)}, meshes={len(self.meshes)},"
                f"skins={len(self.skins)}, cameras={len(self.cameras)})")


class Mesh:
    """Object containing vertex and related data."""
    def __init__(self, primitives: list[Primitive] | None = None, name: str = "unknown") -> None:
        self.primitives = primitives or []
        self.name = name

    def __repr__(self):
        return f"Mesh(name='{self.name}', primitive_count={len(self.primitives)})"


class Attribute:
    def __init__(self, name: str, fmt: str, attr_type, count, array):
        self.name = name
        self.fmt = fmt
        self.type = attr_type
        self.count = count
        self.array = array

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', fmt={self.fmt}, type={self.type}, count={self.count})"


class Primitive:
    """Geometry to be rendered, with optional material."""
    def __init__(self, attributes: list[Attribute], indices: Sequence[int] | None,
                 mode: int, material: Material | None = None) -> None:
        self.attributes = attributes
        self.indices = indices
        self.mode = mode
        self.material = material

    def __repr__(self):
        return f"Primitive(attributes={list(self.attributes)}, mode={self.mode})"


class Material(ABC):
    """Base class for Material types"""


class SimpleMaterial(Material):
    def __init__(self, name: str = "default",
                 diffuse: Sequence[float] = (0.8, 0.8, 0.8, 1.0),
                 ambient: Sequence[float] = (0.2, 0.2, 0.2, 1.0),
                 specular: Sequence[float] = (0.0, 0.0, 0.0, 1.0),
                 emission: Sequence[float] = (0.0, 0.0, 0.0, 1.0),
                 shininess: float = 20,
                 texture_name: str | None = None) -> None:

        self.name = name
        self.diffuse = diffuse
        self.ambient = ambient
        self.specular = specular
        self.emission = emission
        self.shininess = shininess
        self.texture_name = texture_name

    def __repr__(self):
        return f"Material(name='{self.name}', texture='{self.texture_name}'"


class PBRMaterial(Material):
    def __init__(self):
        # TODO: implement this class
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
