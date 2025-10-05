from collections import namedtuple

CustomField = namedtuple("CustomField", "fields removals repositions")
Reposition = namedtuple("Reposition", "field after")

# Versions of the loaded libraries
versions = {
    'avcodec': 0,
    'avformat': 0,
    'avutil': 0,
    'swresample': 0,
    'swscale': 0,
}

# Group codecs by version they are usually packaged with.
release_versions = {
    4: {'avcodec': 58, 'avformat': 58, 'avutil': 56, 'swresample': 3, 'swscale': 5},  # 4.x
    5: {'avcodec': 59, 'avformat': 59, 'avutil': 57, 'swresample': 4, 'swscale': 6},  # 5.x
    6: {'avcodec': 60, 'avformat': 60, 'avutil': 58, 'swresample': 4, 'swscale': 7},  # 6.x
    7: {'avcodec': 61, 'avformat': 61, 'avutil': 59, 'swresample': 5, 'swscale': 8},  # 7.x
    8: {'avcodec': 62, 'avformat': 62, 'avutil': 60, 'swresample': 6, 'swscale': 9},  # 8.x
}

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


def add_version_changes(library, version, structure, fields, removals, repositions=None):
    if version not in _version_changes[library]:
        _version_changes[library][version] = {}

    if structure in _version_changes[library][version]:
        raise Exception("Structure: {} from: {} has already been added for version {}.".format(structure,
                                                                                               library,
                                                                                               version)
                        )

    _version_changes[library][version][structure] = CustomField(fields, removals, repositions)


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

                    if cf_data.repositions:
                        for reposition in cf_data.repositions:
                            data = None
                            insertId = None
                            for idx, field in enumerate(list(cf_data.fields)):
                                if field[0] == reposition.field:
                                    data = field
                                elif field[0] == reposition.after:
                                    insertId = idx

                            if data and insertId:
                                cf_data.fields.remove(data)
                                cf_data.fields.insert(insertId+1, data)
                            else:
                                print(f"Warning: {reposition} for {library} was not able to be processed.")

                    structure._fields_ = cf_data.fields
