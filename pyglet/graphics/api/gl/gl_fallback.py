"""Fallbacks for OpenGL functions provided by extensions.

Some extensions expose functionality that later became core OpenGL under a
suffixed function name. This module lets GL backends use those
extension functions without changing module globals.
"""
from __future__ import annotations

from typing import Protocol


class ExtensionInfo(Protocol):
    """The extension information needed to select function fallbacks."""

    def have_extension(self, extension: str) -> bool:
        """Return whether an extension is available on this context."""


EXTENSION_FUNCTION_FALLBACKS: dict[str, dict[str, str]] = {
    "GL_EXT_separate_shader_objects": {
        "glActiveShaderProgram": "glActiveShaderProgramEXT",
        "glBindProgramPipeline": "glBindProgramPipelineEXT",
        "glCreateShaderProgramv": "glCreateShaderProgramvEXT",
        "glDeleteProgramPipelines": "glDeleteProgramPipelinesEXT",
        "glGenProgramPipelines": "glGenProgramPipelinesEXT",
        "glGetProgramPipelineInfoLog": "glGetProgramPipelineInfoLogEXT",
        "glGetProgramPipelineiv": "glGetProgramPipelineivEXT",
        "glIsProgramPipeline": "glIsProgramPipelineEXT",
        "glProgramParameteri": "glProgramParameteriEXT",
        "glProgramUniform1f": "glProgramUniform1fEXT",
        "glProgramUniform1fv": "glProgramUniform1fvEXT",
        "glProgramUniform1i": "glProgramUniform1iEXT",
        "glProgramUniform1iv": "glProgramUniform1ivEXT",
        "glProgramUniform1ui": "glProgramUniform1uiEXT",
        "glProgramUniform1uiv": "glProgramUniform1uivEXT",
        "glProgramUniform2f": "glProgramUniform2fEXT",
        "glProgramUniform2fv": "glProgramUniform2fvEXT",
        "glProgramUniform2i": "glProgramUniform2iEXT",
        "glProgramUniform2iv": "glProgramUniform2ivEXT",
        "glProgramUniform2ui": "glProgramUniform2uiEXT",
        "glProgramUniform2uiv": "glProgramUniform2uivEXT",
        "glProgramUniform3f": "glProgramUniform3fEXT",
        "glProgramUniform3fv": "glProgramUniform3fvEXT",
        "glProgramUniform3i": "glProgramUniform3iEXT",
        "glProgramUniform3iv": "glProgramUniform3ivEXT",
        "glProgramUniform3ui": "glProgramUniform3uiEXT",
        "glProgramUniform3uiv": "glProgramUniform3uivEXT",
        "glProgramUniform4f": "glProgramUniform4fEXT",
        "glProgramUniform4fv": "glProgramUniform4fvEXT",
        "glProgramUniform4i": "glProgramUniform4iEXT",
        "glProgramUniform4iv": "glProgramUniform4ivEXT",
        "glProgramUniform4ui": "glProgramUniform4uiEXT",
        "glProgramUniform4uiv": "glProgramUniform4uivEXT",
        "glProgramUniformMatrix2fv": "glProgramUniformMatrix2fvEXT",
        "glProgramUniformMatrix2x3fv": "glProgramUniformMatrix2x3fvEXT",
        "glProgramUniformMatrix2x4fv": "glProgramUniformMatrix2x4fvEXT",
        "glProgramUniformMatrix3fv": "glProgramUniformMatrix3fvEXT",
        "glProgramUniformMatrix3x2fv": "glProgramUniformMatrix3x2fvEXT",
        "glProgramUniformMatrix3x4fv": "glProgramUniformMatrix3x4fvEXT",
        "glProgramUniformMatrix4fv": "glProgramUniformMatrix4fvEXT",
        "glProgramUniformMatrix4x2fv": "glProgramUniformMatrix4x2fvEXT",
        "glProgramUniformMatrix4x3fv": "glProgramUniformMatrix4x3fvEXT",
        "glUseProgramStages": "glUseProgramStagesEXT",
        "glValidateProgramPipeline": "glValidateProgramPipelineEXT",
    },
    "GL_EXT_geometry_shader": {
        "glFramebufferTexture": "glFramebufferTextureEXT",
    },
    "GL_OES_draw_elements_base_vertex": {
        "glDrawElementsBaseVertex": "glDrawElementsBaseVertexOES",
        "glDrawElementsInstancedBaseVertex": "glDrawElementsInstancedBaseVertexOES",
        "glDrawRangeElementsBaseVertex": "glDrawRangeElementsBaseVertexOES",
        "glMultiDrawElementsBaseVertex": "glMultiDrawElementsBaseVertexEXT",
    },
    "GL_OES_tessellation_shader": {
        "glPatchParameteri": "glPatchParameteriOES",
    },
}


def get_extension_function_fallbacks(info: ExtensionInfo) -> dict[str, str]:
    """Return regular function names mapped to extension function names."""
    fallbacks = {}
    for extension, extension_fallbacks in EXTENSION_FUNCTION_FALLBACKS.items():
        if info.have_extension(extension):
            fallbacks.update(extension_fallbacks)
    return fallbacks


def apply_extension_function_fallbacks(info: ExtensionInfo, functions: object) -> None:
    """Use available extension functions in place of their regular names.

    ``functions`` must be local to one surface context. Mutating a generated
    module-level GL binding would incorrectly share a decision between
    contexts and backends.
    """
    for function_name, extension_name in get_extension_function_fallbacks(info).items():
        setattr(functions, function_name, getattr(functions, extension_name))
