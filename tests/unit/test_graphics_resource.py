from dataclasses import dataclass

import pytest

from pyglet.graphics.resource import BufferKey, GraphicsResource, ResourceKey, ShaderKey, ShaderProgramKey, TextureKey


@dataclass(frozen=True, slots=True)
class SharedTestKey(ResourceKey):
    pass


class TextureResource(GraphicsResource[object, TextureKey]):
    key_type = TextureKey

    def __init__(self, handle: object, *, key: TextureKey | None = None) -> None:
        super().__init__(key=key)
        self._handle = handle

    def delete(self) -> None:
        self._handle = None


class ShaderResource(GraphicsResource[object, ShaderKey]):
    key_type = ShaderKey

    def delete(self) -> None:
        self._handle = None


class ShaderProgramResource(GraphicsResource[object, ShaderProgramKey]):
    key_type = ShaderProgramKey

    def delete(self) -> None:
        self._handle = None


def test_resource_key_is_hashable_when_handle_is_not() -> None:
    resource = TextureResource([])

    assert hash(resource.key)
    assert resource.handle == []


def test_resources_with_the_same_key_type_have_unique_keys() -> None:
    class FirstResource(GraphicsResource[object, SharedTestKey]):
        key_type = SharedTestKey

        def delete(self) -> None:
            self._handle = None

    class SecondResource(GraphicsResource[object, SharedTestKey]):
        key_type = SharedTestKey

        def delete(self) -> None:
            self._handle = None

    first = FirstResource()
    second = FirstResource()
    sibling = SecondResource()

    assert first.key == SharedTestKey(1)
    assert second.key == SharedTestKey(2)
    assert sibling.key == SharedTestKey(3)


def test_resource_key_types_do_not_compare_equal() -> None:
    assert TextureKey(1) != BufferKey(1)


def test_shader_resource_key_types_are_distinct() -> None:
    shader = ShaderResource()
    program = ShaderProgramResource()

    assert isinstance(shader.key, ShaderKey)
    assert isinstance(program.key, ShaderProgramKey)
    assert shader.key != program.key


def test_resource_handle_is_read_only_and_key_survives_deletion() -> None:
    resource = TextureResource(object())
    key = resource.key

    with pytest.raises(AttributeError):
        resource.handle = object()

    resource.delete()

    assert resource.key == key
    assert resource.handle is None


def test_id_is_a_read_only_handle_alias() -> None:
    resource = TextureResource(object())

    assert resource.id is resource.handle


def test_existing_key_can_be_shared_with_a_resource_view() -> None:
    owner = TextureResource(object())
    view = TextureResource(owner.handle, key=owner.key)

    assert view.key == owner.key
    assert view.handle is owner.handle
