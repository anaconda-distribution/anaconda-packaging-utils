"""
File:           repodata_api.py
Description:    Library that provides tooling for pulling and parsing `repodata.json` files from `repo.anaconda.com`
"""


import logging
from dataclasses import dataclass
from enum import Enum
from typing import Final, Optional, cast, no_type_check

from conda.exceptions import InvalidVersionSpec
from conda.models.version import VersionOrder

from anaconda_packaging_utils.api._types import BaseApiException
from anaconda_packaging_utils.api._utils import init_optional_int, init_optional_str, make_request_and_validate
from anaconda_packaging_utils.types import JsonObjectType, JsonType, SchemaType

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

    ## Required fields ##
    subdir: str
    ## Optional fields ##
    arch: Optional[str] = None
    platform: Optional[str] = None


@dataclass
class PackageData:
    """
    Per-package data stored in a `repodata.json` blob
    """

    ## Required fields ##
    build: str
    build_number: int
    depends: list[str]
    md5: str
    sha256: str
    name: str
    size: int
    version: str
    subdir: str
    ## Optional fields ##
    timestamp: Optional[int] = None
    date: Optional[str] = None
    track_features: Optional[str] = None
    license: Optional[str] = None
    license_family: Optional[str] = None

    # TODO rm: Enforce type checking when this PR is released
    #   https://github.com/conda/conda/pull/13385
    @no_type_check
    def __lt__(self, other: VersionOrder) -> bool:
        """
        Allows for version comparisons between two `PackageData` instances
        NOTE: We are relying on the default implementation of `__eq__()` for dataclasses, which checks that all fields
              are equivalent.
        NOTE: Type checking is disabled for this function as `VersionOrder`
        :param other: Object to compare against this one.
        :returns: If this instance has a lower version than the compared instance.
        """
        if not isinstance(other, PackageData):
            return False
        # Comparing versions between two different software projects/packages is meaningless.
        if self.name != other.name:
            return False
        try:
            self_v = VersionOrder(self.version)
            other_v = VersionOrder(other.version)
            # If two versions are equal, fallback to comparing the build number
            if self_v == other_v:
                return self.build_number < other.build_number
            return self_v < other_v
        except InvalidVersionSpec:
            # If a `VersionOrder` object failed to be created, we are not able to accurately compare these objects.
            pass
        return False


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
                    "subdir",
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
                    "subdir": {"type": "string"},
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
    :returns: URL to the repodata JSON blob of interest.
    """
    if channel not in _SUPPORTED_CHANNEL_ARCH:
        raise ApiException(f"Requested package channel is not supported: {channel}")
    if arch not in _SUPPORTED_CHANNEL_ARCH[channel]:
        raise ApiException(f"Requested architecture `{arch}` is not supported by this channel: {channel}")
    return f"{_BASE_REPODATA_URL}/{channel}/{arch}/repodata.json"


def _serialize_repodata_metadata(obj: JsonObjectType) -> RepodataMetadata:
    """
    Serializes a JSON object to a RepodataMetadata instance. The JSON must have been previously validated.
    :param obj: JSON object to parse
    :returns: Constructed RepodataMetadata instance
    """
    return RepodataMetadata(
        subdir=cast(str, obj["subdir"]),
        arch=init_optional_str("arch", obj),
        platform=init_optional_str("platform", obj),
    )


def _serialize_package_data(obj: JsonObjectType) -> PackageData:
    """
    Serializes a JSON object to a PackageData instance. The JSON must have been previously validated.
    :param obj: JSON object to parse
    :returns: Constructed PackageData instance
    """
    return PackageData(
        ## Required fields ##
        build=cast(str, obj["build"]),
        build_number=cast(int, obj["build_number"]),
        depends=cast(list[str], obj["depends"]),
        md5=cast(str, obj["md5"]),
        sha256=cast(str, obj["sha256"]),
        name=cast(str, obj["name"]),
        size=cast(int, obj["size"]),
        version=cast(str, obj["version"]),
        subdir=cast(str, obj["subdir"]),
        ## Optional fields ##
        timestamp=init_optional_int("timestamp", obj),
        date=init_optional_str("date", obj),
        track_features=init_optional_str("track_features", obj),
        # TODO handle NULLable license fields
        license=init_optional_str("license", obj),
        license_family=init_optional_str("license_family", obj),
    )


def _serialize_repodata(obj: JsonObjectType) -> Repodata:
    """
    Serializes a JSON object to a Repodata instance. The JSON must have been previously validated.
    :param obj: JSON object to parse
    :returns: Constructed Repodata instance
    """
    packages = cast(JsonObjectType, obj["packages"])
    serialized_packages: dict[str, PackageData] = {}
    for name, payload in packages.items():
        serialized_packages[name] = _serialize_package_data(cast(JsonObjectType, payload))

    return Repodata(
        info=_serialize_repodata_metadata(cast(JsonObjectType, obj["info"])),
        packages=serialized_packages,
        removed=cast(list[str], obj["removed"]),
        repodata_version=cast(int, obj["repodata_version"]),
    )


def fetch_repodata(channel: Channel, arch: Architecture) -> Repodata:
    """
    Fetches and parses a `repodata.json` blob into a data structure
    :param channel: Target publishing channel.
    :param arch: Target package architecture. Some older reference material calls this "subdir"
    :raises ApiException: If the target channel and architecture are not supported or HTTP request failed.
    :returns: Serialized form of the `repodata.json` structure.
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

    return _serialize_repodata(cast(JsonObjectType, response_json))
