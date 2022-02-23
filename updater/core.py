""" Base class implementation for core features present in the updater module.

This is the updater core class which provides all facilities other implementation should rely in.
This class should not be used directly, use a derived class instead.
"""
import contextlib
import io
import os
import platform
import zipfile
import logging
import json
import urllib.request
from pubsub import pub # type: ignore
from typing import Optional, Dict, Tuple, Union, Any
from . import paths
log = logging.getLogger("updater.core")

class UpdaterCore(object):
    """ Base class for all updater implementations.

    Implementations must add user interaction methods and call logic for all methods present in this class.
    """

    def __init__(self, endpoint: str, current_version: str, app_name: str = "", password: Optional[bytes] = None) -> None:
        """ 
        :param endpoint: The URl endpoint where the module should retrieve update information. It must return a json valid response or a non 200 HTTP status code.
        :type endpoint: str
        :param current_version: Application's current version.
        :type current_version: str
        :param app_name: Name of the application.
            (default is empty)
        :type app_name: str
        :param password: Password for update zipfile.
        :type password: bytes
        """
        self.endpoint = endpoint
        self.current_version = current_version
        self.app_name = app_name
        self.password = password

    def get_update_information(self) -> Dict[str, Any]:
        """ Calls the provided URL endpoint and returns information about the available update sent by the server. The format should adhere to the json specifications for updates.

        If the server returns a status code different to 200 or the json file is not valid, this will raise either a :py:exc:`urllib.error.HTTPError` or a :external:py:exc:`json.JSONDecodeError`.

        :rtype: dict
        """
        response = urllib.request.urlopen(self.endpoint)
        data: str = response.read()
        content: Dict[str, Any] = json.loads(data)
        return content

    def get_version_data(self, content: Dict[str, Any]) -> Tuple[Union[bool, str], Union[bool, str], Union[bool, str]]:
        """ Parses the dictionary returned by :py:func:`updater.core.updaterCore.get_update_information` and, if there is a new update available, returns information about it in a tuple.

        the module checks whether :py:attr:`updater.core.updaterCore.current_version` is different to the version reported in the update file, and the json specification file contains a binary link for the user's architecture. If both of these conditions are True, a tuple is returned with (new_version, update_description, update_url).

        If there is no update available,  a tuple with Falsy values is returned.

        This method can raise a KeyError if there are no updates for the current architecture defined in the update file.

        :returns: tuple with update information or False values.
        :rtype: tuple
        """
        available_version = content["current_version"]
        update_url_key = platform.system()+platform.architecture()[0][:2]
        if available_version == self.current_version:
            return (False, False, False)
        if content["downloads"].get(update_url_key) == None:
            log.error("Update file doesn't include architecture {}".format(update_url_key))
            raise KeyError("Update file doesn't include current architecture.")
        available_description = content["description"]
        update_url = content ['downloads'][update_url_key]
        return (available_version, available_description, update_url)

    def download_update(self, update_url: str, update_destination: str, chunk_size: int = io.DEFAULT_BUFFER_SIZE) -> str:
        """ Downloads an update URL and notifies all subscribers of the download progress.

        This function will send a pubsub notification every time the download progress updates by using :py:func:`pubsub.pub.sendMessage` under the topic "updater.update-progress".
        You might subscribe to this notification by using :py:func:`pubsub.pub.subscribe` with a function with this signature:

        ``def receive_progress(total_downloaded: int, total_size: int):``

        In this function, it is possible to update the UI progress bar if needed.
        Don't forget to call :py:func:`pubsub.pub.unsubscribe` at the end of the update.

        :param update_url: Direct link to update zip file.
        :type update_url: str
        :param update_destination: Destination path to save the update file
        :type update_destination: str
        :param chunk_size: chunk size for downloading the update (default to :py:data:`io.DEFAULT_BUFFER_SIZE`)
        :type chunk_size: int
        :returns: The update file path in the system.
        :rtype: str
        """
        def _download_callback(transferred_blocks, block_size, total_size):
            total_downloaded = transferred_blocks*block_size
            pub.sendMessage("updater.update-progress", total_downloaded=total_downloaded, total_size=total_size)

        filename, headers = urllib.request.urlretrieve(update_url, update_destination, _download_callback)
        log.debug("Update downloaded")
        return update_destination

    def extract_update(self, update_archive: str, destination: str) -> str:
        """ Given an update archive, extracts it. Returns the directory to which it has been extracted.

        :param update_archive: Path to the update file.
        :type update_archive: str
        :param destination: Path to extract the archive. User must have permission to do file operations on the path.
        :type destination: str
        :returns: Path where the archive has been extracted.
        :rtype: str
        """
        with contextlib.closing(zipfile.ZipFile(update_archive)) as archive:
            if self.password:
                archive.setpassword(self.password)
            archive.extractall(path=destination)
        log.debug("Update extracted")
        return destination

    def move_bootstrap(self, extracted_path: str) -> str:
        """ Moves the bootstrapper binary from the update extraction folder to a working path, so it will be able to perform operations under the update directory later.

        :param extracted_path: Path to which the update file has been extracted.
        :type extracted_path: str
        :returns: The path to the bootstrap binary to be run to actually perform the update.
        :rtype: str
        """
        working_path = os.path.abspath(os.path.join(extracted_path, '..'))
        if platform.system() == 'Darwin':
            extracted_path = os.path.join(extracted_path, 'Contents', 'Resources')
        downloaded_bootstrap = os.path.join(extracted_path, self.bootstrap_name())
        new_bootstrap_path = os.path.join(working_path, self.bootstrap_name())
        os.rename(downloaded_bootstrap, new_bootstrap_path)
        return new_bootstrap_path

    def execute_bootstrap(self, bootstrap_path: str, source_path: str) -> None:
        """ Executes the bootstrapper binary, which will move the files from the update directory to the app folder, finishing with the update process.

        :param bootstrap_path: Path to the bootstrap binary that will perform the update, as returned by :py:func:`move_bootstrap`
        :type bootstrap_path: str
        :param source_path: Path where the update file was extracted, as returned by :py:func:`extract_update`
        :type source_path: str
        """
        arguments = r'"%s" "%s" "%s" "%s"' % (os.getpid(), source_path, paths.app_path(), paths.get_executable())
        if platform.system() == 'Windows':
            import win32api # type: ignore
            win32api.ShellExecute(0, 'open', bootstrap_path, arguments, '', 5)
        else:
            import subprocess
            self.make_executable(bootstrap_path)
            subprocess.Popen(['%s %s' % (bootstrap_path, arguments)], shell=True)
        log.info("Bootstrap executed")

    def bootstrap_name(self) -> str:
        """ Returns the name of the bootstrapper, based in user platform.

        :rtype: str
        """
        if platform.system() == 'Windows':
            return 'bootstrap.exe'
        elif platform.system() == 'Darwin':
            return 'bootstrap-mac.sh'
        return 'bootstrap-lin.sh'

    def make_executable(self, path: str) -> None:
        """ Set execution permissions in a script on Unix platforms. """
        import stat
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IEXEC)
