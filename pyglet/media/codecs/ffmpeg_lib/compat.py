from __future__ import annotations

import warnings
from typing import Any, NamedTuple, Protocol, Sequence, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ctypes import Structure


LibraryName = str
Version = int
FieldDef = Tuple[str, Any]

class Reposition(NamedTuple):
    field: str
    after: str


class CustomField(NamedTuple):
    fields: list[FieldDef]
    removals: list[str]
    repositions: list[Reposition] | None


# Versions of the loaded libraries
versions: dict[LibraryName, Version] = {
    'avcodec': 0,
    'avformat': 0,
    'avutil': 0,
    'swresample': 0,
    'swscale': 0,
}

# Group codecs by version they are usually packaged with.
release_versions: dict[Version, dict[LibraryName, Version]] = {
    4: {'avcodec': 58, 'avformat': 58, 'avutil': 56, 'swresample': 3, 'swscale': 5},  # 4.x
    5: {'avcodec': 59, 'avformat': 59, 'avutil': 57, 'swresample': 4, 'swscale': 6},  # 5.x
    6: {'avcodec': 60, 'avformat': 60, 'avutil': 58, 'swresample': 4, 'swscale': 7},  # 6.x
    7: {'avcodec': 61, 'avformat': 61, 'avutil': 59, 'swresample': 5, 'swscale': 8},  # 7.x
    8: {'avcodec': 62, 'avformat': 62, 'avutil': 60, 'swresample': 6, 'swscale': 9},  # 8.x
}

# Removals done per library and version.
_version_changes: dict[LibraryName, dict[Version, dict[type[Structure], CustomField]]] = {
    'avcodec': {},
    'avformat': {},
    'avutil': {},
    'swresample': {},
    'swscale': {}
}


def set_version(library: LibraryName, version: Version) -> None:  # noqa: D103
    versions[library] = version


def add_version_changes(  # noqa: D103
        library: LibraryName,
        version: Version,
        structure: type[Structure],
        fields: list[FieldDef],
        removals: Sequence[str] | None,
        repositions: Sequence[Reposition] | None = None,
) -> None:
    if version not in _version_changes[library]:
        _version_changes[library][version] = {}

    if structure in _version_changes[library][version]:
        msg = f"Structure: {structure} from: {library} has already been added for version {version}."
        raise Exception(msg)

    _version_changes[library][version][structure] = CustomField(
        fields, list(removals) if removals else None, list(repositions) if repositions else None)


def apply_version_changes() -> None:
    """Apply version changes to Structures in FFMpeg libraries.

    Field data can vary from version to version, however assigning _fields_ automatically assigns memory.
    _fields_ can also not be re-assigned. Use a temporary list that can be manipulated before setting the
    _fields_ of the Structure.
    """
    for library, data in _version_changes.items():
        for version in data:
            for structure, cf_data in _version_changes[library][version].items():
                if versions[library] == version:
                    if cf_data.removals:
                        for remove_field in cf_data.removals:
                            for field in list(cf_data.fields):
                                if field[0] == remove_field:
                                    cf_data.fields.remove(field)

                    if cf_data.repositions:
                        for reposition in cf_data.repositions:
                            moved_field: FieldDef | None = None
                            insert_index: int | None = None
                            for idx, field in enumerate(list(cf_data.fields)):
                                if field[0] == reposition.field:
                                    moved_field = field
                                elif field[0] == reposition.after:
                                    insert_index = idx

                            if moved_field is not None and insert_index is not None:
                                cf_data.fields.remove(moved_field)
                                cf_data.fields.insert(insert_index + 1, moved_field)
                            else:
                                warnings.warn(f"{reposition} for {library} was not able to be processed.")

                    structure._fields_ = cf_data.fields
