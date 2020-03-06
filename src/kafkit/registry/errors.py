"""Exceptions classes for the Registry client.
"""

__all__ = ('RegistryError', 'RegistryHttpError', 'RegistryRedirectionError',
           'RegistryBadRequestError', 'RegistryBrokenError')


class RegistryError(Exception):
    """Base exception for Registry errors.
    """


class RegistryHttpError(RegistryError):
    """A base exception that includes metadata about the HTTP response.

    Parameters
    ----------
    status_code : `int`
        The HTTP status code.
    *args
        A custom, arbitrary, error message. Setting this overrides ``message``.
    error_code : `int`
        The Confluent Schema Registry error code. See
        https://docs.confluent.io/current/schema-registry/docs/api.html#errors
    message : `str`
        The error message, intended to be the ``message`` field in Schema
        Registry error responses.
    """

    def __init__(self, status_code, *args, error_code=None, message=None):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message

        if message:
            super().__init__(
                f'Registry error ({status_code:d}). {error_code} - {message}')
        else:
            super().__init__(*args)


class RegistryRedirectionError(RegistryHttpError):
    """An exception for 3XX responses.
    """


class RegistryBadRequestError(RegistryHttpError):
    """An exception if the request is invalid (4XX errors).
    """


class RegistryBrokenError(RegistryHttpError):
    """An excpetion if the server is down (5XX errors).
    """
