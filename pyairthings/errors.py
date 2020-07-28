"""Define package errors."""


class AirthingsError(Exception):
    """Define a base error."""

    pass


class RequestError(AirthingsError):
    """Define an error related to invalid requests."""

    pass
