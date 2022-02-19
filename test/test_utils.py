import pytest
from updater import utils

@pytest.mark.parametrize("number_of_bytes, expected_result", [
        (11, "11"),
        (200000, "195.31Kb"),
        (2000000, "1.91Mb"),
        (20000000, "19.07Mb"),
        (2000000000, "1.86Gb"),
        (2000000000000, "1.82Tb"),
        (2000000000000000, "1.78Pb"),
        ])
def test_convert_bytes(number_of_bytes, expected_result):
    result = utils.convert_bytes(number_of_bytes)
    assert result == expected_result