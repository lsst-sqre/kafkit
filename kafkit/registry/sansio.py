"""Code to help use the Confluent Schema Registry that is not specific to a
particular http client library.

This code and architecture is inspired by
https://github.com/brettcannon/gidgethub and https://sans-io.readthedocs.io.
See licenses/gidgethub.txt for license info.
"""

__all__ = ('make_headers', 'decipher_response', 'decode_body', 'RegistryApi',
           'MockRegistryApi', 'SchemaCache', 'SubjectCache')

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
        - If the message is empty or ``content_type`` is `None`, the returned
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


class RegistryApi(metaclass=abc.ABCMeta):
    """A baseclass for Confluent Schema Registry clients.
    """

    def __init__(self, *, url):
        self.url = url
        self._schema_cache = SchemaCache()
        self._subject_cache = SubjectCache(self._schema_cache)

    @property
    def schema_cache(self):
        """The schema cache (`~kafkit.registry.sansio.SchemaCache`).
        """
        return self._schema_cache

    @property
    def subject_cache(self):
        """The subject cache (`~kafkit.registry.sansio.SubjectCache`).
        """
        return self._subject_cache

    @abc.abstractmethod
    async def _request(self, method, url, headers, body):
        """Make an HTTP request.
        """

    async def _make_request(self, method, url, url_vars, data):
        """Construct and make an HTTP request.
        """
        expanded_url = format_url(host=self.url, url=url, url_vars=url_vars)
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
            The endpoint path, usually relative to the ``RegistryApi.url``
            attribute (an absolute URL is also okay). The url can be templated
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
            The endpoint path, usually relative to the ``RegistryApi.url``
            attribute (an absolute URL is also okay). The url can be templated
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
            The endpoint path, usually relative to the ``RegistryApi.url``
            attribute (an absolute URL is also okay). The url can be templated
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
            The endpoint path, usually relative to the ``RegistryApi.url``
            attribute (an absolute URL is also okay). The url can be templated
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
            The endpoint path, usually relative to the ``RegistryApi.url``
            attribute (an absolute URL is also okay). The url can be templated
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
            schema_id = self.schema_cache[schema]
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
        self.schema_cache.insert(schema, result['id'])

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

        See also
        --------
        get_schema_by_subject

        Notes
        -----
        The schema and ID are cached locally so that repeated calls are fast.
        This cache is shared by other high-level methods, like
        `register_schema`.
        """
        # Look in the cache first
        try:
            schema = self.schema_cache[schema_id]
            return schema
        except KeyError:
            pass

        result = await self.get(
            '/schemas/ids{/schema_id}',
            url_vars={'schema_id': str(schema_id)})
        schema = fastavro.parse_schema(json.loads(result['schema']))

        # Add schema to cache
        self.schema_cache.insert(schema, schema_id)

        return schema

    async def get_schema_by_subject(self, subject, version='latest'):
        """Get a schema for a subject in the registry.

        Wraps ``GET /subjects/(string: subject)/versions/(versionId: version)``

        Parameters
        ----------
        subject : `str`
            Name of the subject in the Schema Registry.
        version : `int` or `str`, optional
            The version of the schema with respect to the ``subject``. To
            get the latest schema, supply ``"latest"`` (default).

        Returns
        -------
        schema_info : `dict`
            A dictionary with the schema and metadata about the schema. The
            keys are:

            ``"schema"``
                The schema itself, preparsed by `fastavro.parse_schema`.
            ``"subject"``
                The subject this schema is registered under in the registry.
            ``"version"``
                The version of this schema with respect to the ``subject``.
            ``"id"``
                The ID of this schema (compatible with `get_schema_by_id`).

        See also
        --------
        get_schema_by_id

        Notes
        -----
        Results from this method are cached locally, so repeated calls are
        fast. Keep in mind that any call with the ``version`` parameter set
        to ``"latest"`` will always miss the cache. The schema is still
        cached, though, under it's true subject version. If you app repeatedly
        calls this method, and you want to make use of caching, replace
        ``"latest"`` versions with integer versions once they're known.
        """
        try:
            # The SubjectCache.get method is designed to have the same return
            # type as this method.
            return self.subject_cache.get(subject, version)
        except ValueError:
            pass

        result = await self.get(
            '/subjects{/subject}/versions{/version}',
            url_vars={'subject': subject, 'version': str(version)})

        schema = fastavro.parse_schema(json.loads(result['schema']))

        try:
            self.subject_cache.insert(
                result['subject'],
                result['version'],
                schema_id=result['id'],
                schema=schema)
        except TypeError:
            # Can't cache versions like "latest"
            pass

        return {
            'id': result['id'],
            'version': result['version'],
            'subject': result['subject'],
            'schema': schema
        }


class MockRegistryApi(RegistryApi):
    """A mock implementation of the RegistryApi client that doensn't do
    network operations and provides attributes for introspection.
    """

    DEFAULT_HEADERS = {
        'content-type': "application/vnd.schemaregistry.v1+json"
    }

    def __init__(self, url='http://registry:8081',
                 status_code=200, headers=None, body=b''):
        super().__init__(url=url)
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

    def __contains__(self, key):
        try:
            self[key]
        except KeyError:
            return False
        return True

    @staticmethod
    def _serialize_schema(schema):
        """Predictably serialize the schema so that it's hashable.
        """
        schema = fastavro.parse_schema(schema)
        return json.dumps(schema, sort_keys=True)


class SubjectCache:
    """A cache of subjects in a schema registry that maps subject and version
    tuples to an actual schema.

    Parameters
    ----------
    schema_cache : `SchemaCache`
        A schema cache instance.

    Notes
    -----
    The SubjectCache provides a subject-aware layer over the `SchemaCache`.
    While schemas and their IDs are unique in a schema registry, multiple
    subject-version combinations can point to the same schema-ID combination.

    When you insert a schema into the SubjectCache, you are also inserting
    the schema and schema ID into the member `SchemaCache`.
    """

    def __init__(self, schema_cache):
        self.schema_cache = schema_cache

        self._subject_to_id = {}

    def get_id(self, subject, version):
        """Get the schema ID of a subject version.

        Parameters
        ----------
        subject : `str`
            The name of the subject.
        version : `int`
            The version number of the schema in the subject.

        Returns
        -------
        schema_id : `int`
            ID of the schema in a Schema Registry.

        Raises
        ------
        ValueError
            Raised if the schema does not exist in the cache.

        See also
        --------
        get_schema
        get
        """
        try:
            return self._subject_to_id[(subject, version)]
        except KeyError as e:
            raise ValueError from e

    def get_schema(self, subject, version):
        """Get the schema of a subject version.

        Parameters
        ----------
        subject : `str`
            The name of the subject.
        version : `int`
            The version number of the schema in the subject.

        Returns
        -------
        schema : `dict`
            An Avro schema, preparsed by `fastavro.parse_schema`.

        Raises
        ------
        ValueError
            Raised if the schema does not exist in the cache.

        See also
        --------
        get_id
        get
        """
        try:
            return self.schema_cache[self.get_id(subject, version)]
        except KeyError as e:
            raise ValueError from e

    def get(self, subject, version):
        """Get the full set of schema and ID information for a subject version.

        Parameters
        ----------
        subject : `str`
            The name of the subject.
        version : `int`
            The version number of the schema in the subject.

        Returns
        -------
        schema_info : `dict`
            A dictionary with the full set of information about the cached
            schema. The keys are:

            ``"subject"``
                The name of the subject.
            ``"version"``
                The version number of the schema in the subject.
            ``"id"``
                ID of the schema in a Schema Registry.
            ``"schema"``
                The Avro schema, preparsed by `fastavro.parse_schema`.

        Raises
        ------
        ValueError
            Raised if the schema does not exist in the cache.

        See also
        --------
        get_id
        get_schema
        """
        try:
            schema_id = self.get_id(subject, version)
            schema = self.schema_cache[schema_id]
        except KeyError as e:
            raise ValueError from e

        # Important: this return type maches RegistryApi.get_schema_by_subject
        # If this is changed, make sure get_schema_by_subject is also changed.
        return {
            'subject': subject,
            'version': version,
            'id': schema_id,
            'schema': schema
        }

    def insert(self, subject, version, schema_id=None, schema=None):
        """Insert a subject version into the cache.

        Parameters
        ----------
        subject : `str`
            The name of the subject.
        version : `int`
            The version number of the schema in the subject.
        schema_id : `int`, optional
            ID of the schema in a Schema Registry. See Notes.
        schema : `dict`, optional
            The Avro schema itself. See Notes.

        Raises
        ------
        TypeError
            Raised if the ``version`` parameter is a string. String-based
            versions, like "latest," cannot be cached.
        ValueError
            Raised if the ``schema_id`` or ``schema`` parameters are needed
            but aren't set. See Notes.

        Notes
        -----
        If the subject version being cached is already in the schema cache,
        then only one of ``schema_id`` or ``schema`` need to be passed to this
        method. However, if the schema isn't cached, then both ``schema_id``
        and ``schema`` need to be set. The ``schema_id`` and ``schema`` are
        added to the underlying schema cache.
        """
        if not isinstance(version, int):
            raise TypeError(
                'Cannot cache a non-integer version of a subject '
                '(such as "latest").'
            )

        if schema_id is not None:
            if schema_id not in self.schema_cache:
                # Need to add this schema to the schema_cache first
                if schema is None:
                    raise ValueError(
                        'Trying to cache the schema ID for subject '
                        f'{subject!r}, version {version}, but its schema ID '
                        f'({schema_id}) and schema are not in the schema '
                        'cache. Provide the schema as well as the schema_id.'
                    )
                self.schema_cache.insert(schema, schema_id)
            self._subject_to_id[(subject, version)] = schema_id

        elif schema is not None:
            if schema not in self.schema_cache:
                # Need to add this schema to the schema_cache first
                if schema_id is None:
                    raise ValueError(
                        'Trying to cache the schema ID for subject '
                        f'{subject!r}, version {version}, but it\'s schema ID '
                        'and schema are not in the schema cache. Provide the '
                        'schema argument as well as schema_id.'
                    )
                self.schema_cache.insert(schema, schema_id)
            schema_id = self.schema_cache[schema]
            self._subject_to_id[(subject, version)] = schema_id

        else:
            raise ValueError(
                'Provide either a schema_id or schema argument (or both).'
            )

    def __contains__(self, key):
        return key in self._subject_to_id
