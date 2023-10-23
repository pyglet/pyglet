# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2023 pyglet contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

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
