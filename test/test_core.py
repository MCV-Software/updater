import sys
import os
import pytest
import requests_mock
from unittest import mock
from json.decoder import JSONDecodeError
from requests.exceptions import HTTPError
from updater import core

app_name: str = "a simple app"
current_version: str = "0.15"
endpoint: str = "https://gitlab.mcvsoftware.com"

# Fake a win32api module, as this fails on non-windows platforms without this hack.
# ToDo: Find a way to do this better.
win32api = mock.Mock(name="win32api")
win32api.__name__ = "win32api"
sys.modules["win32api"] = win32api

def test_requests_session():
    global app_name, current_version, endpoint
    updater = core.UpdaterCore(endpoint=endpoint, app_name=app_name, current_version=current_version)
    updater.create_session()
    assert hasattr(updater, "session")
    assert app_name in updater.session.headers.get("User-Agent")
    assert current_version in updater.session.headers.get("User-Agent")

def test_get_update_information_valid_json(file_data, json_data):
    global app_name, current_version, endpoint
    updater = core.UpdaterCore(endpoint=endpoint, app_name=app_name, current_version=current_version)
    updater.create_session()
    with requests_mock.Mocker(session=updater.session) as mocked:
        mocked.get(endpoint, json=json_data)
        contents = updater.get_update_information()
        assert contents == json_data

def test_get_update_information_invalid_json(file_data, json_data):
    global app_name, current_version, endpoint
    updater = core.UpdaterCore(endpoint=endpoint, app_name=app_name, current_version=current_version)
    updater.create_session()
    with requests_mock.Mocker(session=updater.session) as mocked:
        mocked.get(endpoint, text="thisisnotjson")
        with pytest.raises(JSONDecodeError):
            contents = updater.get_update_information()

def test_get_update_information_not_found():
    global app_name, current_version, endpoint
    updater = core.UpdaterCore(endpoint=endpoint, app_name=app_name, current_version=current_version)
    updater.create_session()
    with requests_mock.Mocker(session=updater.session) as mocked:
        mocked.get(endpoint, status_code=404)
        with pytest.raises(HTTPError):
            contents = updater.get_update_information()

def test_version_data_no_update(json_data):
    global app_name, endpoint
    updater = core.UpdaterCore(endpoint=endpoint, app_name=app_name, current_version=json_data.get("current_version"))
    updater.create_session()
    results = updater.get_version_data(json_data)
    assert results == (False, False, False)

@pytest.mark.parametrize("platform, architecture", [
    ("Windows", ("32bit", "")),
    ("Windows", ("64bit", "")),
])
def test_version_data_update_available(json_data, platform, architecture):
    global app_name, current_version, endpoint
    updater = core.UpdaterCore(endpoint=endpoint, app_name=app_name, current_version=current_version)
    updater.create_session()
    with mock.patch("platform.system", return_value=platform):
        with mock.patch("platform.architecture", return_value=architecture):
            results = updater.get_version_data(json_data)
            k = platform+architecture[0][:2]
            assert results == (json_data["current_version"], json_data["description"], json_data["downloads"][k])

def test_version_data_architecture_not_found(json_data):
    global app_name, current_version, endpoint
    updater = core.UpdaterCore(endpoint=endpoint, app_name=app_name, current_version=current_version)
    updater.create_session()
    with mock.patch("platform.system", return_value="nonos"):
        with mock.patch("platform.architecture", return_value=("31bits", "")):
            with pytest.raises(KeyError):
                results = updater.get_version_data(json_data)

def test_download_update():
    global app_name, current_version, endpoint
    updater = core.UpdaterCore(endpoint=endpoint, app_name=app_name, current_version=current_version)
    updater.create_session()
    with mock.patch("pubsub.pub.sendMessage") as sendMessage_mock:
        with mock.patch("io.open") as open_mock:
            with requests_mock.Mocker(session=updater.session) as mocker:
                updatefile = os.path.join(os.path.dirname(__file__), "helloworld_v2_win64.zip")
                mocker.get("http://downloads.update.org/update.zip", body=open(updatefile, "rb"))
                result = updater.download_update(update_url="http://downloads.update.org/update.zip", update_destination="update.zip")
                open_mock.assert_called_once_with("update.zip", "w+b")
                assert result == "update.zip"
                assert sendMessage_mock.call_count > 0

def test_extract_archive():
    # This only tests if archive extraction methods were called successfully and with the right parameters.
    global app_name, current_version, endpoint
    updater = core.UpdaterCore(endpoint=endpoint, app_name=app_name, current_version=current_version)
    zipfile_opened = mock.MagicMock()
    with mock.patch("zipfile.ZipFile", return_value=zipfile_opened) as zipfile_mock:
        result = updater.extract_update("update.zip", os.path.dirname(__file__))
        assert result == os.path.dirname(__file__)
        zipfile_mock.called_once_with("update.zip")
        zipfile_opened.extractall.assert_called_once()
    # Test a password protected update file.
    zipfile_opened_with_password = mock.MagicMock()
    with mock.patch("zipfile.ZipFile", return_value=zipfile_opened_with_password) as zipfile_mock:
        # Set a password manually.
        updater.password = "MyLongPassword"
        result2 = updater.extract_update("update.zip", os.path.dirname(__file__))
        assert result2 == os.path.dirname(__file__)
        zipfile_mock.called_once_with("update.zip")
        zipfile_opened_with_password.setpassword.called_once_with("MyLongPassword")
        zipfile_opened_with_password.extractall.assert_called_once()

@pytest.mark.parametrize("system", [("Windows"), ("Darwin"), ("Linux")])
def test_move_bootstrap(system):
    global app_name, current_version, endpoint
    updater = core.UpdaterCore(endpoint=endpoint, app_name=app_name, current_version=current_version)
    # provide a fake extraction path.
    extracted_path = os.path.dirname(__file__)
    # supposedly, the bootstrap file should be moved to the parent path.

    with mock.patch("platform.system", return_value=system):
            with mock.patch("os.rename") as os_rename:
                expected_path = os.path.abspath(os.path.join(extracted_path, "..", updater.bootstrap_name()))
                result = updater.move_bootstrap(extracted_path)
                assert result == expected_path
                os_rename.assert_called_once()

@pytest.mark.parametrize("system", [("Windows"), ("Darwin"), ("Linux")])
def test_execute_bootstrap(system):
    global app_name, current_version, endpoint
    updater = core.UpdaterCore(endpoint=endpoint, app_name=app_name, current_version=current_version)
    with mock.patch("platform.system", return_value=system):
        with mock.patch("os.stat") as os_stat:
            with mock.patch("subprocess.Popen") as subprocess_popen:
                with mock.patch("os.chmod") as os_chmod:
                    with mock.patch("win32api.ShellExecute") as  win32api_ShellExecute:
                        bootstrap_path = os.path.join(os.path.dirname(__file__), updater.bootstrap_name())
                        source_path = os.path.dirname(__file__)
                        updater.execute_bootstrap(bootstrap_path, source_path)
                        if system == "Windows":
                            win32api_ShellExecute.assert_called_once()
                        else:
                            os_chmod.assert_called_once()
                            os_stat.assert_called_once()
                            subprocess_popen.assert_called_once()

@pytest.mark.parametrize("system, bootstrap_file", [
        ("Windows", "bootstrap.exe"),
        ("Darwin", "bootstrap-mac.sh"),
        ("Linux", "bootstrap-lin.sh")
    ])
def test_bootstrap_name(system, bootstrap_file):
    global app_name, current_version, endpoint
    updater = core.UpdaterCore(endpoint=endpoint, app_name=app_name, current_version=current_version)
    with mock.patch("platform.system", return_value=system):
        result = updater.bootstrap_name()
        assert result == bootstrap_file
