"""Scene iteration should visit every descendant in depth-first document order."""
import base64
import io
import json
import struct

import pytest

import pyglet.model
from pyglet.model.codecs.base import Node, Scene
from pyglet.model.codecs.gltf import GLTFModelDecoder


@pytest.mark.parametrize('shape', ['empty', 'flat', 'siblings', 'grandchild', 'branches'])
def test_scene_depth_first_order(shape):
    a, b, c, d, e = [Node() for _ in range(5)]
    if shape == 'empty':
        roots, expected = [], []
    elif shape == 'flat':
        roots, expected = [a, b], [a, b]
    elif shape == 'siblings':
        a.children = [b, c]
        roots, expected = [a, d], [a, b, c, d]
    elif shape == 'grandchild':
        a.children, b.children = [b], [c]
        roots, expected = [a, d], [a, b, c, d]
    else:
        a.children, b.children, c.children = [b, c], [d], [e]
        roots, expected = [a], [a, b, d, c, e]
    scene = Scene(roots)
    assert list(scene) == expected
    assert list(scene) == expected
    assert scene.nodes == roots


def test_deep_scene_does_not_require_python_recursion():
    nodes = [Node() for _ in range(1500)]
    for parent, child in zip(nodes, nodes[1:]):
        parent.children = [child]
    assert list(Scene([nodes[0]])) == nodes


def test_loaded_gltf_visits_nested_mesh_nodes():
    binary = struct.pack('<9f', 0, 0, 0, 1, 0, 0, 0, 1, 0)
    data = {
        'asset': {'version': '2.0'},
        'buffers': [{'byteLength': len(binary), 'uri': 'data:application/octet-stream;base64,' + base64.b64encode(binary).decode()}],
        'bufferViews': [{'buffer': 0, 'byteLength': len(binary)}],
        'accessors': [{'bufferView': 0, 'componentType': 5126, 'count': 3, 'type': 'VEC3', 'min': [0, 0, 0], 'max': [1, 1, 0]}],
        'meshes': [{'primitives': [{'attributes': {'POSITION': 0}}]}],
        'nodes': [{'name': 'root', 'children': [1]}, {'name': 'child', 'children': [2]},
                  {'name': 'grandchild', 'mesh': 0}, {'name': 'other root', 'mesh': 0}],
        'scenes': [{'nodes': [0, 3]}], 'scene': 0,
    }
    scene = pyglet.model.load('hierarchy.gltf', io.StringIO(json.dumps(data)), decoder=GLTFModelDecoder())
    visited = list(scene)
    assert [node.name for node in visited] == ['root', 'child', 'grandchild', 'other root']
    assert len([node for node in visited if node.mesh is not None]) == 2
    assert visited[2].mesh is visited[3].mesh
