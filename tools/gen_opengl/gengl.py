"""Generate the pyglet OpenGL bindings.
See : tools/gen_opengl/requirements.txt.

We are using the opengl-registry project to extract this information from
https://raw.githubusercontent.com/KhronosGroup/OpenGL-Registry/master/xml/gl.xml

A local version gl.xml can also be used.

Usage:

# Fetch gl.xml from Khronos Github repo
python gengl.py
python gengl.py --source url

# Use local gl.xml
python gengl.py --source local
"""  # noqa: D205
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import TextIO, Iterable

from opengl_registry import Registry, RegistryReader

REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
GEN_OPENGL_DIR = Path(__file__).parent
DEST_PATH = REPO_ROOT / "pyglet" / "graphics" / "api" / "gl"


# Try to match with features we utilize in pyglet to ensure all the relevant information is
# generated with it.
EXTENSIONS = [
    "GL_ARB_buffer_storage",
    "GL_ARB_bindless_texture",
    "GL_ARB_compute_shader",
    "GL_ARB_draw_elements_base_vertex",
    "GL_ARB_ES3_compatibility",
    "GL_ARB_geometry_shader4",
    "GL_ARB_gpu_shader_int64",
    "GL_ARB_multisample",
    "GL_ARB_pixel_buffer_object",
    "GL_ARB_separate_shader_objects",
    "GL_ARB_shader_storage_buffer_object",
    "GL_ARB_sync",
    "GL_ARB_tessellation_shader",
    "GL_ARB_texture_compression_bptc",  # BPTC compressed texture formats.
    "GL_ARB_texture_storage",
    "GL_EXT_framebuffer_object",
    "GL_EXT_geometry_shader",
    "GL_EXT_multi_draw_arrays",  # Batched vertex-domain draw calls.
    "GL_EXT_pixel_buffer_object",
    "GL_EXT_read_format_bgra",  # BGRA  format support.
    "GL_APPLE_texture_format_BGRA8888",  # BGRA format support.
    "GL_EXT_texture_format_BGRA8888",  # BGRA format support.
    "GL_EXT_separate_shader_objects",
    "GL_EXT_texture_compression_dxt1",  # DXT1 compressed texture.
    "GL_EXT_texture_compression_rgtc",  # RGTC compressed texture formats.
    "GL_EXT_texture_compression_s3tc",  # S3TC/DDS compressed texture support.
    "GL_EXT_unpack_subimage",  # Row-length controls for pixel uploads.
    "GL_KHR_texture_compression_astc_ldr",  # ASTC LDR compressed texture formats.
    "GL_NV_mesh_shader",
    "GL_NV_pixel_buffer_object",
    "GL_OES_draw_elements_base_vertex",  # Base vertex draw for webgl.
    "GL_OES_tessellation_shader",  # Tessellation for webgl.
]


def get_supported_extensions(registry: Registry, api: str | None = None) -> list[str]:
    """Return checked extensions defined for an optional registry API."""
    supported_extensions = []
    for extension in EXTENSIONS:
        try:
            extension_definition = registry.get_extension(extension)
        except KeyError:
            continue
        if api and api not in extension_definition._supported.split("|"):  # noqa: SLF001
            continue
        supported_extensions.append(extension)
    return supported_extensions


def main() -> None:  # noqa: D103
    values = parse_args(sys.argv[1:])
    if values.source == "url":
        # Fetch gl.xml from Khronos Github repo
        reader = RegistryReader.from_url()
    else:
        # Use the local gl.xml file
        reader = RegistryReader.from_file(GEN_OPENGL_DIR / "gl.xml")

    registry = reader.read()
    supported_extensions = get_supported_extensions(registry)
    gles_extensions = get_supported_extensions(registry, api="gles2")

    core_profile = registry.get_profile(
        api="gl",
        profile="core",
        version="4.6",
        extensions=supported_extensions,
    )
    compat_profile = registry.get_profile(
        api="gl",
        profile="compat",
        version="4.6",
        extensions=supported_extensions,
    )
    gles_profile = registry.get_profile(
        api="gles2",
        profile="core",
        version="3.2",
        extensions=gles_extensions,
    )

    core_writer = PygletGLWriter(registry=core_profile, out_module=DEST_PATH / "gl")
    core_writer.run()
    compat_writer = PygletGLWriter(registry=compat_profile, out_module=DEST_PATH / "gl_compat")
    compat_writer.run()
    gles_writer = PygletGLWriter(
        registry=gles_profile,
        out_module=DEST_PATH / "gles",
        api_name="OpenGL ES",
    )
    gles_writer.run()


def parse_args(args: str) -> Namespace:  # noqa: D103
    parser = ArgumentParser()
    parser.add_argument("--source", choices=["local", "url"], default="url")
    return parser.parse_args(args)


class PygletGLWriter:
    """Write a GL API module and its type stub."""

    # All gl types manually matched to ctypes.
    # Inspect registry.types
    types = {  # noqa: RUF012
        "GLenum": "c_uint",
        "GLboolean": "c_ubyte",
        "GLbitfield": "c_uint",
        "GLvoid": "None",
        "GLbyte": "c_char",
        "GLubyte": "c_ubyte",
        "GLshort": "c_short",
        "GLushort": "c_ushort",
        "GLint": "c_int",
        "GLuint": "c_uint",
        "GLclampx": "c_uint",
        "GLsizei": "c_int",
        "GLfloat": "c_float",
        "GLclampf": "c_float",
        "GLdouble": "c_double",
        "GLclampd": "c_double",
        "GLchar": "c_char",
        "GLintptr": "c_ptrdiff_t",
        "GLsizeiptr": "c_ptrdiff_t",
        "GLint64": "c_int64",
        "GLuint64": "c_uint64",
        "GLuint64EXT": "c_uint64",
        "GLsync": "POINTER(struct___GLsync)",
        "GLDEBUGPROC": "CFUNCTYPE(None, GLenum, GLenum, GLuint, GLenum, GLsizei, POINTER(GLchar), POINTER(GLvoid))",
    }
    # All gl types matched to python types
    pythontypes = {
        "GLenum": "int",
        "GLboolean": "int",
        "GLbitfield": "int",
        "GLvoid": "None",
        "GLbyte": "bytes",
        "GLubyte": "int",
        "GLshort": "int",
        "GLushort": "int",
        "GLint": "int",
        "GLuint": "int",
        "GLclampx": "int",
        "GLsizei": "int",
        "GLfloat": "float",
        "GLclampf": "float",
        "GLdouble": "float",
        "GLclampd": "float",
        "GLchar": "bytes",
        # "GLintptr": "c_ptrdiff_t",
        # "GLsizeiptr": "c_ptrdiff_t",
        "GLint64": "int",
        "GLuint64": "int",
        "GLuint64EXT": "int",
    }
    exclude_commands = set()

    def __init__(
        self,
        *,
        registry: Registry,
        out_module: Path,
        function_class: str = "GLFunctions",
        api_name: str = "OpenGL",
    ):
        self._registry = registry
        self._out_module = out_module
        self._function_class = function_class
        self._api_name = api_name
        self._out = None
        self._stub = None
        self._all = []  # Entries for __all__
        self._commands = []

    def run(self):
        """Write the file and close"""
        with open(self._out_module.with_suffix(".py"), mode='w') as out:
            self.write_template(out, GEN_OPENGL_DIR / "gl.template")
            self.write_types(out)
            self.write_enums(out)
            self.write_commands(out)
            self.write_footer(out)

        with open(self._out_module.with_suffix(".pyi"), mode='w') as stub:
            self.write_template(stub, GEN_OPENGL_DIR / "gl_stub.template")
            self.write_types(stub)
            self.write_enum_stubs(stub)
            self.write_command_stubs(stub)

    def write_lines(self, fp: TextIO, lines: Iterable[str]) -> None:
        """Write one or several lines to the out file."""
        for line in lines:
            fp.write(line)
            fp.write("\n")

    def write_template(self, fp: TextIO, template: Path) -> None:
        """Write the header."""
        with open(template) as fd:
            fp.write(fd.read())

    def write_types(self, fp: TextIO) -> None:
        """Write all types."""
        self.write_lines(fp, ["# GL type definitions"])
        self.write_lines(fp, [f"{k} = {v}" for k, v in self.types.items()])
        self.write_lines(fp, [""])
        self._all.extend(self.types.keys())

    def write_enums(self, fp: TextIO) -> None:
        """Write all enums."""
        self.write_lines(fp, ["# GL enumerant/constant definitions"])
        self.write_lines(fp, [
            f"{e.name} = {e.value_int}"
            for e in sorted(self._registry.enums.values())
        ])
        self.write_lines(fp, [""])
        self._all.extend(self._registry.enums.keys())

    def write_enum_stubs(self, fp: TextIO) -> None:
        """Write type annotations for all enums."""
        self.write_lines(fp, ["# GL enumerant/constant definitions"])
        self.write_lines(fp, [
            f"{e.name}: int"  # assume all enums values are integers
            for e in sorted(self._registry.enums.values())
        ])
        self.write_lines(fp, [""])

    def _command_signature(self, cmd) -> tuple[str, str]:  # noqa: ANN001
        """Return ctypes expressions for a registry command's signature."""
        if "*" in cmd.proto:
            restype = f"POINTER({cmd.ptype})"
        else:
            restype = cmd.ptype or "None"

        arguments = []
        for param in cmd.params:
            if "void" in param.value:
                arguments.append("POINTER(GLvoid)")
            else:
                if not self.types.get(param.ptype):
                    raise ValueError(f"ptype {param.ptype} not a known type")
                if param.value.count("*") == 2:
                    arguments.append(f"POINTER(POINTER({param.ptype}))")
                elif param.value.count("*") == 1:
                    arguments.append(f"POINTER({param.ptype})")
                else:
                    arguments.append(param.ptype)

        return restype, ", ".join(arguments)

    def write_commands(self, fp: TextIO) -> None:
        """Write all commands."""
        self.write_lines(fp, ["# GL command definitions"])

        self.write_lines(fp, [
            "",
            f"class {self._function_class}:",
            '    """Functions linked for an active GL context."""',
            "",
            "    def __init__(self) -> None:",
        ])

        # _link_function params : name, restype, argtypes, requires=None, suggestions=None
        for cmd in sorted(self._registry.commands.values()):
            if cmd.name in self.exclude_commands:
                continue

            restype, argtypes = self._command_signature(cmd)
            requires = f"{self._api_name} {cmd.requires}" if cmd.requires else None
            # NOTE: PROCs are optional
            # proc_name = f"PFN{cmd.name.upper()}PROC"
            command_definition = (
                f"        self.{cmd.name} = _link_function({cmd.name!r}, {restype}, [{argtypes}], "
                f"requires={requires!r})"
            )

            self.write_lines(fp, [
                command_definition,
                # f"{proc_name} = CFUNCTYPE({restype}, {argtypes})",
            ])
            self._all.append(cmd.name)

        self.write_lines(fp, ["", "# These functions may be imported before a context is created."])
        for cmd in sorted(self._registry.commands.values()):
            if cmd.name in self.exclude_commands:
                continue

            restype, argtypes = self._command_signature(cmd)
            requires = f"{self._api_name} {cmd.requires}" if cmd.requires else None
            self.write_lines(fp, [
                f"{cmd.name} = _link_function_proxy({cmd.name!r}, {restype}, [{argtypes}], requires={requires!r})",
            ])

        self._all.append(self._function_class)
        self.write_lines(fp, [""])

    def write_footer(self, fp: TextIO) -> None:
        """Write __all__ section."""
        self.write_lines(fp, [
            "",
            "__all__ = [",
            *[f"    '{name}'," for name in self._all],
            "]",
        ])

    def write_command_stubs(self, fp: TextIO) -> None:
        """Write type annotations for all commands."""
        self.write_lines(fp, ["# GL command definitions"])
        self.write_lines(fp, ["", f"class {self._function_class}:", "    def __init__(self) -> None: ..."])

        # _link_function params : name, restype, argtypes, requires=None, suggestions=None
        for cmd in sorted(self._registry.commands.values()):
            if cmd.name in self.exclude_commands:
                continue

            # Return type: If the function returns a pointer type ...
            if "*" in cmd.proto:
                restype = f"_Pointer[{cmd.ptype}]"
            else:
                restype = cmd.ptype or "None"

            # Arguments can be pointer and pointer-pointer
            arguments = []
            names = []
            for param in cmd.params:
                # print(cmd.name, param.name, param.ptype, "|", param.value)
                names.append(param.name)

                # Detect void pointers. They don't have a ptype set
                if "void" in param.value:
                    # The exact types which are valid is hard to determine since
                    # ctypes automatically converts arguments to the required type, so allow Any
                    arguments.append("_Pointer[GLvoid] | Any")
                else:
                    # Ensure we actually know what the type is
                    if not self.types.get(param.ptype):
                        raise ValueError(f"ptype {param.ptype} not a known type")
                    # Handle pointer-pointer and pointers: *, **, *const*
                    if param.value.count("*") == 2:
                        arguments.append(f"_Pointer[_Pointer[{param.ptype}]] | Any")
                    elif param.value.count("*") == 1:
                        arguments.append(f"_Pointer[{param.ptype}] | Any")
                    else:
                        arguments.append(param.ptype)

            # Arguments can be pointer and pointer-pointer
            argannotations = ", ".join(
                f"{name}: {f'{arg} | {self.pythontypes[arg]}' if arg in self.pythontypes else arg}" for name, arg in
                zip(names, arguments, strict=True))

            function_stub = f"def {cmd.name}({argannotations}) -> {self.pythontypes.get(restype, restype)}: ..."
            self.write_lines(fp, [f"    {function_stub}"])

        self.write_lines(fp, [""])
        for cmd in sorted(self._registry.commands.values()):
            if cmd.name in self.exclude_commands:
                continue

            if "*" in cmd.proto:
                restype = f"_Pointer[{cmd.ptype}]"
            else:
                restype = cmd.ptype or "None"

            arguments = []
            names = []
            for param in cmd.params:
                names.append(param.name)
                if "void" in param.value:
                    arguments.append("_Pointer[GLvoid] | Any")
                elif param.value.count("*") == 2:
                    arguments.append(f"_Pointer[_Pointer[{param.ptype}]] | Any")
                elif param.value.count("*") == 1:
                    arguments.append(f"_Pointer[{param.ptype}] | Any")
                else:
                    arguments.append(param.ptype)

            argannotations = ", ".join(
                f"{name}: {f'{arg} | {self.pythontypes[arg]}' if arg in self.pythontypes else arg}"
                for name, arg in zip(names, arguments, strict=True)
            )
            self.write_lines(fp, [
                f"def {cmd.name}({argannotations}) -> {self.pythontypes.get(restype, restype)}: ...",
            ])


if __name__ == "__main__":
    main()
