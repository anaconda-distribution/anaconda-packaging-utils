"""
File:           test_api_utils.py
Description:    Tests API `_utils` module
                Note: The `PyPi` API is used as the example API for these generic utility tests.
"""

from typing import Final, no_type_check
from unittest.mock import patch

import pytest

from anaconda_packaging_utils.api import _utils
from anaconda_packaging_utils.api._types import BaseApiException
from anaconda_packaging_utils.api.pypi_api import PackageInfo
from anaconda_packaging_utils.tests.testing_utils import MOCK_BASE_URL, TEST_FILES_PATH, load_json_file
from anaconda_packaging_utils.types import JsonObjectType

TEST_PYPI_FILES: Final[str] = f"{TEST_FILES_PATH}/pypi_api"


@no_type_check
def test_make_request_and_validate_get_package() -> None:
    """
    Tests the fetching and validation of a GET package request
    """
    response_json = load_json_file(f"{TEST_PYPI_FILES}/valid_get_package.json")
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.headers = {"content-type": "application/json"}
        mock_get.return_value.json.return_value = response_json
        assert (
            _utils.make_request_and_validate(  # pylint: disable=protected-access
                f"{MOCK_BASE_URL}/scipy/json",
                PackageInfo.get_schema(True),
            )
            == response_json
        )


@no_type_check
def test_make_request_and_validate_get_package_version() -> None:
    """
    Tests the fetching and validation of a GET package request @ a version
    """
    response_json = load_json_file(f"{TEST_PYPI_FILES}/valid_get_package_version.json")
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.headers = {"content-type": "application/json"}
        mock_get.return_value.json.return_value = response_json
        assert (
            _utils.make_request_and_validate(  # pylint: disable=protected-access
                f"{MOCK_BASE_URL}/scipy/1.11.1/json",
                PackageInfo.get_schema(False),
            )
            == response_json
        )


@no_type_check
def test_make_request_and_validate_bad_http_response() -> None:
    """
    Tests scenarios where the HTTP response is malformed
    """
    with patch("requests.get") as mock_get:
        # GET returns a non-200 error code
        mock_get.return_value.status_code = 400
        mock_get.return_value.headers = {"content-type": "application/json"}
        mock_get.return_value.json.return_value = load_json_file(f"{TEST_PYPI_FILES}/valid_get_package_version.json")
        with pytest.raises(BaseApiException):
            _utils.make_request_and_validate(  # pylint: disable=protected-access
                f"{MOCK_BASE_URL}/scipy/1.11.1/json",
                PackageInfo.get_schema(False),
            )

        # GET response is None
        mock_get.return_value = None
        with pytest.raises(BaseApiException):
            _utils.make_request_and_validate(  # pylint: disable=protected-access
                f"{MOCK_BASE_URL}/scipy/1.11.1/json",
                PackageInfo.get_schema(False),
            )


@no_type_check
def test_make_request_and_validate_bad_http_content() -> None:
    """
    Tests scenarios where the HTTP content is malformed
    """
    with patch("requests.get") as mock_get:
        # No content header
        mock_get.return_value.status_code = 200
        mock_get.return_value.headers = {}
        mock_get.return_value.json.return_value = load_json_file(f"{TEST_PYPI_FILES}/valid_get_package_version.json")
        with pytest.raises(BaseApiException):
            _utils.make_request_and_validate(  # pylint: disable=protected-access
                f"{MOCK_BASE_URL}/scipy/1.11.1/json",
                PackageInfo.get_schema(False),
            )

        # Non-JSON content
        mock_get.return_value.headers = {"content-type": "text/html"}
        with pytest.raises(BaseApiException):
            _utils.make_request_and_validate(  # pylint: disable=protected-access
                f"{MOCK_BASE_URL}/scipy/1.11.1/json",
                PackageInfo.get_schema(False),
            )

        # JSON is malformed
        mock_get.return_value.headers = {"content-type": "application/json"}
        mock_get.return_value.json.return_value = "bad: json"
        with pytest.raises(BaseApiException):
            _utils.make_request_and_validate(  # pylint: disable=protected-access
                f"{MOCK_BASE_URL}/scipy/1.11.1/json",
                PackageInfo.get_schema(False),
            )


@no_type_check
def test_make_request_and_validate_bad_schema() -> None:
    """
    Tests if the JSON schema validator handles as expected
    """
    response_json = load_json_file(f"{TEST_PYPI_FILES}/valid_get_package_version.json")
    # Redact a required field to corrupt the schema
    del response_json["info"]["license"]
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.headers = {"content-type": "application/json"}
        mock_get.return_value.json.return_value = response_json
        with pytest.raises(BaseApiException):
            _utils.make_request_and_validate(
                f"{MOCK_BASE_URL}/scipy/json",
                PackageInfo.get_schema(True),
            )


def test_check_for_empty_field() -> None:
    """
    Tests checking for empty JSON fields
    """
    _utils.check_for_empty_field("Test", "foobar")
    with pytest.raises(BaseApiException):
        _utils.check_for_empty_field("Test", "")
        _utils.check_for_empty_field("Test", None)


def test_init_optional_str() -> None:
    """
    Tests optional casting wrapper
    """
    obj: Final[JsonObjectType] = {"foo": "bar"}
    assert _utils.init_optional_str("foo", obj) == "bar"
    assert _utils.init_optional_str("baz", obj) is None


def test_init_optional_int() -> None:
    obj: Final[JsonObjectType] = {"foo": 42}
    assert _utils.init_optional_int("foo", obj) == 42
    assert _utils.init_optional_int("baz", obj) is None
