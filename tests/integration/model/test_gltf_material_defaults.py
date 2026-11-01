"""Valid glTF materials may omit the metallic-roughness block entirely."""
import base64
import io
import json
import struct

import pytest

from pyglet.model.codecs.gltf import load_gltf


def load_triangle(material):
    binary = struct.pack('<9f', 0, 0, 0, 1, 0, 0, 0, 1, 0)
    data = {
        'asset': {'version': '2.0'},
        'buffers': [{'byteLength': len(binary), 'uri': 'data:application/octet-stream;base64,' + base64.b64encode(binary).decode()}],
        'bufferViews': [{'buffer': 0, 'byteLength': len(binary)}],
        'accessors': [{'bufferView': 0, 'componentType': 5126, 'count': 3, 'type': 'VEC3', 'min': [0, 0, 0], 'max': [1, 1, 0]}],
        'materials': [material],
        'meshes': [{'primitives': [{'attributes': {'POSITION': 0}, 'material': 0}]}],
        'nodes': [{'mesh': 0}], 'scenes': [{'nodes': [0]}], 'scene': 0,
    }
    return load_gltf('triangle.gltf', io.StringIO(json.dumps(data)))


@pytest.mark.parametrize('properties', [
    {}, {'name': 'Default material'}, {'doubleSided': True},
    {'alphaMode': 'BLEND', 'emissiveFactor': [0.1, 0.2, 0.3]},
    {'extensions': {'VENDOR_material': {'value': 1}}, 'extras': {'note': 'kept'}},
    {'pbrMetallicRoughness': {}},
])
def test_optional_metallic_roughness_defaults(properties):
    model = load_triangle(properties)
    material = model.materials[0]
    assert tuple(material.base_color_factor) == (1, 1, 1, 1)
    assert material.metalic_factor == 1 and material.roughness_factor == 1
    assert material.base_color_texture is None and material.metallic_roughness_texture is None
    assert model.meshes[0].primitives[0].material is material
    assert list(model.meshes[0].primitives[0].attributes[0].array) == [0, 0, 0, 1, 0, 0, 0, 1, 0]
    assert material.double_sided is properties.get('doubleSided', False)
    assert material.extensions == properties.get('extensions')
    assert material.extras == properties.get('extras')


def test_explicit_metallic_roughness_values_are_preserved():
    material = load_triangle({'pbrMetallicRoughness': {
        'baseColorFactor': [0.1, 0.2, 0.3, 0.4], 'metallicFactor': 0.25, 'roughnessFactor': 0.75,
    }}).materials[0]
    assert material.base_color_factor == [0.1, 0.2, 0.3, 0.4]
    assert material.metalic_factor == 0.25 and material.roughness_factor == 0.75
