"""
File:           test_config_data.py
Description:    Tests configuration data library
"""
from typing import Final, no_type_check
from unittest.mock import mock_open, patch

import jsonschema
import pytest

from anaconda_packaging_utils.storage.config_data import ConfigData
from anaconda_packaging_utils.tests.testing_utils import TEST_FILES_PATH

TEST_CONFIG_FILES: Final[str] = f"{TEST_FILES_PATH}/config_files"
VALID_SCHEMA_TO_STR: Final[
    str
] = """{
  "token.github": "aec070645fe53ee3b3763059376134f058cc",
  "local_path.aggregate": "/home/fakeuser/work/aggregate"
}"""


def test_valid_schema() -> None:
    """
    Construct an instance with an valid schema
    """
    ConfigData(f"{TEST_CONFIG_FILES}/valid_schema.yaml")


def test_template_has_valid_schema() -> None:
    """
    Ensure that the provided template file matches our current schema
    """
    ConfigData("anaconda-packaging-utils-config-template.yaml")


def test_invalid_schema() -> None:
    """
    Construct an instance with an invalid schema
    """
    # Known `mypy` issue: https://github.com/pytest-dev/pytest/issues/8984
    with pytest.raises(jsonschema.ValidationError):  # type: ignore[misc]
        ConfigData(f"{TEST_CONFIG_FILES}/invalid_schema.yaml")


def test_file_not_found() -> None:
    """
    Construct an instance with an unknown file
    """
    with pytest.raises(FileNotFoundError):
        ConfigData("/bad/path")


def test_to_str() -> None:
    """
    Ensure sting casting pretty-prints table information
    """
    data = ConfigData(f"{TEST_CONFIG_FILES}/valid_schema.yaml")
    output = str(data)
    assert output == VALID_SCHEMA_TO_STR


def test_contains_found() -> None:
    """
    Ensure data can be checked before access
    """
    data = ConfigData(f"{TEST_CONFIG_FILES}/valid_schema.yaml")
    assert "token.github" in data
    assert "local_path.aggregate" in data


def test_contains_not_found() -> None:
    """
    Ensure containment doesn't return false positives
    """
    data = ConfigData(f"{TEST_CONFIG_FILES}/valid_schema.yaml")
    assert "foo.bar" not in data


def test_access_found() -> None:
    """
    Access of a valid key should return the expected value
    """
    data = ConfigData(f"{TEST_CONFIG_FILES}/valid_schema.yaml")
    assert data["token.github"] == "aec070645fe53ee3b3763059376134f058cc"
    assert data["local_path.aggregate"] == "/home/fakeuser/work/aggregate"


def test_access_not_found() -> None:
    """
    Access of an invalid key should raise an exception
    """
    data = ConfigData(f"{TEST_CONFIG_FILES}/valid_schema.yaml")
    with pytest.raises(KeyError):
        test = data["invalid.key"]
        assert test is None


def test_no_mutations() -> None:
    """
    Ensure that the data underlying data structure cannot be mutated
    """
    data = ConfigData(f"{TEST_CONFIG_FILES}/valid_schema.yaml")
    # Note that `mypy` should prevent assignment, but we'll suppress it so we can test that assignment is disallowed.
    with pytest.raises(TypeError):
        data["github.token"] = "foo.bar"  # type: ignore[index] # pylint: disable=E1137


@no_type_check
def test_caching() -> None:
    """
    Ensure that the cache is not changed if two instances reference the same config file. Some unit tests would fail if
    the cache was not cleared between unit tests.

    `@typing.no_type_check()` suppresses `Any` errors while using mockers.
    """
    file_path = f"{TEST_CONFIG_FILES}/fake_schema.yaml"
    file_data = """
    token:
      github: aec070645fe53ee3b3763059376134f058cc
    local_path:
      aggregate: /home/fakeuser/work/aggregate
    """
    with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
        data0 = ConfigData(file_path)
        assert mock_file.call_count == 1
        data1 = ConfigData(file_path)
        assert mock_file.call_count == 1
        # The addresses of these tables should be the same, as these tables are the same static cache.
        assert id(data0._config_tbl) == id(data1._config_tbl)  # pylint: disable=protected-access
