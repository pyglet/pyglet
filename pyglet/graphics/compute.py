from ctypes import byref


from pyglet.gl import *


def _get_tuple(constant: int) -> tuple[int, int, int]:
    val_x = GLint()
    val_y = GLint()
    val_z = GLint()

    for i, value in enumerate((val_x, val_y, val_z)):
        glGetIntegeri_v(constant, i, byref(value))

    return val_x.value, val_y.value, val_z.value


def _get_value(constant: int) -> int:
    val = GLint()
    glGetIntegerv(constant, byref(val))
    return val.value


def get_max_work_group_count() -> tuple[int, int, int]:
    return _get_tuple(GL_MAX_COMPUTE_WORK_GROUP_COUNT)


def get_max_work_group_size() -> tuple[int, int, int]:
    return _get_tuple(GL_MAX_COMPUTE_WORK_GROUP_SIZE)


def get_max_work_group_invocations() -> int:
    return _get_value(GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS)


def get_max_shared_memory_size() -> int:
    return _get_value(GL_MAX_COMPUTE_SHARED_MEMORY_SIZE)

