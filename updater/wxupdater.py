# -*- coding: utf-8 -*-
""" Updater implementation that supports WXPython phoenix.

This module allows you to perform authomatic updates via the updater package by instantiating the :py:class:`WXUpdater` class and calling to the :py:func:`WXUpdater.check_for_updates` function, which retrieves update information from the provided server, ask the user to authorize the update if needed, and displays a progress bar while the update downloads.

:note:
    You need to have the WXPython library installed in your system. If you are not using this graphical user interface, probably you might use another update implementation.

Automatic updates can be implemented, within a WXPython application, in the following way:

    >>> import wx
    >>> from updater.wxupdater import WXUpdater
    >>> app = wx.App()
    >>> updater = WXUpdater(app_name="My app", current_version="0.1", endpoint="https://some_url.com")
    >>> updater.check_for_updates()
    >>> app.MainLoop()

Also, you can customize messages in the update dialogs via the parameters :py:data:`WXUpdater.new_update_title`, :py:data:`WXUpdater.new_update_msg`, :py:data:`WXUpdater.update_progress_title`, :py:data:`WXUpdater.update_progress_msg`, :py:data:`WXUpdater.update_almost_complete_title` and :py:data:`WXUpdater.update_almost_complete_msg`,

    >>> import wx
    >>> from updater.wxupdater import WXUpdater
    >>> app = wx.App()
    >>> updater = WXUpdater(app_name="My app", current_version="0.1", endpoint="https://some_url.com")
    >>> updater.new_update_title = "New version of my awesome app is available"
    >>> updater.new_update_msg = "Do you want to get it right now?"
    >>> updater.check_for_updates()
    >>> app.MainLoop()
"""

import os
import tempfile
import wx # type: ignore
import logging
from typing import Optional, Any, cast
from pubsub import pub # type: ignore
from pubsub.core.topicexc import TopicNameError
from platform_utils import paths # type: ignore
from . import core, utils

log = logging.getLogger("updater.WXUpdater")

class WXUpdater(core.UpdaterCore):
    """ Class to implement updates via a WXPython interface.

    :ivar new_update_title: Title to display in the dialog when a new update is available.
    :ivar new_update_msg: Text to display to users when an update is available. This text is displayed in a message box. It supports the following variables: {app_name}, {update_version} and {description} which are provided by the update information.
    :ivar update_progress_title: Title to display when the update is in progress. Available variables are {total_downloaded} and {total_size}, which are human readable strings of data downloaded.
    :ivar update_progress_msg: Text to display while update is downloading. Available variables are {total_downloaded} and {total_size}, which are human readable strings of data downloaded.
    :ivar update_almost_complete_title: Title of the message to display to users when the update is about to be installed.
    :ivar update_almost_complete_msg: Message to explain to users about the application restart, after updates are applied.
    """

    new_update_title: str = "New version for {app_name}"
    new_update_msg: str = "There's a new {app_name} version available. Would you like to download it now?\n\n {app_name} version: {update_version}\n\nChanges:\n{update_description}"
    update_progress_title: str = "Downloading update..."
    update_progress_msg: str = "Updating... {total_downloaded} of {total_size}"
    update_almost_complete_title: str = "Done"
    update_almost_complete_msg: str = "The update is about to be installed in your system. After being installed, the application will restart. Press OK to continue."

    def __init__(self, new_update_title: Optional[str] = None, new_update_msg: Optional[str] = None, update_progress_title: Optional[str] = None, update_progress_msg: Optional[str] = None, update_almost_complete_title: Optional[str] = None, update_almost_complete_msg: Optional[str] = None, *args, **kwargs):
        """ class constructor.

        It accepts all parameters required by :py:class:`updater.core.UpdaterCore`, plus the following:

        :param new_update_title: Title to display in the dialog when a new update is available.
        :type new_update_title: str
        :param new_update_msg: Text to display to users when an update is available. This text is displayed in a message box. It supports the following variables: {app_name}, {update_version} and {description} which are provided by the update information.
        :type new_update_msg: str
        :param update_progress_title: Title to display when the update is in progress. Available variables are {total_downloaded} and {total_size}, which are human readable strings of data downloaded.
        :type update_progress_title: str
        :param update_progress_msg: Text to display while update is downloading. Available variables are {total_downloaded} and {total_size}, which are human readable strings of data downloaded.
        :type update_progress_msg: str
        :param update_almost_complete_title: Title of the message to display to users when the update is about to be installed.
        :type update_almost_complete_title: str
        :param update_almost_complete_msg: Message to explain to users about the application restart, after updates are applied.
        :type update_almost_complete_msg: str
        """
        super(WXUpdater, self).__init__(*args, **kwargs)
        if new_update_title:
            self.new_update_title = new_update_title
        if new_update_msg:
            self.new_update_msg = new_update_msg
        if update_progress_title:
            self.update_progress_title = update_progress_title
        if update_progress_msg:
            self.update_progress_msg
        if update_almost_complete_title:
            self.update_almost_complete_title = update_almost_complete_title
        if update_almost_complete_msg:
            self.update_almost_complete_msg = update_almost_complete_msg
        self.progress_dialog: Any = None

    def initialize(self) -> None:
        """ Inits pubsub events for the updater, subscribing to the 'updater.update-progress' message. """
        pub.subscribe(self.on_update_progress, "updater.update-progress")

    def create_progress_dialog(self) -> None:
        """ Creates the update progress dialog that will be shown to users during download. """
        self.progress_dialog = wx.ProgressDialog(self.update_progress_msg.format(total_downloaded="0", total_size="0"), self.update_progress_title,  parent=None, maximum=100)

    def on_new_update_available(self) -> bool:
        """ Displays a dialog informing about a new update available, and asking whether user wants to download it.

        This function is called when :py:func:`wxupdater.WXUpdater.check_for_updates` triggers a new update.

        :returns: True if user wants to download the update, False otherwise.
        :rtype: bool
        """
        dialog = wx.MessageDialog(None, self.new_update_msg, self.new_update_title, style=wx.YES|wx.NO|wx.ICON_WARNING)
        response = dialog.ShowModal()
        dialog.Destroy()
        if response == wx.ID_YES:
            return True
        else:
            return False

    def on_update_progress(self, total_downloaded: int, total_size: int) -> None:
        """ callback function used to update the wx progress dialog.

        This function receives pubsub events sent by :py:func:`updater.core.UpdaterCore.download_update`.
        """
        if self.progress_dialog == None:
            self.create_progress_dialog()
            self.progress_dialog.Show()
        if total_downloaded == total_size:
            self.progress_dialog.Destroy()
        else:
            self.progress_dialog.Update((total_downloaded*100)/total_size, self.update_progress_msg.format(total_downloaded=utils.convert_bytes(total_downloaded), total_size=utils.convert_bytes(total_size)))
            self.progress_dialog.SetTitle(self.update_progress_msg.format(total_downloaded=utils.convert_bytes(total_downloaded), total_size=utils.convert_bytes(total_size)))

    def on_update_almost_complete(self) -> None:
        """ Displays a dialog informing the user about the app going to be restarted soon.

        This function is executed when the update is about to be installed. Once user accepts the dialog, the bootstrap file will be run and the app will restart.
        """
        ms = wx.MessageDialog(None, self.update_almost_complete_msg, self.update_almost_complete_title)
        return ms.ShowModal()

    def check_for_updates(self) -> None:
        """ Check for updates.

        This is the only function that should be executed from this class from outside of the updater package.

        It checks for updates based in the parameters passed during instantiation.

        If there are updates available, displays a dialog to confirm the download of update. If the update downloads successfully, it also extracts and installs it.
        """
        self.create_session()
        self.initialize()
        update_info = self.get_update_information()
        version_data = self.get_version_data(update_info)
        if version_data[0] == False:
            return None
        response = self.on_new_update_available()
        if response == False:
            return None
        base_path = tempfile.mkdtemp()
        print(base_path)
        download_path = os.path.join(base_path, 'update.zip')
        downloaded = self.download_update(cast(str, version_data[2]), download_path)
        update_path = os.path.join(base_path, 'update')
        extraction_path = self.extract_update(downloaded, destination=update_path)
        bootstrap_exe = self.move_bootstrap(extraction_path)
        source_path = os.path.join(paths.app_path(), "sandbox")
        self.on_update_almost_complete()
        self.execute_bootstrap(bootstrap_exe, source_path)

    def __del__(self) -> None:
        """ Unsubscribe events before deleting this object. """
        try:
            pub.unsubscribe(self.on_update_progress, "updater.update-progress")
        except TopicNameError:
            pass