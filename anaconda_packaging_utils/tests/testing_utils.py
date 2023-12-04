"""
File:           testing_utils.py
Description:    Contains constants and other utilities used throughout the unit tests in this project.
"""
import json
from pathlib import Path
from typing import Final

from anaconda_packaging_utils.types import JsonType, SentinelType

# Path to supplementary files used in test cases
TEST_FILES_PATH = "anaconda_packaging_utils/tests/test_aux_files"

# Fake URL to use when a real URL is mocked.
MOCK_BASE_URL: Final[str] = "https://mock.website.com"


class MockHttpJsonResponse:
    """
    Class that mocks an HTTP response with a JSON payload.
    """

    _sentinel = SentinelType()

    def __init__(self, status_code: int, json_file: Path | str = "", json_data: JsonType | SentinelType = _sentinel):
        """
        Constructs a mocked HTTP response that returns JSON
        :param status_code: HTTP status code to return
        :param json_file: (Optional) Path to file to load JSON data from.
        :param json_data: (Optional) If `json_file` is unspecified, this value can set the JSON payload directly.
        """
        self.headers = {"content-type": "application/json"}
        self.status_code = status_code

        if json_file != "":
            self.json_data = load_json_file(json_file)
        else:
            self.json_data = {} if isinstance(json_data, SentinelType) else json_data

    def json(self) -> JsonType:
        """
        Mocked function call that returns JSON data
        :return: Parsed JSON data
        """
        return self.json_data


def load_json_file(file: Path | str) -> JsonType:
    """
    Loads JSON from a test file.

    This could be turned into a fixture, but `mypy` doesn't play nice with those decorators.

    :param file:    JSON filename of the file to read
    :returns: Parsed JSON read from the file
    """
    with open(Path(file), "r", encoding="utf-8") as f:
        j: JsonType = json.load(f)
        return j
