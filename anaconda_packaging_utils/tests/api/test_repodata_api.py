"""
File:           test_repodata_api.py
Description:    Tests the repodata API
"""
from typing import Final, no_type_check
from unittest.mock import patch

import pytest

from anaconda_packaging_utils.api import repodata_api
from anaconda_packaging_utils.api._utils import make_request_and_validate
from anaconda_packaging_utils.tests.testing_utils import MOCK_BASE_URL, TEST_FILES_PATH, load_json_file

TEST_REPODATA_FILES: Final[str] = f"{TEST_FILES_PATH}/repodata_api"


@no_type_check
@pytest.mark.parametrize(
    "file",
    [
        "repodata_main_linux64_small.json",
        "repodata_main_linux64.json",
        "repodata_main_osx64.json",
        "repodata_r_ppc64le.json",
    ],
)
def test_validate_repodata_schema(file: str):
    """
    Validates the jsonschema representation of a `repodata.json` against several examples.
    """
    response_json = load_json_file(f"{TEST_REPODATA_FILES}/{file}")
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.headers = {"content-type": "application/json"}
        mock_get.return_value.json.return_value = response_json
        assert make_request_and_validate(
            MOCK_BASE_URL, repodata_api._REPODATA_JSON_SCHEMA  # pylint: disable=protected-access
        )
