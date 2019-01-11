"""Code to help use the Confluent Schema Registry that is not specific to a
particular http client library.

This code and architecture is inspired by
https://github.com/brettcannon/gidgethub and https://sans-io.readthedocs.io.
See licenses/gidgethub.txt for license info.
"""

__all__ = ('make_headers', 'decipher_response', 'decode_body', 'RegistryApi',
           'SchemaCache')

import abc
import json
import logging

import fastavro

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
        self.schemas = SchemaCache()

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
        """Send an HTTP GET request.

        Parameters
        ----------
        url : `str`
            The endpoint path, usually relative to the ``host`` attribute
            (an absolute URL is also okay). The url can be templated
            (``/a{/b}/c``, where ``b`` is a variable).
        url_vars : `dict`, optional
            A dictionary of variable names and values to expand the templated
            ``url`` parameter.

        Returns
        -------
        data
            The response body. If the response is JSON, the data is parsed
            into a Python object.

        Raises
        ------
        kafkit.registry.RegistryRedirectionError
            Raised if the server returns a 3XX status.
        kafkit.registry.RegistryRadRequestError
            Raised if the server returns a 4XX status because the request
            is incorrect, not authenticated, or not authorized.
        kafkit.registry.RegistryBrokenError
            Raised if the server returns a 5XX status because something is
            wrong with the server itself.
        """
        data = await self._make_request("GET", url, url_vars, b"")
        return data

    async def post(self, url, url_vars=dict(), *, data):
        """Send an HTTP POST request.

        Parameters
        ----------
        url : `str`
            The endpoint path, usually relative to the ``host`` attribute
            (an absolute URL is also okay). The url can be templated
            (``/a{/b}/c``, where ``b`` is a variable).
        url_vars : `dict`, optional
            A dictionary of variable names and values to expand the templated
            ``url`` parameter.
        data : object
            The body of the request as a JSON-serializable object.

        Returns
        -------
        data
            The response body. If the response is JSON, the data is parsed
            into a Python object.

        Raises
        ------
        kafkit.registry.RegistryRedirectionError
            Raised if the server returns a 3XX status.
        kafkit.registry.RegistryRadRequestError
            Raised if the server returns a 4XX status because the request
            is incorrect, not authenticated, or not authorized.
        kafkit.registry.RegistryBrokenError
            Raised if the server returns a 5XX status because something is
            wrong with the server itself.
        """
        data = await self._make_request("POST", url, url_vars, data)
        return data

    async def patch(self, url, url_vars=dict(), *, data):
        """Send an HTTP PATCH request.

        Parameters
        ----------
        url : `str`
            The endpoint path, usually relative to the ``host`` attribute
            (an absolute URL is also okay). The url can be templated
            (``/a{/b}/c``, where ``b`` is a variable).
        url_vars : `dict`, optional
            A dictionary of variable names and values to expand the templated
            ``url`` parameter.
        data : object
            The body of the request as a JSON-serializable object.

        Returns
        -------
        data
            The response body. If the response is JSON, the data is parsed
            into a Python object.

        Raises
        ------
        kafkit.registry.RegistryRedirectionError
            Raised if the server returns a 3XX status.
        kafkit.registry.RegistryRadRequestError
            Raised if the server returns a 4XX status because the request
            is incorrect, not authenticated, or not authorized.
        kafkit.registry.RegistryBrokenError
            Raised if the server returns a 5XX status because something is
            wrong with the server itself.
        """
        data = await self._make_request("PATCH", url, url_vars, data)

    async def put(self, url, url_vars=dict(), data=b""):
        """Send an HTTP PUT request.

        Parameters
        ----------
        url : `str`
            The endpoint path, usually relative to the ``host`` attribute
            (an absolute URL is also okay). The url can be templated
            (``/a{/b}/c``, where ``b`` is a variable).
        url_vars : `dict`, optional
            A dictionary of variable names and values to expand the templated
            ``url`` parameter.
        data : object, optional
            The body of the request as a JSON-serializable object.

        Returns
        -------
        data
            The response body. If the response is JSON, the data is parsed
            into a Python object.

        Raises
        ------
        kafkit.registry.RegistryRedirectionError
            Raised if the server returns a 3XX status.
        kafkit.registry.RegistryRadRequestError
            Raised if the server returns a 4XX status because the request
            is incorrect, not authenticated, or not authorized.
        kafkit.registry.RegistryBrokenError
            Raised if the server returns a 5XX status because something is
            wrong with the server itself.
        """
        data = await self._make_request("PATCH", url, url_vars, data)

    async def delete(self, url, url_vars=dict(), *, data=b""):
        """Send an HTTP DELETE request.

        Parameters
        ----------
        url : `str`
            The endpoint path, usually relative to the ``host`` attribute
            (an absolute URL is also okay). The url can be templated
            (``/a{/b}/c``, where ``b`` is a variable).
        url_vars : `dict`, optional
            A dictionary of variable names and values to expand the templated
            ``url`` parameter.
        data : object, optional
            The body of the request as a JSON-serializable object.

        Returns
        -------
        data
            The response body. If the response is JSON, the data is parsed
            into a Python object.

        Raises
        ------
        kafkit.registry.RegistryRedirectionError
            Raised if the server returns a 3XX status.
        kafkit.registry.RegistryRadRequestError
            Raised if the server returns a 4XX status because the request
            is incorrect, not authenticated, or not authorized.
        kafkit.registry.RegistryBrokenError
            Raised if the server returns a 5XX status because something is
            wrong with the server itself.
        """
        data = await self._make_request("DELETE", url, url_vars, data)

    @staticmethod
    def _prep_schema(schema):
        """Prep a schema for submission through an API request by
        removing any fastavro hints and dumping to a string.
        """
        schema = schema.copy()
        try:
            del schema['__fastavro_parsed']
        except KeyError:
            pass
        # sort keys for repeatable tests
        return json.dumps(schema, sort_keys='true')

    async def register_schema(self, schema, subject=None):
        """Register a schema or get the ID of an existing schema.

        Wraps ``POST /subjects/(string: subject)/versions``.

        Parameters
        ----------
        schema : `dict`
            An `Avro schema <http://avro.apache.org/docs/current/spec.html>`__
            as a Python dictionary.
        subject : `str`, optional
            The subject to register the schema under. If not provided, the
            fully-qualified name of the schema is adopted as the subject name.

        Returns
        -------
        schema_id : `int`
            The ID of the schema in the registry.

        Notes
        -----
        The schema and ID are cached locally so that repeated calls are fast.
        This cache is shared by other high-level methods, like
        `get_schema_by_id`.
        """
        # Parsing the schema also produces a fully-qualified name, which is
        # useful for getting a subject name.
        schema = fastavro.parse_schema(schema)

        # look in cache first
        try:
            schema_id = self.schemas[schema]
            return schema_id
        except KeyError:
            pass

        if subject is None:
            try:
                subject = schema['name']
            except (KeyError, TypeError):
                raise RuntimeError('Cannot get a subject name from a \'name\' '
                                   f'key in the schema: {schema!r}')

        result = await self.post(
            '/subjects{/subject}/versions',
            url_vars={'subject': subject},
            data={'schema': self._prep_schema(schema)})

        # add to cache
        self.schemas.insert(schema, result['id'])

        return result['id']

    async def get_schema_by_id(self, schema_id):
        """Get a schema from the registry given its ID.

        Wraps ``GET /schemas/ids/{int: id}``.

        Parameters
        ----------
        schema_id : `int`
            The ID of the schema in the registry.

        Returns
        -------
        schema : `dict`
            The Avro schema. The schema is pre-parsed by
            `fastavro.parse_schema`.

        Notes
        -----
        The schema and ID are cached locally so that repeated calls are fast.
        This cache is shared by other high-level methods, like
        `register_schema`.
        """
        # Look in the cache first
        try:
            schema = self.schemas[schema_id]
            return schema
        except KeyError:
            pass

        result = await self.get(
            '/schemas/ids{/schema_id}',
            url_vars={'schema_id': str(schema_id)})
        schema = fastavro.parse_schema(result['schema'])

        # Add schema to cache
        self.schemas.insert(schema, schema_id)

        return schema


class MockRegistryApi(RegistryApi):
    """A mock implementation of the RegistryApi client that doens't do
    network operations and provides attributes for introspection.
    """

    DEFAULT_HEADERS = {
        'content-type': "application/vnd.schemaregistry.v1+json"
    }

    def __init__(self, host='http://registry:8081',
                 status_code=200, headers=None, body=b''):
        super().__init__(host=host)
        self.response_code = status_code
        self.response_headers = headers if headers else self.DEFAULT_HEADERS
        self.response_body = body

    async def _request(self, method, url, headers, body):
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body
        response_headers = self.response_headers.copy()
        return self.response_code, response_headers, self.response_body


class SchemaCache:
    """A cache of schemas that maintains a mapping of schemas and their IDs
    in a Schema Registry.

    Notes
    -----
    Use key access to obtain the schema either by ID, or by the value of the
    schema itself.
    """

    def __init__(self):
        self._id_to_schema = {}
        self._schema_to_id = {}

    def insert(self, schema, schema_id):
        """Insert a schema into the cache.

        Parameters
        ----------
        schema : `dict`
            An Avro schema.
        schema_id : `int`
            ID of the schema in a Schema Registry.
        """
        # ensure the cached schemas are always parsed, and then serialize
        # so it's hashable
        serialized_schema = SchemaCache._serialize_schema(schema)

        self._id_to_schema[schema_id] = serialized_schema
        self._schema_to_id[serialized_schema] = schema_id

    def __getitem__(self, key):
        if isinstance(key, int):
            return json.loads(self._id_to_schema[key])
        else:
            # Key must be a schema
            # Always ensure the schema is parsed
            schema = key.copy()
            try:
                serialized_schema = SchemaCache._serialize_schema(schema)
            except Exception:
                # If the schema couldn't be parsed, its not going to be a
                # valid key anyhow.
                raise KeyError
            return self._schema_to_id[serialized_schema]

    @staticmethod
    def _serialize_schema(schema):
        """Predictably serialize the schema so that it's hashable.
        """
        schema = fastavro.parse_schema(schema)
        return json.dumps(schema, sort_keys=True)
