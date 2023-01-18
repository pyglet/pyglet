from collections import namedtuple

CustomField = namedtuple("CustomField", "fields removals")

# Versions of the loaded libraries
versions = {
    'avcodec': 0,
    'avformat': 0,
    'avutil': 0,
    'swresample': 0,
    'swscale': 0,
}

# Group codecs by version they are usually packaged with.
release_versions = [
    {'avcodec': 58, 'avformat': 58, 'avutil': 56, 'swresample': 3, 'swscale': 5},
    {'libavcodec': 59, 'avformat': 59, 'avutil': 57, 'swresample': 4, 'swscale': 6}
]

# Removals done per library and version.
_version_changes = {
    'avcodec': {},
    'avformat': {},
    'avutil': {},
    'swresample': {},
    'swscale': {}
}


def set_version(library, version):
    versions[library] = version


def add_version_changes(library, version, structure, fields, removals):
    if version not in _version_changes[library]:
        _version_changes[library][version] = {}

    if structure in _version_changes[library][version]:
        raise Exception("Structure: {} from: {} has already been added for version {}.".format(structure,
                                                                                               library,
                                                                                               version)
                        )

    _version_changes[library][version][structure] = CustomField(fields, removals)


def apply_version_changes():
    """Apply version changes to Structures in FFmpeg libraries.
       Field data can vary from version to version, however assigning _fields_ automatically assigns memory.
       _fields_ can also not be re-assigned. Use a temporary list that can be manipulated before setting the
       _fields_ of the Structure."""

    for library, data in _version_changes.items():
        for version in data:
            for structure, cf_data in _version_changes[library][version].items():
                if versions[library] == version:
                    if cf_data.removals:
                        for remove_field in cf_data.removals:
                            for field in list(cf_data.fields):
                                if field[0] == remove_field:
                                    cf_data.fields.remove(field)

                    structure._fields_ = cf_data.fields
