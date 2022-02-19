import os
import pytest
import updater
from unittest import mock

@pytest.mark.parametrize("system", [("Windows"), ("Linux"), ("Darwin")])
def test_find_datafiles(system):
    with mock.patch("platform.system", return_value=system):
        result = updater.find_datafiles()
    if system == "Windows":
        assert "bootstrap.exe" in result[0][1][0]
        assert os.path.exists(result[0][1][0])
    else:
        assert len(result[0][1]) == 2
        assert os.path.exists(result[0][1][0])
        assert os.path.exists(result[0][1][1])