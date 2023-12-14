"""
File:           github_api.py
Description:    Library that provides tools for using the PyGitHub API.

                As the PyGitHub project provides a pretty extensive API, this library primarily provides utility
                wrappers.
"""
import logging
from typing import Final, Optional

from github import Github, Repository

# TODO enforce type checking when `percy` exports types
from percy.render.recipe import Recipe

import anaconda_packaging_utils.cryptography.utils as crypto_utils
from anaconda_packaging_utils.api._types import BaseApiException
from anaconda_packaging_utils.storage import file_io
from anaconda_packaging_utils.storage.config_data import ConfigData

# Logging object for this module
log = logging.getLogger(__name__)

# Anaconda Recipes organization name
ANACONDA_RECIPE_BASE: Final[str] = "AnacondaRecipes"
# Path to find the `aggregate` repository
REPO_AGGREGATE_PATH: Final[str] = f"{ANACONDA_RECIPE_BASE}/aggregate"


class ApiException(BaseApiException):
    """
    Indicates an exception occurred with this API.
    """

    pass


class GitHubApi:
    """
    Singleton wrapper to the PyGithub project. This "ensures" that we only construct and authenticate the underlying
    Github object once. All convenience member.

    As best as I can tell, the `PyGitHub` project is not guaranteed to be thread safe. However, read-only GitHub API
    requests are not likely to cause a threading issue, by their very nature.
    """

    # The GitHub API is wrapped in a list as a cheesy way to work around an initialization problem. Defaulting to `None`
    # or using an `Optional` causes the static analyzer to freak out on every use of the `_gh`, even if the static
    # variable has to have been initialized by instance-method call time.
    _gh: list[Github] = []

    def __init__(self) -> None:
        """
        Constructs a GitHubApi Instance
        :raises ApiException: If there was a failure to authenticate.
        """
        if len(GitHubApi._gh) == 0:
            try:
                GitHubApi._gh.append(Github(ConfigData()["token.github"]))
            except Exception as e:
                raise ApiException("Failed to auth or connect to GitHub") from e

    def fetch_aggregate(self) -> Repository.Repository:
        """
        Convenience function for accessing the `aggregate` repo.
        :raises ApiException: If there was a failure to access the repo.
        :returns: Repository object that represents `aggregate`.
        """
        try:
            return GitHubApi._gh[0].get_repo(REPO_AGGREGATE_PATH)
        except Exception as e:
            raise ApiException("Failed to access `aggregate`") from e

    def fetch_feedstock(self, package: str) -> tuple[Repository.Repository, Optional[str]]:
        """
        Convenience function for accessing a feedstock repository.
        :param package: Name of the target package.
        :raises ApiException: If there was a failure to access the repo.
        :returns: Repository object that represents the target package feedstock AND if possible, the SHA-1 hash of the
            version of the repo set in `aggregate`.
        """
        # Treat `aggregate` as the initial source of truth. As `aggregate` "should" be what's publicly available, we
        # should use it as a basis of our target feedstock version.
        aggregate: Repository.Repository = self.fetch_aggregate()
        feedstock_name: str = f"{package}-feedstock"
        sha: Optional[str] = None
        # Attempt to determine the version (determined by SHA-1 hash) that `aggregate` points to. If that fails,
        # continue to fetch the repo anyways.
        try:
            submodule = aggregate.get_contents(f"/{feedstock_name}")
            # Although this shouldn't happen, the static analyzer would like us to cover the case where `get_contents()`
            # returns a list. In the event we do hit this case, log it.
            if isinstance(submodule, list):
                raise ApiException(f"API returned a list for submodule {feedstock_name}")
            sha = submodule.sha
            # Reset the SHA if it is invalid. Act as if we did not find it.
            if sha is not None and not crypto_utils.is_valid_sha1(sha):
                log.warning("Received invalid SHA from `%s`: %s", package, sha)
                sha = None
        except Exception as e:  # pylint: disable=broad-exception-caught
            log.warning(
                "Failed to acquire SHA of `%s` from `aggregate`," " with exception %s",
                package,
                e,
            )

        try:
            return (
                GitHubApi._gh[0].get_repo(f"{ANACONDA_RECIPE_BASE}/{feedstock_name}"),
                sha,
            )
        except Exception as e:
            raise ApiException(f"Failed to access `{feedstock_name}` from aggregate") from e

    def fetch_recipe(self, package: str) -> Recipe:
        """
        Pulls a recipe file down for use with `percy`.
        :param package: Name of the target package.
        :raises ApiException: If there was a failure to access the repo.
        :returns: Recipe, as a Percy object.
        """
        feedstock, sha = self.fetch_feedstock(package)
        # Render-safe for the API, default to empty string
        sha = "" if sha is None else sha

        meta = feedstock.get_contents("/recipe/meta.yaml", ref=sha)
        if isinstance(meta, list):
            raise ApiException("GitHub API returned `meta.yaml` as a list")
        # Content is returned encoded in Base-64
        meta_content = meta.decoded_content.decode()
        if not meta_content or not isinstance(meta_content, str):
            raise ApiException("Github API returned `meta.yaml` as an invalid string")
        tmp = file_io.write_temp_file(
            meta_content,
            tag=f"{package}_recipe",
        )
        log.info("Recipe for `%s` downloaded to: %s", package, tmp)
        return Recipe.from_file(tmp)
