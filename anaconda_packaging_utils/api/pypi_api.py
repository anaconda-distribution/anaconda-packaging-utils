"""
File:           pypi_api.py
Description:    Library that provides tooling for pulling information from the publicly available PyPi API.

                API Docs: https://warehouse.pypa.io/api-reference/json.html#
"""


import dataclasses
import datetime
import logging
import traceback
from typing import Final, no_type_check

import requests
from jsonschema import validate as schema_validate

import anaconda_packaging_utils.cryptography.utils as crypto_utils
from anaconda_packaging_utils.types import JsonType, SchemaType

# Logging object for this module
log = logging.getLogger(__name__)

# Base URL that all endpoints use
BASE_URL: Final[str] = "https://pypi.python.org/pypi"
# Timeout of HTTP requests, in seconds
HTTP_REQ_TIMEOUT: Final[int] = 60


@dataclasses.dataclass(frozen=True)
class VersionMetadata:
    """
    Represents information stored in the object found in the "urls" or "releases/<version>" keys. This block contains
    version info.

    This object contains a subset of all the provided fields. We only focus on what we need.

    Notes:
        - The `digest` object is flattened into a variable named per hashing algorithm.
    """

    md5: str
    sha256: str
    filename: str
    python_version: str
    size: int
    upload_time: datetime.datetime
    url: str

    @staticmethod
    @no_type_check
    def get_schema() -> SchemaType:
        """
        Returns a JSON schema used to validate JSON responses.
        :returns: JSON schema for a packaging info
        """
        return {
            "type": "object",
            "required": [
                "digests",
                "filename",
                "python_version",
                "size",
                "upload_time_iso_8601",
                "url",
            ],
            "properties": {
                "digests": {
                    "type": "object",
                    "required": ["md5", "sha256"],
                    "properties": {
                        "md5": {"type": "string"},
                        "sha256": {"type": "string"},
                    },
                },
                "filename": {"type": "string"},
                "python_version": {"type": "string"},
                "size": {"type": "integer"},
                "upload_time_iso_8601": {"type": "string"},
                "url": {"type": "string"},
            },
        }


@dataclasses.dataclass(frozen=True)
class PackageInfo:
    """
    Represents information stored in the "info"-keyed object found in both GET request types.

    Notes:
      - This object contains a subset of all provided fields. We only focus on what we need
      - `null` set to a string parameter -> empty string, ""
      - We remove/flatten the `info` key as the `PackageMetadata` class will normalizes output between the two endpoints
      - We only store the `VersionMetadata` for variants labeled `source` as we don't care about PyPi's wheel packaging
    """

    description: str
    description_content_type: str
    docs_url: str
    license: str
    name: str
    package_url: str
    project_url: str
    homepage_url: str
    source_url: str
    release_url: str
    requires_python: str
    summary: str
    version: str
    source_metadata: VersionMetadata

    @staticmethod
    @no_type_check
    def get_schema(requires_releases: bool) -> SchemaType:
        """
        Returns a JSON schema used to validate JSON responses.
        :param requires_releases: Depending on the endpoint used, the API will optionally return information about every
            release/package version. Setting this to "True" will require the `releases` property
        :returns: JSON schema for a packaging info
        """
        base: SchemaType = {
            "type": "object",
            "required": ["info", "urls"],
            "properties": {
                "info": {
                    "type": "object",
                    "required": [
                        "description",
                        "description_content_type",
                        "docs_url",
                        "license",
                        "name",
                        "package_url",
                        "project_url",
                        "project_urls",
                        "release_url",
                        "requires_python",
                        "summary",
                        "version",
                    ],
                    "properties": {
                        "description": {"type": ["string", "null"]},
                        "description_content_type": {"type": ["string", "null"]},
                        "docs_url": {"type": ["string", "null"]},
                        "license": {"type": "string"},
                        "name": {"type": "string"},
                        "package_url": {"type": "string"},
                        "project_url": {"type": "string"},
                        "project_urls": {
                            "type": "object",
                            "properties": {
                                "Homepage": {"type": "string"},
                                "Source": {"type": "string"},
                            },
                        },
                        "release_url": {"type": "string"},
                        "requires_python": {"type": "string"},
                        "summary": {"type": ["string", "null"]},
                        "version": {"type": "string"},
                    },
                },
                "releases": {
                    "type": "object",
                    # Versioning strings are likely too broad to attempt to validate. In order to prevent a validation
                    # error on some bizarre versioning pattern, we accept everything.
                    "patternProperties": {
                        "^.*$": {
                            "type": "array",
                            "items": {
                                **VersionMetadata.get_schema(),
                            },
                        },
                    },
                    "additionalProperties": False,
                },
                "urls": {
                    "type": "array",
                    "items": {
                        **VersionMetadata.get_schema(),
                    },
                },
            },
        }
        if requires_releases:
            base["required"].append("releases")
        return base


@dataclasses.dataclass
class PackageMetadata:
    """
    Class that represents all the metadata about a Package
    """

    info: PackageInfo
    releases: dict[str, VersionMetadata]  # version -> metadata


class ApiException(Exception):
    """
    Generic exception indicating an unrecoverable failure of this API.

    This exception is meant to condense many possible failures into one generic error. The thinking is, if the calling
    code runs into any API failure, there isn't much that can be done. So it is easier for the caller to handle one
    exception than many exception types.
    """

    def __init__(self, message: str):
        """
        Constructs an API exception
        :param message: String description of the issue encountered.
        """
        super().__init__(message if len(message) else "An unknown API issue was encountered.")


def _calc_package_metadata_url(package: str) -> str:
    """
    Generates the URL for fetching package metadata
    :param package: Name of the package
    :returns: REST endpoint to use to fetch package metadata
    """
    return f"{BASE_URL}/{package}/json"


def _calc_package_version_metadata_url(package: str, version: str) -> str:
    """
    Generates the URL for fetching package metadata, at a specific version
    :param package: Name of the package
    :param version: Version of the package
    :returns: REST endpoint to use to fetch package metadata
    """
    return f"{BASE_URL}/{package}/{version}/json"


def _make_request_and_validate(endpoint: str, schema: SchemaType) -> JsonType:
    """
    Makes an HTTP request against the API and validates the result.
    :param endpoint: REST endpoint (URL) used in this request
    :param schema: JSON schema to validate the results against
    :raises ApiException: If there is an unrecoverable issue with the API
    """
    response = None
    try:
        log.debug("Performing GET request on: %s", endpoint)
        response = requests.get(endpoint, timeout=HTTP_REQ_TIMEOUT)
    except Exception as e:
        raise ApiException("GET request failed.") from e

    # This should not be possible, but we'll guard against it anyways.
    if response is None:
        raise ApiException("HTTP response was never set.")

    # Validate HTTP response
    if response.status_code != 200:
        raise ApiException(f"API returned a {response.status_code} HTTP status code")
    if "content-type" not in response.headers:
        raise ApiException("API returned with no `content-type` header.")
    content_type = response.headers["content-type"]
    if content_type != "application/json":
        raise ApiException(f"API returned a non-JSON `content-type`: {content_type}")

    # Validate JSON
    response_json: JsonType = {}
    try:
        response_json = response.json()
    except Exception as e:
        raise ApiException("Failed to parse JSON response.") from e
    try:
        schema_validate(response_json, schema)
    except Exception as e:
        log.debug("Validation exception trace: %s", traceback.format_exc())
        raise ApiException("Returned JSON does not match minimum schema.") from e

    # TODO ensure that the package name matches the package name seen in the JSON response

    return response_json


def _check_for_empty_field(field: str, value: str | None) -> None:
    """
    Convenience function that checks if a critical field is empty/null
    :param field: Field name (for debugging purposes)
    :param value: Value of the field to check
    :raises ApiException: If the field is empty
    """
    if value is None or len(value) == 0:
        raise ApiException(f"`{field}` field is empty: {value}")


def _parse_version_metadata(data: JsonType) -> VersionMetadata:
    """
    Given a schema-validated JSON, parse version metadata
    :param data: JSON data to parse. Pre-req: This must have been previously validated against the schema provided by
        the class.
    :raises ApiException: If there is an unrecoverable issue with the API
    :returns: Version metadata, as an immutable dataclass object
    """
    # Validate non-string fields
    time_str: Final[str] = data["upload_time_iso_8601"]  # type: ignore
    upload_time: datetime.datetime
    try:
        upload_time = datetime.datetime.fromisoformat(time_str)
    except Exception as e:
        raise ApiException(f"Failed to convert timestamp: {time_str}") from e

    size_str = int(data["size"])  # type: ignore
    size: int
    try:
        size = int(size_str)
    except Exception as e:
        raise ApiException(f"Failed to convert size: {size_str}") from e

    parsed: Final[VersionMetadata] = VersionMetadata(
        md5=str(data["digests"]["md5"]),  # type: ignore
        sha256=str(data["digests"]["sha256"]),  # type: ignore
        filename=str(data["filename"]),  # type: ignore
        python_version=str(data["python_version"]),  # type: ignore
        size=size,
        upload_time=upload_time,
        url=str(data["url"] or ""),  # type: ignore
    )

    # Validate the remaining critical fields
    if not crypto_utils.is_valid_md5(parsed.md5):
        raise ApiException(f"VersionMetadata MD5 hash is invalid: {parsed.md5}")
    if not crypto_utils.is_valid_sha256(parsed.sha256):
        raise ApiException(f"VersionMetadata SHA-256 hash is invalid: {parsed.md5}")
    _check_for_empty_field("VersionMetadata.filename", parsed.filename)
    _check_for_empty_field("VersionMetadata.python_version", parsed.python_version)

    return parsed


def _parse_package_info(data: JsonType) -> PackageInfo:
    """
    Given a schema-validated JSON, parse version metadata
    :param data: JSON data to parse. Pre-req: This must have been previously validated against the schema provided by
        the class.
    :raises ApiException: If there is an unrecoverable issue with the API
    :returns: Package info, as an immutable dataclass object
    """
    # Extract the VersionMetadata for "source" objects
    version_metadata: VersionMetadata | None = None
    urls: list[JsonType] = data["urls"]  # type:ignore
    url: JsonType
    for url in urls:
        if url["python_version"] == "source":  # type: ignore
            version_metadata = _parse_version_metadata(url)
            break
    # Although the schema checks have passed, we still need to verify that a `source` code artifact is available.
    if version_metadata is None:
        raise ApiException("Source artifacts are not provided!")

    # These fields may not always be provided and are not guaranteed
    project_urls = data["info"]["project_urls"]  # type: ignore
    homepage_url = ""
    if "Homepage" in project_urls:  # type: ignore
        homepage_url = str(project_urls["Homepage"])  # type: ignore

    source_url = ""
    if "Source" in project_urls:  # type: ignore
        source_url = str(project_urls["Source"])  # type: ignore

    parsed = PackageInfo(
        description=str(data["info"]["description"] or ""),  # type: ignore
        description_content_type=str(
            data["info"]["description_content_type"] or ""  # type:ignore
        ),
        docs_url=str(data["info"]["docs_url"] or ""),  # type: ignore
        license=str(data["info"]["license"]),  # type: ignore
        name=str(data["info"]["name"]),  # type: ignore
        package_url=str(data["info"]["package_url"]),  # type: ignore
        project_url=str(data["info"]["project_url"]),  # type: ignore
        homepage_url=homepage_url,
        source_url=source_url,
        release_url=str(data["info"]["release_url"]),  # type: ignore
        # This field may be empty
        requires_python=str(data["info"]["requires_python"]),  # type: ignore
        summary=str(data["info"]["summary"] or ""),  # type: ignore
        version=str(data["info"]["version"]),  # type: ignore
        source_metadata=version_metadata,
    )

    # Validate the remaining critical values
    _check_for_empty_field("PackageInfo.license", parsed.license)
    _check_for_empty_field("PackageInfo.name", parsed.name)
    _check_for_empty_field("PackageInfo.package_url", parsed.package_url)
    _check_for_empty_field("PackageInfo.project_url", parsed.project_url)
    _check_for_empty_field("PackageInfo.release_url", parsed.release_url)
    _check_for_empty_field("PackageInfo.version", parsed.version)

    return parsed


def fetch_package_metadata(package: str) -> PackageMetadata:
    """
    Fetches and validates package metadata from the PyPi API.
    :param package: Name of the package
    :raises ApiException: If there is an unrecoverable issue with the API
    """
    response_json = _make_request_and_validate(
        _calc_package_metadata_url(package),
        PackageInfo.get_schema(True),  # type: ignore[misc]
    )

    info = _parse_package_info(response_json)
    # Pre-populate with the top-level "latest" release information that is guaranteed to be there. If the `releases`
    # section duplicates this info, `releases` will be the source of truth.
    releases: dict[str, VersionMetadata] = {
        info.version: info.source_metadata,
    }

    # Iterate over the build artifacts released per build and exclusively pull-out the package source information.
    #
    # In some cases, there may be more than one `source` artifact. In theory, source code is the same for any version,
    # so prefer to pull tar-balls over other archival formats (like `.zip`s) for their compression ability.
    version: str
    artifacts: list[JsonType]
    rel_json: dict[str, JsonType] = response_json["releases"]  # type: ignore
    for version, artifacts in rel_json.items():  # type: ignore
        artifact: JsonType
        release_artifacts: list[VersionMetadata] = []
        for artifact in artifacts:
            if artifact["python_version"] == "source":  # type: ignore
                release_artifacts.append(_parse_version_metadata(artifact))
        if len(release_artifacts) == 0:
            raise ApiException("API did not return any source artifacts.")
        elif len(release_artifacts) == 1:
            releases[version] = release_artifacts[0]
        else:
            for rel_artifact in release_artifacts:
                if rel_artifact.filename.find(".tar"):
                    releases[version] = rel_artifact
                    break
            # In the future, it is likely that we will want to include more preference conditions. For now, if we can't
            # find a tarball, return the first item presented.
            else:
                releases[version] = release_artifacts[0]

    # If no version/release information is produced, raise an exception
    if len(releases) == 0:
        raise ApiException("API did not return any source information.")

    return PackageMetadata(
        info=info,
        releases=releases,
    )


def fetch_package_version_metadata(package: str, version: str) -> PackageMetadata:
    """
    Fetches and validates package metadata (at a specific version) from the PyPi API.
    :param package: Name of the package
    :param version: Version of the package
    :raises ApiException: If there is an unrecoverable issue with the API
    """
    response_json = _make_request_and_validate(
        _calc_package_version_metadata_url(package, version),
        PackageInfo.get_schema(False),  # type: ignore[misc]
    )

    info = _parse_package_info(response_json)

    return PackageMetadata(
        info=info,
        releases={
            info.version: info.source_metadata,
        },
    )
