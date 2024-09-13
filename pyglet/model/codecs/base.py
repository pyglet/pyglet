from __future__ import annotations

from pyglet.gl import GL_TRIANGLES

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Sequence


class Scene:
    """Container for one or more Node objects."""

    def __init__(self, nodes: list[Node] | None = None) -> None:
        self.nodes = nodes or []

    def __iter__(self):
        """Iterate over all Nodes and their children (if existing)."""
        for top_node in self.nodes:
            for node in top_node:
                yield node

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

    def __iter__(self):
        yield self
        for child_node in self.nodes:
            yield child_node

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


class Primitive:
    """Geometry information for a Mesh."""
    def __init__(self, attributes: dict[str, Sequence[float]], indices: Sequence[int] | None = None,
                 material: Material | None = None, mode: int = GL_TRIANGLES) -> None:
        self.attributes = attributes
        self.indices = indices
        self.material = material
        self.mode = mode

    def __repr__(self):
        return f"Primitive(attributes={list(self.attributes)}, mode={self.mode})"


class Material:
    __slots__ = ("name", "diffuse", "ambient", "specular", "emission", "shininess", "texture_name")

    def __init__(self, name: str = "default",
                 diffuse: Sequence[float] = (0.8, 0.8, 0.8, 1.0),
                 ambient: Sequence[float] = (0.2, 0.2, 0.2, 1.0),
                 specular: Sequence[float] = (0.0, 0.0, 0.0, 1.0),
                 emission: Sequence[float] = (0.0, 0.0, 0.0, 1.0),
                 shininess: float = 20,
                 texture_name: str | None = None):

        self.name = name
        self.diffuse = diffuse
        self.ambient = ambient
        self.specular = specular
        self.emission = emission
        self.shininess = shininess
        self.texture_name = texture_name

    def __eq__(self, other: Material) -> bool:
        return (self.name == other.name and self.diffuse == other.diffuse and
                self.ambient == other.ambient and self.specular == other.specular and
                self.emission == other.emission and self.shininess == other.shininess and
                self.texture_name == other.texture_name)

    def __hash__(self) -> int:
        return hash((self.name, self.texture_name, tuple(self.diffuse), tuple(self.specular),
                     tuple(self.ambient), tuple(self.emission), self.shininess, self.texture_name))


class Skin:
    pass


class Camera:
    pass
