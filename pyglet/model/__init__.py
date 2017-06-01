from pyglet.model import codecs as _codecs
from pyglet.compat import BytesIO
from pyglet.gl import GL_TRIANGLES
from pyglet import graphics


def load(filename, file=None, decoder=None, batch=None):
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
        `batch` : Batch or None
            An optional Batch instance to add this model to. 

    :rtype: Model
    """

    if not file:
        file = open(filename, 'rb')

    if not hasattr(file, 'seek'):
        file = BytesIO(file.read())

    try:
        if decoder:
            return decoder.decode(file, filename, batch)
        else:
            first_exception = None
            for decoder in _codecs.get_decoders(filename):
                try:
                    model = decoder.decode(file, filename, batch)
                    return model
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


class Model(object):

    _own_batch = False

    def __init__(self, obj, batch=None, x=0, y=0, z=0):
        if not batch:
            batch = graphics.Batch()
            self._own_batch = True
        self._batch = batch

        self._x = x
        self._y = y
        self._z = z
        self._vertex_lists = []

        self.mesh_list = obj.mesh_list

        for mesh in self.mesh_list:
            for material in mesh.materials:
                self._vertex_lists.append(self._batch.add(len(material.vertices) // 3,
                                                          GL_TRIANGLES,
                                                          material.group,
                                                          ('v3f/static', material.vertices),
                                                          ('n3f/static', material.normals),
                                                          ('t2f/static', material.tex_coords)))

        # for mesh in self.mesh_list:
        #     # print(m.name, m.materials)
        #     for mat in mesh.materials:
        #         print(mat.group.name, mat.group)

    def draw(self):
        if self._own_batch:
            self._batch.draw()
        else:
            self._batch.draw_subset(self._vertex_lists)


_codecs.add_default_model_codecs()
