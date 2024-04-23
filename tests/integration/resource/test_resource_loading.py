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

import pytest

from pyglet import resource
from pyglet.util import asbytes


@pytest.fixture
def loader():
    script_home = os.path.dirname(__file__)
    return resource.Loader(script_home=script_home)


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


# Expected Failures:

def test_no_path_exception(loader):
    loader.path = []
    pytest.raises(resource.ResourceNotFoundException, loader.file, 'f1.txt')


def test_resource_not_found(loader):
    pytest.raises(resource.ResourceNotFoundException, loader.file, 'foo')


def test_invalid_filename_format(loader):
    pytest.raises((AttributeError, TypeError), loader.file, ['foo'])
