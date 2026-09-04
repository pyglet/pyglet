from pyglet.graphics.api.gl.gl_fallback import apply_extension_function_fallbacks


class _ExtensionInfo:
    def __init__(self, extensions: set[str]) -> None:
        self.extensions = extensions

    def have_extension(self, extension: str) -> bool:
        return extension in self.extensions


class _Functions:
    def __init__(self) -> None:
        setattr(self, "glActiveShaderProgram", "core")
        setattr(self, "glActiveShaderProgramEXT", "extension")

    def __getattr__(self, name: str) -> str:
        return name


def test_extension_function_fallback_replaces_the_regular_function() -> None:
    functions = _Functions()

    apply_extension_function_fallbacks(_ExtensionInfo({"GL_EXT_separate_shader_objects"}), functions)

    assert functions.glActiveShaderProgram == "extension"


def test_extension_function_fallback_does_not_apply_without_its_extension() -> None:
    functions = _Functions()

    apply_extension_function_fallbacks(_ExtensionInfo(set()), functions)

    assert functions.glActiveShaderProgram == "core"


def test_extension_function_fallbacks_are_local_to_one_function_table() -> None:
    extension_functions = _Functions()
    core_functions = _Functions()

    apply_extension_function_fallbacks(_ExtensionInfo({"GL_EXT_separate_shader_objects"}), extension_functions)
    apply_extension_function_fallbacks(_ExtensionInfo(set()), core_functions)

    assert extension_functions.glActiveShaderProgram == "extension"
    assert core_functions.glActiveShaderProgram == "core"
