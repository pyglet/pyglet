"""Resource names inside a ZIP subdirectory are relative to that exact directory."""

import zipfile

import pytest

from pyglet.resource import Loader, ResourceNotFoundException


@pytest.fixture
def archive(tmp_path):
    path = tmp_path / "resources.zip"
    with zipfile.ZipFile(path, "w") as output:
        for name in ("assets/star.txt", "assets/atlas.txt", "assets/textures/tile.txt",
                     "assets/nested/assets.txt", "other/assets/outsider.txt", "assets-old/sibling.txt",
                     "assets.txt", "root.txt"):
            output.writestr(name, name.encode())
        output.writestr("assets/", b"")
    return path


@pytest.mark.parametrize("name", ["star.txt", "atlas.txt", "textures/tile.txt", "nested/assets.txt"])
def test_nested_archive_names_are_preserved(archive, name):
    loader = Loader([str(archive) + "/assets"])
    with loader.file(name) as source:
        assert source.read() == ("assets/" + name).encode()
    with loader.location(name).open(name, "rt") as source:
        assert source.read() == "assets/" + name


def test_nested_archive_excludes_siblings(archive):
    loader = Loader([str(archive) + "/assets"])
    loader.reindex()
    assert set(loader._index) == {"star.txt", "atlas.txt", "textures/tile.txt", "nested/assets.txt"}
    for name in ("outsider.txt", "sibling.txt", "assets.txt", "root.txt"):
        with pytest.raises(ResourceNotFoundException):
            loader.file(name)


def test_deep_archive_directory(archive):
    loader = Loader([str(archive) + "/assets/textures"])
    with loader.file("tile.txt") as source:
        assert source.read() == b"assets/textures/tile.txt"


def test_root_archive_names_are_unchanged(archive):
    loader = Loader([str(archive)])
    with loader.file("assets/star.txt") as source:
        assert source.read() == b"assets/star.txt"
    with loader.file("root.txt") as source:
        assert source.read() == b"root.txt"


@pytest.mark.parametrize("directory_first", [False, True])
def test_zip_and_directory_search_precedence(archive, tmp_path, directory_first):
    folder = tmp_path / "directory"
    folder.mkdir()
    (folder / "star.txt").write_bytes(b"directory")
    paths = [str(archive) + "/assets", str(folder)]
    if directory_first:
        paths.reverse()
    loader = Loader(paths)
    with loader.file("star.txt") as source:
        assert source.read() == (b"directory" if directory_first else b"assets/star.txt")
