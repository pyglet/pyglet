"""Shared writer for Khronos XML registries."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, TextIO

from opengl_registry import Registry, RegistryReader


REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
_EGL_CAST = re.compile(r"EGL_CAST\((?P<type>\w+),(?P<value>-?\d+)\)")


class KhronosWriter:
    """Write ctypes bindings for a single Khronos registry profile."""

    def __init__(self, *, registry: Registry, out_module: Path, template: Path,
                 types: dict[str, str], link_function: str, api_name: str,
                 function_class: str | None = None,
                 function_subclass: str | None = None,
                 exclude_commands: set[str] | None = None) -> None:
        self._registry = registry
        self._out_module = out_module
        self._template = template
        self._types = types
        self._link_function = link_function
        self._api_name = api_name
        self._function_class = function_class
        self._function_subclass = function_subclass
        self._exclude_commands = exclude_commands or set()
        self._all: list[str] = []

    def run(self) -> None:
        """Write the binding module."""
        self._out_module.parent.mkdir(parents=True, exist_ok=True)
        with self._out_module.open("w", encoding="utf8", newline="\n") as output:
            output.write(self._template.read_text(encoding="utf8"))
            self._write_types(output)
            self._write_enums(output)
            self._write_commands(output)
            self._write_footer(output)

    @staticmethod
    def _write_lines(output: TextIO, lines: Iterable[str]) -> None:
        for line in lines:
            output.write(line)
            output.write("\n")

    def _write_types(self, output: TextIO) -> None:
        # Avoid types that are imported from other spots.
        generated_types = {
            name: ctype for name, ctype in self._types.items() if name != ctype
        }
        self._write_lines(output, [])
        self._write_lines(output, [f"# {self._api_name} type definitions"])
        self._write_lines(output, [f"{name} = {ctype}" for name, ctype in generated_types.items()])
        self._write_lines(output, [""])
        self._all.extend(generated_types)

    def _enum_value(self, enum) -> str:  # noqa: ANN001
        """Translate registry values which are legal C but not Python literals."""
        cast = _EGL_CAST.fullmatch(enum.value)
        if cast:
            value = cast.group("value")
            return "None" if value == "0" else value
        return enum.value

    def _write_enums(self, output: TextIO) -> None:
        self._write_lines(output, [f"# {self._api_name} enumerant/constant definitions"])
        self._write_lines(output, [
            f"{enum.name} = {self._enum_value(enum)}"
            for enum in sorted(self._registry.enums.values(), key=lambda item: item.name)
        ])
        self._write_lines(output, [""])
        self._all.extend(self._registry.enums)

    def _ctype(self, ptype: str | None, value: str) -> str:
        """Return a ctypes expression for a command return value or parameter."""
        declaration = value.lstrip().removeprefix("const ")
        if ptype:
            try:
                ctype = self._types[ptype]
            except KeyError as exc:
                raise ValueError(f"ptype {ptype} is not a known {self._api_name} type") from exc
        elif (declaration_type := declaration.removeprefix("struct ").split(maxsplit=1)[0]) in self._types:
            ctype = self._types[declaration_type]
        elif "void" in value:
            ctype = "None"
        elif declaration.startswith("unsigned long"):
            ctype = "c_ulong"
        elif declaration.startswith("unsigned int"):
            ctype = "c_uint"
        elif declaration.startswith("int"):
            ctype = "c_int"
        elif declaration.startswith("char"):
            ctype = "c_char"
        else:
            raise ValueError(f"Cannot determine ctypes type for {value!r}")

        pointer_count = value.count("*")
        if declaration.startswith("char") and pointer_count == 1:
            return "c_char_p"
        if "void" in value and pointer_count:
            return "c_void_p"
        return "POINTER(" * pointer_count + ctype + ")" * pointer_count

    def _command_signature(self, command) -> tuple[str, str]:  # noqa: ANN001
        return self._ctype(command.ptype, command.proto), ", ".join(
            self._ctype(param.ptype, param.value) for param in command.params)

    def _write_commands(self, output: TextIO) -> None:
        self._write_lines(output, [f"# {self._api_name} command definitions"])
        commands = [
            command for command in sorted(self._registry.commands.values(), key=lambda item: item.name)
            if command.name not in self._exclude_commands
        ]
        for command in commands:
            restype, argtypes = self._command_signature(command)
            requires = f"{self._api_name} {command.requires}" if command.requires else None
            self._write_lines(output, [
                f"{command.name} = {self._link_function}({command.name!r}, {restype}, [{argtypes}], {requires!r})",
            ])
            self._all.append(command.name)

        if self._function_class:
            self._write_lines(output, ["", f"class {self._function_class}:", "    def __init__(self) -> None:"])
            for command in commands:
                restype, argtypes = self._command_signature(command)
                requires = f"{self._api_name} {command.requires}" if command.requires else None
                self._write_lines(output, [
                    f"        self.{command.name} = {self._link_function}({command.name!r}, "
                    f"{restype}, [{argtypes}], {requires!r})",
                ])
            self._all.append(self._function_class)
        if self._function_subclass:
            self._write_lines(output, ["", f"class {self._function_subclass}({self._function_class}):",
                                       "    def __init__(self) -> None:", "        super().__init__()"])
            self._all.append(self._function_subclass)
        self._write_lines(output, [""])

    def _write_footer(self, output: TextIO) -> None:
        self._write_lines(output, ["__all__ = [", *[f"    {name!r}," for name in self._all], "]"])


def read_profile(
    xml_file: Path,
    *,
    api: str,
    version: str,
    extensions: Iterable[str] = (),
) -> Registry:
    """Read a core profile and explicitly selected registry extensions.

    ``opengl_registry.Registry.get_profile`` only resolves extension names
    beginning with ``GL_``. Add extensions here so GLX, EGL, and WGL names work
    too (for example, ``GLX_EXT_import_context``).
    """
    registry = RegistryReader.from_file(xml_file).read()
    profile = registry.get_profile(api=api, profile="core", version=version, extensions=[])
    _add_extensions(registry, profile, api, extensions)
    return profile


def read_extensions(
    xml_file: Path,
    *,
    api: str,
    extensions: Iterable[str],
    include_extra_extensions: bool = False,
) -> Registry:
    """Read extension-only bindings for a registry API.

    When ``include_extra_extensions`` is true, all extensions for ``api`` not
    already in ``extensions`` are added. This is intentionally opt-in: some
    legacy extensions require additional platform type mappings.
    """
    registry = RegistryReader.from_file(xml_file).read()
    selected_extensions = list(extensions)
    if include_extra_extensions:
        selected_extensions.extend(
            name for name, extension in registry.extensions.items()
            if api in extension._supported.split("|") and name not in selected_extensions  # noqa: SLF001
        )

    profile = Registry(types=registry.types)
    _add_extensions(registry, profile, api, selected_extensions)
    return profile


def _add_extensions(
    registry: Registry,
    profile: Registry,
    api: str,
    extensions: Iterable[str],
) -> None:
    """Add selected extension enums and commands to ``profile``."""

    for extension_name in extensions:
        try:
            extension = registry.extensions[extension_name]
        except KeyError as exc:
            raise ValueError(f"unknown {api} extension: {extension_name}") from exc

        if api not in extension._supported.split("|"):  # noqa: SLF001
            raise ValueError(f"{extension_name} does not support the {api} API")

        for enum_name in extension.enums:
            enum = registry.get_enum(enum_name)
            if enum:
                profile.add_enum(enum)

        for command_name in extension.commands:
            command = registry.get_command(command_name)
            if command:
                command.requires = extension.name
                profile.add_command(command)
