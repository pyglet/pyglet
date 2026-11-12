"""
Layout:

.                               (file home)
    f1.txt                          F1
    dir1/
        f2.txt                      F2
        dir1/
            f3.txt                  F3
        res.zip/
            f7.txt                  F7
            dir1/
                f8.txt              F8
                dir1/
                    f9.txt          F9
    dir2/
        f6.txt                      F6

"""

import os
from pathlib import Path
from zipfile import ZipFile
from builtins import open as builtin_open
from unittest import mock

import pytest

import pyglet.font
import pyglet.image
import pyglet.media
import pyglet.model
from pyglet import resource
from pyglet.util import DecodeException, asbytes

TEST_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))


@pytest.fixture
def loader():
    script_home = os.path.dirname(__file__)
    return resource.Loader(script_home=script_home)


@pytest.fixture
def data_loader():
    return resource.Loader(pathlist=[TEST_DATA_PATH])


@pytest.fixture
def opened_files(monkeypatch):
    files = []

    def track_open(filename, *args, **kwargs):
        fileobj = builtin_open(filename, *args, **kwargs)
        files.append((os.path.normcase(os.path.normpath(os.path.abspath(filename))), fileobj))
        return fileobj

    monkeypatch.setattr('builtins.open', mock.Mock(side_effect=track_open))
    return files


def assert_file_closed(opened_files, relative_path):
    path = os.path.normcase(os.path.normpath(os.path.join(TEST_DATA_PATH, relative_path)))
    matching_files = [fileobj for filename, fileobj in opened_files if filename == path]
    assert matching_files
    assert all(fileobj.closed for fileobj in matching_files)


def get_open_file(opened_files, relative_path):
    path = os.path.normcase(os.path.normpath(os.path.join(TEST_DATA_PATH, relative_path)))
    return next(fileobj for filename, fileobj in opened_files if filename == path)


def test_base_path_only(loader):
    assert loader.file('f1.txt').read().strip() == asbytes('F1')


def test_blank_base_path(loader):
    loader.path = ['']
    assert loader.file('f1.txt').read().strip() == asbytes('F1')


def test_unused_paths(loader):
    loader.path = ['foo', 'bar', '.']
    assert loader.file('f1.txt').read().strip() == asbytes('F1')


def test_subfolder(loader):
    loader.path = ['dir1', 'dir2']
    assert loader.file('f2.txt').read().strip() == asbytes('F2')
    assert loader.file('f6.txt').read().strip() == asbytes('F6')


def test_subfolder_trailing_slash(loader):
    loader.path = ['dir1/', 'dir2/']
    assert loader.file('f2.txt').read().strip() == asbytes('F2')
    assert loader.file('f6.txt').read().strip() == asbytes('F6')


def test_sub_subfolder(loader):
    loader.path = ['dir1/dir1']
    assert loader.file('f3.txt').read().strip() == asbytes('F3')


def test_sub_subfolder_trailing_slash(loader):
    loader.path = ['dir1/dir1/']
    assert loader.file('f3.txt').read().strip() == asbytes('F3')


@pytest.mark.parametrize('root', ['', 'assets/sub', 'assets/sub/'])
def test_zip_search_root_preserves_names_and_ancestry(tmp_path: Path, root: str) -> None:
    archive = tmp_path / 'assets.zip'
    contents = {
        'assets/sub/test.txt': b'nested',
        'assets/sub/assets.txt': b'name shares prefix characters',
        'assets/sub/deeper/test.txt': b'deeper',
        'other/assets/sub/foreign.txt': b'unrelated',
        'assets/submarine/sibling.txt': b'sibling',
        'assets/sub': b'same name as directory',
    }
    with ZipFile(archive, 'w') as zip_file:
        for name, data in contents.items():
            zip_file.writestr(name, data)

    loader = resource.Loader(pathlist=[str(archive) + '/' + root])
    loader.reindex()
    prefix = root.rstrip('/') + '/' if root else ''
    expected = {name[len(prefix):]: data for name, data in contents.items() if name.startswith(prefix)}
    location = loader.location(next(iter(expected)))
    try:
        assert set(loader._index) == set(expected)
        for name, data in expected.items():
            with loader.file(name) as file:
                assert file.read() == data
    finally:
        location.zip.close()


def test_zipfile(loader):
    loader.path = ['dir1/res.zip']
    assert loader.file('f7.txt').read().strip() == asbytes('F7')


def test_zipfile_trailing_slash(loader):
    loader.path = ['dir1/res.zip/']
    assert loader.file('f7.txt').read().strip() == asbytes('F7')


def test_zipfile_subdirs(loader):
    loader.path = ['dir1/res.zip/dir1', 'dir1/res.zip/dir1/dir1/']
    assert loader.file('f8.txt').read().strip() == asbytes('F8')
    assert loader.file('f9.txt').read().strip() == asbytes('F9')


def test_reindex_after_path_change(loader):
    loader.path = ['dir1']
    loader.reindex()
    assert loader.file('f2.txt').read().strip() == asbytes('F2')
    with pytest.raises(resource.ResourceNotFoundException):
        loader.file('f6.txt')

    loader.path = ['dir2']
    loader.reindex()
    assert loader.file('f6.txt').read().strip() == asbytes('F6')
    with pytest.raises(resource.ResourceNotFoundException):
        loader.file('f2.txt')


# Expected Failures:

def test_no_path_exception(loader):
    loader.path = []
    pytest.raises(resource.ResourceNotFoundException, loader.file, 'f1.txt')


def test_resource_not_found(loader):
    pytest.raises(resource.ResourceNotFoundException, loader.file, 'foo')


def test_invalid_filename_format(loader):
    pytest.raises((AttributeError, TypeError), loader.file, ['foo'])


def test_file_remains_caller_owned(loader):
    fileobj = loader.file('f1.txt')

    assert fileobj.read().strip() == asbytes('F1')
    assert not fileobj.closed
    fileobj.close()


def test_loads_static_resources_from_test_data(data_loader, opened_files, test_window):
    image = data_loader.image('images/rgba.png')
    assert_file_closed(opened_files, 'images/rgba.png')

    document = data_loader.text('media/README')
    assert_file_closed(opened_files, 'media/README')

    data_loader.add_font('fonts/action_man.ttf')
    assert_file_closed(opened_files, 'fonts/action_man.ttf')

    audio = data_loader.audio('media/alert.wav', streaming=False)
    assert_file_closed(opened_files, 'media/alert.wav')

    scene = data_loader.scene('models/logo3d.obj')
    assert_file_closed(opened_files, 'models/logo3d.obj')

    assert isinstance(image, pyglet.image.ImageData)
    assert image.width > 0 and image.height > 0
    assert document.text.startswith('The .wav files')
    assert pyglet.font.have_font('Action Man')
    assert isinstance(audio, pyglet.media.StaticSource)
    assert isinstance(scene, pyglet.model.Scene)


def test_loads_animation_from_test_data(data_loader, opened_files, test_window):
    try:
        animation = data_loader.animation('images/dinosaur.gif')
    except DecodeException:
        assert_file_closed(opened_files, 'images/dinosaur.gif')
        pytest.skip('GIF decoder is not available on this platform.')

    assert_file_closed(opened_files, 'images/dinosaur.gif')
    assert animation.frames


def test_loads_shader_from_test_data(data_loader, opened_files, test_window):
    shader = data_loader.shader('resource_loader_test.vert')

    assert_file_closed(opened_files, 'resource_loader_test.vert')
    assert shader.shader_type == 'vertex'
    shader.delete()


def test_loads_streaming_media_from_test_data(data_loader, opened_files):
    source = data_loader.audio('media/alert.wav', streaming=True)

    assert isinstance(source, pyglet.media.StreamingSource)
    assert not get_open_file(opened_files, 'media/alert.wav').closed


@pytest.mark.parametrize('archive', [False, True])
def test_shared_locations_and_search_precedence(tmp_path: Path, archive: bool) -> None:
    roots: list[str] = []
    archive_path = tmp_path / 'resources.zip'
    for directory in ('first', 'second'):
        files = {'common.txt': directory, f'{directory}.txt': directory,
                 'nested/child.txt': directory}
        if archive:
            with ZipFile(archive_path, 'a') as zip_file:
                for name, content in files.items():
                    zip_file.writestr(f'{directory}/{name}', content)
            roots.append(f'{archive_path}/{directory}')
        else:
            root = tmp_path / directory
            for name, content in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            roots.append(str(root))

    loader = resource.Loader(pathlist=roots)
    loader.reindex()
    first = loader.location('first.txt')
    second = loader.location('second.txt')
    try:
        assert first is not second
        assert loader.location('common.txt') is first
        assert loader.location('nested/child.txt') is first
        for name in ('common.txt', 'first.txt', 'nested/child.txt'):
            with loader.file(name) as file:
                assert file.read() == b'first'
        with loader.file('second.txt') as file:
            assert file.read() == b'second'

        loader.path.reverse()
        loader.reindex()
        assert loader.location('common.txt') is loader.location('second.txt')
        with loader.file('common.txt') as file:
            assert file.read() == b'second'
    finally:
        if archive:
            locations = (first, second, loader.location('first.txt'), loader.location('second.txt'))
            for location in locations:
                location.zip.close()

