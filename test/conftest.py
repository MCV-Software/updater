import pytest
import json

update_data= dict(current_version="1.1", description="Snapshot version.", downloads=dict(Windows32="https://google.com_32", Windows64="https://google.com_64"))
@pytest.fixture
def file_data():
    global update_data
    yield json.dumps(update_data)

@pytest.fixture
def json_data():
    global update_data
    yield update_data