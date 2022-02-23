import os
import sys
import pytest
from unittest import mock
from updater import paths

def test_is_frozen():
    not_frozen = paths.is_frozen()
    assert not_frozen == False
    sys.frozen = True
    frozen = paths.is_frozen()
    assert frozen == True
    del sys.frozen

@pytest.mark.parametrize("is_frozen, expected_result", [
    # When frozen, path should resolve to the executable file.
    (True, sys.executable),
    # When not frozen, it should resolve to the main file being run.
    (False, sys.argv[0])
])
def test_get_executable(is_frozen, expected_result):
    with mock.patch("updater.paths.is_frozen", return_value=is_frozen):
        result = paths.get_executable()
    assert result == expected_result

def test_get_executable_mac():
    old_value = paths.is_mac
    paths.is_mac = True
    sys.frozen = True
    mac_fake_items = ["python", "myapp"]
    with mock.patch("updater.paths.is_frozen", return_value=True):
        with mock.patch("os.listdir", return_value=mac_fake_items):
            result = paths.get_executable()
    assert result != sys.executable
    assert "python" not in result
    del sys.frozen
    paths.is_mac = old_value
def test_executable_directory():
    result = paths.executable_directory()
    assert result == os.path.dirname(sys.argv[0])

def test_app_path():
    result = paths.app_path()
    assert result == os.path.dirname(sys.argv[0])
    old_value = paths.is_mac
    paths.is_mac = True
    sys.frozen = True
    mac_result = paths.app_path()
    assert mac_result == os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), "..", "..", "..", ".."))
    paths.is_mac = old_value
    del sys.frozen