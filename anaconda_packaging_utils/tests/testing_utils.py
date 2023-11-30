"""
File:           testing_utils.py
Description:    Contains constants and other utilities used throughout the unit tests in this project.
"""
import json
from pathlib import Path
from typing import Final

from anaconda_packaging_utils.types import JsonType

# Path to supplementary files used in test cases
TEST_FILES_PATH = "anaconda_packaging_utils/tests/test_aux_files"

# Fake URL to use when a real URL is mocked.
MOCK_BASE_URL: Final[str] = "https://mock.website.com"


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
