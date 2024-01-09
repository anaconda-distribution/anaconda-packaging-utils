"""
File:           jira_api.py
Description:    Wrapper library that provides tools for using the Python JIRA API. The primary purpose of this wrapper
                is to simplify and standardize the authentication process.

                JIRA API links:
                  - Source: https://github.com/pycontribs/jira
                  - Docs: https://jira.readthedocs.io/index.html#
"""
import logging
from typing import Callable, Final

from jira.client import JIRA

from anaconda_packaging_utils.storage.config_data import ConfigData

# Logging object for this module
log = logging.getLogger(__name__)

# Where our JIRA boards are hosted
_JIRA_HOST_URL: Final[str] = "https://anaconda.atlassian.net/"


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


class JiraApi:
    """
    Singleton wrapper to the Python Jira project. This "ensures" that we only construct and authenticate the underlying
    Jira object once.
    """

    # The Jira API is wrapped in a list as a cheesy way to work around an initialization problem. Defaulting to `None`
    # or using an `Optional` causes the static analyzer to freak out on every use of the `_jira`, even if the static
    # variable has to have been initialized by instance-method call time.
    _jira: list[JIRA] = []

    def __init__(self) -> None:
        """
        Constructs a JiraApi instance
        :raises ApiException: If there was a failure to authenticate.
        """
        if len(JiraApi._jira) == 0:
            data_store: Final[ConfigData] = ConfigData()
            try:
                JiraApi._jira.append(
                    JIRA(
                        _JIRA_HOST_URL,
                        basic_auth=(data_store["user_info.email"], data_store["token.jira"]),
                    )
                )
            except Exception as e:
                raise ApiException("Failed to auth or connect to JIRA") from e

    def access_jira(self, callback: Callable[[JIRA], None]) -> None:
        """
        Execute Jira commands via a callback. This ensures some amount of safety around our singleton design pattern
        while also allowing the caller to full access of the API.
        :param callback: Callback that provides access to the single Jira client instance
        :raises ApiException: If the callback throws, it will re-wrap the exception into a generic `ApiException` for
                              easier exception handling.
        """
        try:
            callback(JiraApi._jira[0])
        except Exception as e:
            raise ApiException("`access_jira()` callback raised an exception") from e
