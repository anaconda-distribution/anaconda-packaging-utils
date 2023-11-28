"""
File:           repodata_api.py
Description:    Library that provides tooling for pulling and parsing `repodata.json` files from `repo.anaconda.com`
"""


from dataclasses import dataclass
from enum import Enum
from typing import Final, Optional, no_type_check

from jsonschema import validate as schema_validate

from anaconda_packaging_utils.api.types import BaseApiException
from anaconda_packaging_utils.types import SchemaType

# https://repo.anaconda.com/pkgs/mfain/noarch/repodata.json
# channel / <architecture>


class Channel(str, Enum):
    MAIN = "main"
    FREE = "free"
    R = "r"
    PRO = "pro"
    ARCHIVE = "archive"
    MRO_ARCHIVE = "mro-archive"
    MSYS_2 = "msys2"


class Architecture(str, Enum):
    LINUX_x86_64 = "linux-64"
    LINUX_x86_32 = "linux-32"
    LINUX_GRAVITON_2 = "linux-aarch64"
    LINUX_ARM_v6l = "linux-armv6l"
    LINUX_ARM_v7l = "linux-armv7l"
    LINUX_S390 = "linux-s390x"
    LINUX_PPC64LE = "linux-ppc64le"
    OSX_ARM64 = "osx-arm64"
    OSX_x86_64 = "osx-64"
    OSX_x86_32 = "osx-32"
    WIN_64 = "win-64"
    WIN_32 = "win-32"
    NO_ARCH = "noarch"


_BASE_REPODATA_URL: Final[str] = "https://repo.anaconda.com/pkgs/"

# Maps the available architectures per channel hosted on `repo.anaconda.com`
_SUPPORTED_CHANNEL_ARCH = Final[dict[Channel, set[Architecture]]] = {
    Channel.MAIN: {
        Architecture.LINUX_x86_64,
        Architecture.LINUX_x86_32,
        Architecture.LINUX_GRAVITON_2,
        Architecture.LINUX_S390,
        Architecture.LINUX_PPC64LE,
        Architecture.OSX_x86_64,
        Architecture.OSX_ARM64,
        Architecture.WIN_64,
        Architecture.WIN_32,
        Architecture.NO_ARCH,
    },
    Channel.FREE: {
        Architecture.LINUX_x86_64,
        Architecture.LINUX_x86_32,
        Architecture.LINUX_ARM_v6l,
        Architecture.LINUX_ARM_v7l,
        Architecture.LINUX_PPC64LE,
        Architecture.OSX_x86_64,
        Architecture.OSX_x86_32,
        Architecture.WIN_64,
        Architecture.WIN_32,
        Architecture.NO_ARCH,
    },
    Channel.R: {
        Architecture.LINUX_x86_64,
        Architecture.LINUX_x86_32,
        Architecture.LINUX_ARM_v6l,
        Architecture.LINUX_ARM_v7l,
        Architecture.LINUX_PPC64LE,
        Architecture.OSX_x86_64,
        Architecture.OSX_x86_32,
        Architecture.WIN_64,
        Architecture.WIN_32,
        Architecture.NO_ARCH,
    },
    Channel.PRO: {
        Architecture.LINUX_x86_64,
        Architecture.LINUX_x86_32,
        Architecture.LINUX_ARM_v6l,
        Architecture.LINUX_ARM_v7l,
        Architecture.LINUX_PPC64LE,
        Architecture.OSX_x86_64,
        Architecture.OSX_x86_32,
        Architecture.WIN_64,
        Architecture.WIN_32,
        Architecture.NO_ARCH,
    },
    Channel.ARCHIVE: {
        Architecture.LINUX_x86_64,
        Architecture.LINUX_x86_32,
        Architecture.LINUX_ARM_v6l,
        Architecture.LINUX_ARM_v7l,
        Architecture.LINUX_PPC64LE,
        Architecture.OSX_x86_64,
        Architecture.OSX_x86_32,
        Architecture.WIN_64,
        Architecture.WIN_32,
        Architecture.NO_ARCH,
    },
    Channel.MRO_ARCHIVE: {
        Architecture.LINUX_x86_64,
        Architecture.LINUX_x86_32,
        Architecture.LINUX_ARM_v6l,
        Architecture.LINUX_ARM_v7l,
        Architecture.LINUX_PPC64LE,
        Architecture.OSX_x86_64,
        Architecture.OSX_x86_32,
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

    def __init__(self, message: str):
        """
        Constructs an API exception
        :param message: String description of the issue encountered.
        """
        super().__init__(message)


@dataclass
class RepodataMetadata:
    # Required fields
    subdir: str
    # Optional fields
    arch: Optional[str]
    platform: Optional[str]


@dataclass
class PackageData:
    # Required fields
    build: str
    build_number: int
    depends: list[str]
    md5: str
    sha256: str
    name: str
    size: int
    timestamp: int
    version: str
    # Optional fields
    date: Optional[str]
    track_features: Optional[str]
    license: Optional[str]
    license_family: Optional[str]


@dataclass
class Repodata:
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
            # TODO
        },
        "removed": {"type": "array", "items": {"type": "string"}},
        "repodata_version": {"type": "integer"},
    },
}
