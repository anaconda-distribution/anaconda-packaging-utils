"""
File:           repodata_api.py
Description:    Library that provides tooling for pulling and parsing `repodata.json` files from `repo.anaconda.com`
"""


import logging
from dataclasses import dataclass
from enum import Enum
from typing import Final, Optional

from anaconda_packaging_utils.api._types import BaseApiException
from anaconda_packaging_utils.api._utils import make_request_and_validate
from anaconda_packaging_utils.types import JsonType, SchemaType

# from jsonschema import validate as schema_validate


# https://repo.anaconda.com/pkgs/mfain/noarch/repodata.json
# channel / <architecture>

# Logging object for this module
log = logging.getLogger(__name__)


class Channel(str, Enum):
    """
    Enumeration of channels supported on `repo.anaconda.com`
    """

    MAIN = "main"
    FREE = "free"
    R = "r"
    PRO = "pro"
    ARCHIVE = "archive"
    MRO_ARCHIVE = "mro-archive"
    MSYS_2 = "msys2"


class Architecture(str, Enum):
    """
    Enumeration of architectures supported on `repo.anaconda.com`
    """

    LINUX_X86_64 = "linux-64"
    LINUX_X86_32 = "linux-32"
    LINUX_GRAVITON_2 = "linux-aarch64"
    LINUX_ARM_V6L = "linux-armv6l"
    LINUX_ARM_V7L = "linux-armv7l"
    LINUX_S390 = "linux-s390x"
    LINUX_PPC64LE = "linux-ppc64le"
    OSX_ARM64 = "osx-arm64"
    OSX_X86_64 = "osx-64"
    OSX_X86_32 = "osx-32"
    WIN_64 = "win-64"
    WIN_32 = "win-32"
    NO_ARCH = "noarch"


_BASE_REPODATA_URL: Final[str] = "https://repo.anaconda.com/pkgs"

# Maps the available architectures per channel hosted on `repo.anaconda.com`
_SUPPORTED_CHANNEL_ARCH: Final[dict[Channel, set[Architecture]]] = {
    Channel.MAIN: {
        Architecture.LINUX_X86_64,
        Architecture.LINUX_X86_32,
        Architecture.LINUX_GRAVITON_2,
        Architecture.LINUX_S390,
        Architecture.LINUX_PPC64LE,
        Architecture.OSX_X86_64,
        Architecture.OSX_ARM64,
        Architecture.WIN_64,
        Architecture.WIN_32,
        Architecture.NO_ARCH,
    },
    Channel.FREE: {
        Architecture.LINUX_X86_64,
        Architecture.LINUX_X86_32,
        Architecture.LINUX_ARM_V6L,
        Architecture.LINUX_ARM_V7L,
        Architecture.LINUX_PPC64LE,
        Architecture.OSX_X86_64,
        Architecture.OSX_X86_32,
        Architecture.WIN_64,
        Architecture.WIN_32,
        Architecture.NO_ARCH,
    },
    Channel.R: {
        Architecture.LINUX_X86_64,
        Architecture.LINUX_X86_32,
        Architecture.LINUX_ARM_V6L,
        Architecture.LINUX_ARM_V7L,
        Architecture.LINUX_PPC64LE,
        Architecture.OSX_X86_64,
        Architecture.OSX_X86_32,
        Architecture.WIN_64,
        Architecture.WIN_32,
        Architecture.NO_ARCH,
    },
    Channel.PRO: {
        Architecture.LINUX_X86_64,
        Architecture.LINUX_X86_32,
        Architecture.LINUX_ARM_V6L,
        Architecture.LINUX_ARM_V7L,
        Architecture.LINUX_PPC64LE,
        Architecture.OSX_X86_64,
        Architecture.OSX_X86_32,
        Architecture.WIN_64,
        Architecture.WIN_32,
        Architecture.NO_ARCH,
    },
    Channel.ARCHIVE: {
        Architecture.LINUX_X86_64,
        Architecture.LINUX_X86_32,
        Architecture.LINUX_ARM_V6L,
        Architecture.LINUX_ARM_V7L,
        Architecture.LINUX_PPC64LE,
        Architecture.OSX_X86_64,
        Architecture.OSX_X86_32,
        Architecture.WIN_64,
        Architecture.WIN_32,
        Architecture.NO_ARCH,
    },
    Channel.MRO_ARCHIVE: {
        Architecture.LINUX_X86_64,
        Architecture.LINUX_X86_32,
        Architecture.LINUX_ARM_V6L,
        Architecture.LINUX_ARM_V7L,
        Architecture.LINUX_PPC64LE,
        Architecture.OSX_X86_64,
        Architecture.OSX_X86_32,
        Architecture.WIN_64,
        Architecture.WIN_32,
        Architecture.NO_ARCH,
    },
    Channel.MSYS_2: {
        Architecture.WIN_64,
        Architecture.WIN_32,
    },
}


class ApiException(BaseApiException):
    """
    Indicates an exception occurred with this API.
    """

    pass


@dataclass
class RepodataMetadata:
    """
    Metadata section in a `repodata.json` blob
    """

    # Required fields
    subdir: str
    # Optional fields
    arch: Optional[str] = None
    platform: Optional[str] = None


@dataclass
class PackageData:
    """
    Per-package data stored in a `repodata.json` blob
    """

    # Required fields
    build: str
    build_number: int
    depends: list[str]
    md5: str
    sha256: str
    name: str
    size: int
    version: str
    # Optional fields
    timestamp: Optional[int] = None
    date: Optional[str] = None
    track_features: Optional[str] = None
    license: Optional[str] = None
    license_family: Optional[str] = None


@dataclass
class Repodata:
    """
    Structure that contains an entire serialized `repodata.json` blob
    """

    info: RepodataMetadata
    packages: dict[str, PackageData]
    removed: list[str]
    repodata_version: int


_REPODATA_JSON_SCHEMA: Final[SchemaType] = {
    "type": "object",
    "required": ["info", "packages", "removed", "repodata_version"],
    "properties": {
        "info": {
            "required": ["subdir"],
            "properties": {
                "subdir": {"type": "string"},
                "arch": {"type": "string"},
                "platform": {"type": "string"},
            },
        },
        "packages": {
            "additionalProperties": {
                "type": "object",
                "required": [
                    "build",
                    "build_number",
                    "depends",
                    "md5",
                    "sha256",
                    "name",
                    "size",
                    "version",
                ],
                "properties": {
                    "build": {"type": "string"},
                    "build_number": {"type": "integer"},
                    "depends": {"type": "array", "items": {"type": "string"}},
                    "md5": {"type": "string"},
                    "sha256": {"type": "string"},
                    "name": {"type": "string"},
                    "size": {"type": "integer"},
                    "timestamp": {"type": "integer"},
                    "version": {"type": "string"},
                    "date": {"type": "string"},
                    "track_features": {"type": "string"},
                    "license": {"type": ["string", "null"]},
                    "license_family": {"type": ["string", "null"]},
                },
            }
        },
        "removed": {"type": "array", "items": {"type": "string"}},
        "repodata_version": {"type": "integer"},
    },
}


def _calc_request_url(channel: Channel, arch: Architecture) -> str:
    """
    Calculates the URL to the target `repodata.json` blob.
    :param channel: Target publishing channel.
    :param arch: Target package architecture. Some older reference material calls this "subdir"
    :raises ApiException: If the target channel and architecture are not supported
    :return: URL to the repodata JSON blob of interest.
    """
    if channel not in _SUPPORTED_CHANNEL_ARCH:
        raise ApiException(f"Requested package channel is not supported: {channel}")
    if arch not in _SUPPORTED_CHANNEL_ARCH[channel]:
        raise ApiException(f"Requested architecture `{arch}` is not supported by this channel: {channel}")
    return f"{_BASE_REPODATA_URL}/{channel}/{arch}/repodata.json"


def fetch_repodata(channel: Channel, arch: Architecture) -> Repodata:
    """
    Fetches and parses a `repodata.json` blob into a data structure
    :param channel: Target publishing channel.
    :param arch: Target package architecture. Some older reference material calls this "subdir"
    :raises ApiException: If the target channel and architecture are not supported or HTTP request failed.
    :return: Serialized form of the `repodata.json` structure.
    """
    request_url: Final[str] = _calc_request_url(channel, arch)
    response_json: JsonType
    try:
        response_json = make_request_and_validate(
            request_url,
            _REPODATA_JSON_SCHEMA,
            log,
        )
    except BaseApiException as e:
        raise ApiException(e.message) from e
    # TODO complete
    # TODO handle NULLable license fields
    return Repodata(RepodataMetadata("linux-64"), {}, [], 0)
