import pytest
from updater import utils

@pytest.mark.parametrize("number_of_bytes, expected_result", [
        (11, "11"),
        (20000000, "19.07Mb"),
        (2000000000, "1.86Gb"),
        ])
def test_convert_bytes(number_of_bytes, expected_result):
    result = utils.convert_bytes(number_of_bytes)
    assert result == expected_result