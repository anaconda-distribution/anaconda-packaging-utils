"""
File:           types.py
Description:    Contains common types and classes used in the APIs provided by this package.
"""


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
        super().__init__(message if len(message) else "An unknown API issue was encountered.")
