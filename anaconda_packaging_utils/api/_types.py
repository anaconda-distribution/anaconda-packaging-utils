"""
File:           _types.py
Description:    Contains private constants, types, and classes used in the APIs provided by this package.
"""

from typing import Final

#### Constants ####

# Timeout of HTTP requests, in seconds
DEFAULT_HTTP_REQ_TIMEOUT: Final[int] = 60

#### Classes ####


class BaseApiException(Exception):
    """
    Base API exception indicating an unrecoverable failure of an API.

    The APIs in this module should
    """

    def __init__(self, message: str):
        """
        Constructs an API exception
        :param message: String description of the issue encountered.
        """
        self.message = message if len(message) else "An unknown API issue was encountered."
        super().__init__(self.message)
