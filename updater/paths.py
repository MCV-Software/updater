""" Provide some system paths for multiple platforms.

This module has been taken and modified from https://github.com/accessibleapps/platform_utils and has been used to provide some convenient methods to retrieve system paths.
"""
import platform
import os
import sys

plat: str = platform.system()
is_windows: bool = plat == "Windows"
is_mac: bool = plat == "Darwin"
is_linux: bool = plat == "Linux"

# ToDo: Return correct values for nuitka build executables, as they do not use sys.frozen.
def is_frozen() -> bool:
    """ Checks wheter the updater package is inside a frozen application.

    :rtype: bool
"""
    return hasattr(sys, "frozen")

def get_executable() -> str:
    """Returns the full executable path/name if frozen, or the full path/name of the main module if not.

    :rtype: str
    """
    if is_frozen():
        if not is_mac:
            return sys.executable
        # On Mac, sys.executable points to python. We want the full path to the exe we ran.
        exedir = os.path.abspath(os.path.dirname(sys.executable))
        items = os.listdir(exedir)
        if "python" in items:
            items.remove("python")
        return os.path.join(exedir, items[0])
    # Not frozen
    try:
        import __main__
        return os.path.abspath(__main__.__file__)
    except AttributeError:
        return sys.argv[0]

def executable_directory() -> str:
    """Always determine the directory of the executable, even when run with py2exe or otherwise frozen.

    :rtype: str
    """
    executable = get_executable()
    path = os.path.abspath(os.path.dirname(executable))
    return path

def app_path() -> str:
    """ Returns application directory.

    :rtype: str
    """
    path = executable_directory()
    if is_frozen() and is_mac:
        path = os.path.abspath(os.path.join(path, "..", ".."))
    return path