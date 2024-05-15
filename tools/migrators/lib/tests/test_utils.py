import pytest

from lib import utils


def test_find_by_id():
    data = [
        {"id": "1", "name": "Alice", "details": {"age": 30, "location": "USA"}},
        {"id": "2", "name": "Bob", "details": {"age": 40, "location": "UK"}},
        {"id": "3", "name": "Charlie", "details": {"age": 50, "location": "Canada"}},
    ]

    # Test case: id exists in the data
    result = utils.find_by_id(data, "1")
    assert result == {
        "id": "1",
        "name": "Alice",
        "details": {"age": 30, "location": "USA"},
    }

    # Test case: id does not exist in the data
    result = utils.find_by_id(data, "4")
    assert result is None

    # Test case: data is empty
    result = utils.find_by_id([], "1")
    assert result is None

    # Test case: nested key exists
    result = utils.find_by_id(data, "USA", "details.location")
    assert result == {
        "id": "1",
        "name": "Alice",
        "details": {"age": 30, "location": "USA"},
    }

    # Test case: nested key does not exist
    result = utils.find_by_id(data, "Australia", "details.location")
    assert result is None

    # Test case: data is None
    with pytest.raises(TypeError):
        utils.find_by_id(None, "1")
