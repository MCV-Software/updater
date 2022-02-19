import sys
import pytest
from unittest import mock
# Fake a wx module, so we won't need a fully working WX lib for running unittests.
# ToDo: Find a way to do this better.
wx = mock.Mock(name="wx")
wx.__name__ = "wx"
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