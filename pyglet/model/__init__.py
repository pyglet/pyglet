from pyglet.model import codecs as _codecs
from pyglet.compat import BytesIO
from pyglet.gl import GL_TRIANGLES
from pyglet import graphics


def load(filename, file=None, decoder=None):
    """Load a 3D model from a file.

    :Parameters:
        `filename` : str
            Used to guess the model format, and to load the file if `file` is
            unspecified.
        `file` : file-like object or None
            Source of model data in any supported format.        
        `decoder` : ModelDecoder or None
            If unspecified, all decoders that are registered for the filename
            extension are tried.  If none succeed, the exception from the
            first decoder is raised.

    :rtype: Model
    """

    if not file:
        file = open(filename, 'rb')

    if not hasattr(file, 'seek'):
        file = BytesIO(file.read())

    try:
        if decoder:
            return decoder.decode(file, filename)
        else:
            first_exception = None
            for decoder in _codecs.get_decoders(filename):
                try:
                    image = decoder.decode(file, filename)
                    return image
                except _codecs.ModelDecodeException as e:
                    if (not first_exception or
                                first_exception.exception_priority < e.exception_priority):
                        first_exception = e
                    file.seek(0)

            if not first_exception:
                raise _codecs.ModelDecodeException('No decoders are available'
                                                   'for this model format.')
            raise first_exception
    finally:
        file.close()


class ModelData(object):

    def __init__(self, meshes, materials=None):
        self.meshes = meshes
        self.materials = materials


class Model(object):
    def __init__(self, obj, batch=None, x=0, y=0, z=0):
        self._batch = batch
        self._x = x
        self._y = y
        self._z = z
        self._vertex_lists = []

        self.obj = obj

        self.materials = self.obj.materials
        self.meshes = self.obj.meshes
        self.mesh_list = self.obj.mesh_list

        for mesh in self.mesh_list:
            for group in mesh.materials:
                if self._batch:
                    self._vertex_lists.append(self._batch.add(
                        len(group.vertices) // 3, GL_TRIANGLES,
                        group.material,
                        ('v3f/static', tuple(group.vertices)),
                        ('n3f/static', tuple(group.normals)),
                        ('t2f/static', tuple(group.tex_coords))))
                else:
                    self._vertex_lists.append(graphics.vertex_list(
                        len(group.vertices) // 3,
                        ('v3f/static', tuple(group.vertices)),
                        ('n3f/static', tuple(group.normals)),
                        ('t2f/static', tuple(group.tex_coords))))

    def draw(self):
        # Very slow.
        for i, mesh in enumerate(self.mesh_list):
            for material in mesh.materials:
                material.material.set_state_recursive()
                self._vertex_lists[i].draw(GL_TRIANGLES)
            for material in mesh.materials:
                material.material.unset_state_recursive()


_codecs.add_default_model_codecs()
