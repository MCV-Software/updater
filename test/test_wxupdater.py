import sys
import pytest
from importlib import reload
from unittest import mock
# Fake a wx module, so we won't need a fully working WX lib for running unittests.
# ToDo: Find a way to do this better.
wx = mock.Mock(name="wx")
wx.__name__ = "wx"
# Add some styles we use in the wxupdater module
wx.YES = 2
wx.NO = 8
wx.ICON_WARNING = 256
wx.ID_YES = 5103
wx.ID_NO = 5104
sys.modules["wx"] = wx

# now, import the wxupdater.
from updater import wxupdater

def test_initial_params():
    updater = wxupdater.WXUpdater(endpoint="https://example.com/update.zip", app_name="My awesome application", current_version="0.1")
    assert updater.new_update_title == "New version for {app_name}"
    assert updater.new_update_msg == "There's a new {app_name} version available. Would you like to download it now?\n\n {app_name} version: {update_version}\n\nChanges:\n{update_description}"
    assert updater.update_progress_title == "Downloading update..."
    assert updater.update_progress_msg == "Updating... {total_downloaded} of {total_size}"
    assert updater.update_almost_complete_title == "Done"
    assert updater.update_almost_complete_msg == "The update is about to be installed in your system. After being installed, the application will restart. Press OK to continue."
    assert updater.progress_dialog == None
    del updater

def test_import_error():
    global wx
    sys.modules.pop("wx")
    reload(wxupdater)
    with pytest.raises(ModuleNotFoundError):
        updater = wxupdater.WXUpdater(endpoint="https://example.com/update.zip", app_name="My awesome application", current_version="0.1")
    sys.modules["wx"] = wx
    wxupdater.wx_present = True

def test_custom_messages():
    updater = wxupdater.WXUpdater(endpoint="https://example.com/update.zip", app_name="My awesome application", current_version="0.1", new_update_title="New update", new_update_msg="There is a new update", update_progress_title="Update progress title", update_progress_msg="Update progress message", update_almost_complete_title="Update almost complete", update_almost_complete_msg="Update almost complete message")
    assert updater.new_update_title == "New update"
    assert updater.new_update_msg == "There is a new update"
    assert updater.update_progress_title == "Update progress title"
    assert updater.update_progress_msg == "Update progress message"
    assert updater.update_almost_complete_title == "Update almost complete"
    assert updater.update_almost_complete_msg == "Update almost complete message"

def test_initialize():
    updater = wxupdater.WXUpdater(endpoint="https://example.com/update.zip", app_name="My awesome application", current_version="0.1")
    with mock.patch("pubsub.pub.subscribe") as pub_subscribe:
        updater.initialize()
        pub_subscribe.assert_called_once_with(updater.on_update_progress, "updater.update-progress")
        with mock.patch("pubsub.pub.unsubscribe") as pub_unsubscribe:
            updater.__del__()
            pub_unsubscribe.assert_called_once()

def test_create_progress_dialog():
    updater = wxupdater.WXUpdater(endpoint="https://example.com/update.zip", app_name="My awesome application", current_version="0.1")
    with mock.patch("wx.ProgressDialog") as wx_progress_dialog:
        updater.create_progress_dialog()
        assert updater.progress_dialog != None
        wx_progress_dialog.assert_called_once_with(updater.update_progress_msg.format(total_downloaded=0, total_size=0), updater.update_progress_title.format(total_downloaded=0, total_size=0), parent=None, maximum=100)

@pytest.mark.parametrize("wx_response, return_value", [(wx.ID_YES, True), (wx.ID_NO, False)])
def test_on_new_update_available(wx_response, return_value):
    updater = wxupdater.WXUpdater(endpoint="https://example.com/update.zip", app_name="My awesome application", current_version="0.1")
    wxDialog = mock.Mock()
    wxDialog.ShowModal.return_value = wx_response
    with mock.patch("wx.MessageDialog", return_value=wxDialog):
        result = updater.on_new_update_available()
        assert result == return_value
        wxDialog.ShowModal.assert_called_once()
        wxDialog.Destroy.assert_called_once()

def test_on_update_progress():
    updater = wxupdater.WXUpdater(endpoint="https://example.com/update.zip", app_name="My awesome application", current_version="0.1")
    progressDialog = mock.Mock()
    with mock.patch("wx.ProgressDialog", return_value=progressDialog):
        updater = updater.on_update_progress(0, 100)
        progressDialog.Show.assert_called_once()
        progressDialog.Update.assert_called_once()
        progressDialog.setTitle.Assert_called_once()

def test_on_update_progress_on_100_percent():
    updater = wxupdater.WXUpdater(endpoint="https://example.com/update.zip", app_name="My awesome application", current_version="0.1")
    progressDialog = mock.Mock()
    with mock.patch("wx.ProgressDialog", return_value=progressDialog):
        updater = updater.on_update_progress(100, 100)
        progressDialog.Show.assert_called_once()
        progressDialog.Destroy.assert_called_once()

def test_on_update_almost_complete():
    updater = wxupdater.WXUpdater(endpoint="https://example.com/update.zip", app_name="My awesome application", current_version="0.1")
    dialog = mock.Mock()
    with mock.patch("wx.MessageDialog", return_value=dialog):
        updater.on_update_almost_complete()
        dialog.ShowModal.assert_called_once()

@mock.patch("tempfile.mkdtemp", return_value="tmp")
def test_check_for_updates_update_available(tempfile):
    updater = wxupdater.WXUpdater(endpoint="https://example.com/update.zip", app_name="My awesome application", current_version="0.1")
    with mock.patch.object(updater, "create_session") as create_session:
        with mock.patch.object(updater, "initialize") as initialize:
            with mock.patch.object(updater, "get_update_information") as get_update_information:
                with mock.patch.object(updater, "get_version_data") as get_version_data:
                    with mock.patch.object(updater, "on_new_update_available") as on_new_update_available:
                        with mock.patch.object(updater, "download_update") as download_update:
                            with mock.patch.object(updater, "extract_update") as extract_update:
                                with mock.patch.object(updater, "move_bootstrap") as move_bootstrap:
                                    with mock.patch.object(updater, "on_update_almost_complete") as on_update_almost_complete:
                                        with mock.patch.object(updater, "execute_bootstrap") as execute_bootstrap:
                                            updater.check_for_updates()
                                            execute_bootstrap.assert_called_once()
                                        on_update_almost_complete.assert_called_once()
                                    move_bootstrap.assert_called_once()
                                extract_update.assert_called_once()
                            download_update.assert_called_once()
                        on_new_update_available.assert_called_once()
                    get_version_data.assert_called_once()
                get_update_information.assert_called_once()
            initialize.assert_called_once()
        create_session.assert_called_once()

@mock.patch("tempfile.mkdtemp", return_value="tmp")
def test_check_for_updates_no_update_available(tempfile):
    updater = wxupdater.WXUpdater(endpoint="https://example.com/update.zip", app_name="My awesome application", current_version="0.1")
    with mock.patch.object(updater, "create_session") as create_session:
        with mock.patch.object(updater, "initialize") as initialize:
            with mock.patch.object(updater, "get_update_information") as update_information:
                with mock.patch.object(updater, "get_version_data", return_value=(False, False, False)) as get_version_data:
                    result = updater.check_for_updates()
                    assert result == None
                    get_version_data.assert_called_once()

@mock.patch("tempfile.mkdtemp", return_value="tmp")
def test_check_for_updates_user_cancelled_update(tempfile):
    updater = wxupdater.WXUpdater(endpoint="https://example.com/update.zip", app_name="My awesome application", current_version="0.1")
    with mock.patch.object(updater, "create_session") as create_session:
        with mock.patch.object(updater, "initialize") as initialize:
            with mock.patch.object(updater, "get_update_information") as update_information:
                with mock.patch.object(updater, "get_version_data") as get_version_data:
                    with mock.patch.object(updater, "on_new_update_available", return_value=False) as on_new_update_available:
                        result = updater.check_for_updates()
                        assert result == None
                        on_new_update_available.assert_called_once()