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
def test_validate_repodata_schema(file: str) -> None:
    """
    Validates the jsonschema representation of a `repodata.json` against several examples.
    This is intended to validate the schema format, not necessarily to test `make_request_and_validate()`
    """
    response_json = load_json_file(f"{TEST_REPODATA_FILES}/{file}")
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.headers = {"content-type": "application/json"}
        mock_get.return_value.json.return_value = response_json
        assert make_request_and_validate(
            MOCK_BASE_URL, repodata_api._REPODATA_JSON_SCHEMA  # pylint: disable=protected-access
        )


@no_type_check
def test_fetch_repodata_success() -> None:
    """
    Tests the serialization of an entire `repodata.json` blob. We use a small fake `repodata.json` file for ease of
    validating against.
    """
    response_json = load_json_file(f"{TEST_REPODATA_FILES}/repodata_main_linux64_smaller.json")
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.headers = {"content-type": "application/json"}
        mock_get.return_value.json.return_value = response_json
        assert repodata_api.fetch_repodata(
            repodata_api.Channel.MAIN, repodata_api.Architecture.LINUX_X86_64
        ) == repodata_api.Repodata(
            info=repodata_api.RepodataMetadata(subdir="linux-64"),
            packages={
                "_anaconda_depends-2018.12-py27_0.tar.bz2": repodata_api.PackageData(
                    build="py27_0",
                    build_number=0,
                    depends=[
                        "alabaster",
                        "et_xmlfile",
                        "expat",
                        "fastcache",
                        "filelock",
                        "flask",
                        "flask-cors",
                        "fontconfig",
                    ],
                    md5="199037865cc19536a1ae07b115e5a5c2",
                    sha256="cbaa2e02de8389a04f42ef98d92e11fb319a66dcd86834bdb434dd008525c593",
                    name="_anaconda_depends",
                    size=5598,
                    version="2018.12",
                    subdir="linux-64",
                    timestamp=1562173890182,
                    license="BSD",
                ),
                "distributed-2021.3.0-py36h06a4308_0.conda": repodata_api.PackageData(
                    build="py36h06a4308_0",
                    build_number=0,
                    depends=[
                        "click >=6.6",
                        "cloudpickle >=1.5.0",
                        "contextvars",
                        "cytoolz >=0.8.2",
                        "dask-core >=2020.12.0",
                        "msgpack-python >=0.6.0",
                        "psutil >=5.0",
                        "python >=3.6,<3.7.0a0",
                        "pyyaml",
                        "setuptools",
                        "sortedcontainers !=2.0.0,!=2.0.1",
                        "tblib >=1.6.0",
                        "toolz >=0.8.2",
                        "tornado >=5",
                        "zict >=0.1.3",
                    ],
                    md5="7f27ad8dfe92feddec4c9533a34f02ee",
                    sha256="65f2e21671c1810a3f7ab99b19306ae079dfc43102f46aac203872452bd1c27a",
                    name="distributed",
                    size=1073180,
                    version="2021.3.0",
                    subdir="linux-64",
                    timestamp=1615054637026,
                    license="BSD-3-Clause",
                    license_family="BSD",
                ),
                "zstd-1.4.5-h9ceee32_0.conda": repodata_api.PackageData(
                    build="h9ceee32_0",
                    build_number=0,
                    depends=[
                        "libgcc-ng >=7.3.0",
                        "libstdcxx-ng >=7.3.0",
                        "lz4-c >=1.9.2,<1.10.0a0",
                        "xz >=5.2.5,<6.0a0",
                        "zlib >=1.2.11,<1.3.0a0",
                    ],
                    md5="d05e94324d0cdd0f8f7c099a1c46199b",
                    sha256="bf2b02af3bb83cb46a22fccffb66798e58f4b132cf6337ca876e94aa2918ad46",
                    name="zstd",
                    size=634191,
                    version="1.4.5",
                    subdir="linux-64",
                    timestamp=1595964883124,
                    date="2023-11-30T17:28:55",
                    track_features="foobar",
                    license="BSD 3-Clause",
                ),
            },
            removed=[
                "anaconda-client-1.9.0-py310h06a4308_0.conda",
                "numpy-devel-1.14.3-py36ha22f7c6_2.conda",
                "numpy-devel-1.14.3-py36ha22f7c6_2.tar.bz2",
            ],
            repodata_version=1,
        )


@no_type_check
def test_fetch_repodata_failure() -> None:
    """
    Tests failure scenarios of fetching a repo
    """
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.headers = {"content-type": "application/json"}
        mock_get.return_value.json.return_value = {}
        # Test bad JSON failure
        with pytest.raises(repodata_api.ApiException):
            repodata_api.fetch_repodata(repodata_api.Channel.MAIN, repodata_api.Architecture.LINUX_X86_64)
        # Test bad channel request
        with pytest.raises(repodata_api.ApiException):
            repodata_api.fetch_repodata("fake channel", repodata_api.Architecture.OSX_ARM64)
        # Test bad architecture on channel request
        with pytest.raises(repodata_api.ApiException):
            repodata_api.fetch_repodata(repodata_api.Channel.MSYS_2, repodata_api.Architecture.OSX_ARM64)
