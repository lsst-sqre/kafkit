"""Code to help use the Confluent Schema Registry that is not specific to a
particular http client library.

This code and architecture is inspired by
https://github.com/brettcannon/gidgethub and https://sans-io.readthedocs.io.
See licenses/gidgethub.txt for license info.
"""

__all__ = ('make_headers', 'decipher_response', 'decode_body', 'RegistryApi')

import abc
import json
import logging

from kafkit.httputils import format_url, parse_content_type
from kafkit.registry.errors import (
    RegistryRedirectionError, RegistryBadRequestError, RegistryBrokenError,
    RegistryHttpError)


def make_headers():
    """Make HTTP headers for the Confluent Schema Registry.

    Returns
    -------
    headers : `dict`
        A dictionary of HTTP headers for a Confluent Schema Registry request.
        All keys are normalized to lowercase for consistency.
    """
    headers = {
        'accept': 'application/vnd.schemaregistry.v1+json'
    }
    return headers


def decipher_response(status_code, headers, body):
    """Process a response.
    """
    data = decode_body(headers.get("content-type"), body)

    if status_code in (200, 201, 204):
        return data
    else:
        # Process an error. First try to get the error message from the
        # response and then raise an appropriate exception.
        try:
            error_code = data['error_code']
            message = data['message']
        except (TypeError, KeyError):
            error_code = None
            message = None

        if status_code >= 500:
            raise RegistryBrokenError(
                status_code=status_code, error_code=error_code,
                message=message)
        elif status_code >= 400:
            raise RegistryBadRequestError(
                status_code=status_code, error_code=error_code,
                message=message)
        elif status_code >= 300:
            raise RegistryRedirectionError(status_code=status_code)
        else:
            raise RegistryHttpError(status_code=status_code)


def decode_body(content_type, body):
    """Decode an HTTP body based on the specified content type.

    Parameters
    ----------
    content_type : `str`
        Content type string, from the response header.
    body : `bytes`
        Bytes content of the body.

    Returns
    -------
    decoded
        The decoded message.

        - If the content type is recognized as JSON, the result will be an
          object parsed from the JSON message.
        - If the content type isn't recognized, the body is decoded into a
          string.
        - If the message is empty or ``content_type` is `None`, the returned
          value is `None`.
    """
    logger = logging.getLogger(__name__)
    type_, encoding = parse_content_type(content_type)
    if not len(body) or not content_type:
        return None
    decoded_body = body.decode(encoding)
    if type_ in ('application/vnd.schemaregistry.v1+json', 'application/json'):
        return json.loads(decoded_body)
    else:
        logger.warning(f"Unrecognized content type: {type_!r}. The message "
                       "is being decoded into a string. kafkit might need "
                       "to be updated if the registry server is serving new "
                       "content types.")
        return decoded_body


class RegistryApi(abc.ABC):
    """A baseclass for Confluent Schema Registry clients.
    """

    def __init__(self, *, host):
        self.host = host

    @abc.abstractmethod
    async def _request(self, method, url, headers, body):
        """Make an HTTP request.
        """

    async def _make_request(self, method, url, url_vars, data):
        """Construct and make an HTTP request.
        """
        expanded_url = format_url(host=self.host, url=url, url_vars=url_vars)
        request_headers = make_headers()

        if data == b"":
            body = b""
            request_headers['content-length'] = '0'
        else:
            charset = "utf-8"
            body = json.dumps(data).encode(charset)
            request_headers['content-type'] \
                = f"application/json; charset={charset}"
            request_headers['content-length'] = str(len(body))

        response = await self._request(method, expanded_url, request_headers,
                                       body)
        response_data = decipher_response(*response)
        return response_data

    async def get(self, url, url_vars=dict()):
        data = await self._make_request("GET", url, url_vars, b"")
        return data

    async def post(self, url, url_vars=dict(), *, data):
        data = await self._make_request("POST", url, url_vars, data)
        return data

    async def patch(self, url, url_vars=dict(), *, data):
        data = await self._make_request("PATCH", url, url_vars, data)

    async def put(self, url, url_vars=dict(), data=b""):
        data = await self._make_request("PATCH", url, url_vars, data)

    async def delete(self, url, url_vars=dict(), *, data=b""):
        data = await self._make_request("DELETE", url, url_vars, data)
