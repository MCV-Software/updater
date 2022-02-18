import glob
import os.path
import platform
from typing import List, Tuple

def find_datafiles() -> List[Tuple[str, List[str]]]:
    """ Returns path to the updater bootstrap file.

    :returns: A tuple of the form ("", ["bootstrap_file"])
    :rtype: tuple
    """
    system = platform.system()
    if system == 'Windows':
        file_ext = '*.exe'
    else:
        file_ext = '*.sh'
    path = os.path.abspath(os.path.join(__path__[0], 'bootstrappers', file_ext))
    return [('', glob.glob(path))]
