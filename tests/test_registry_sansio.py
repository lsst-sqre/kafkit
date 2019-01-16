"""Tests for the kafkit.registry.sansio module.
"""

import json

import pytest

from kafkit.registry.sansio import (make_headers, decipher_response,
                                    MockRegistryApi, SchemaCache, SubjectCache)
from kafkit.registry.errors import (
    RegistryRedirectionError, RegistryBadRequestError, RegistryBrokenError)


def test_make_headers():
    headers = make_headers()

    assert headers['accept'] == 'application/vnd.schemaregistry.v1+json'


def test_decipher_response_200():
    status = 200
    headers = {
        "content-type": "application/vnd.schemaregistry.v1+json"
    }
    data = [1, 2, 3]
    body = json.dumps(data).encode('utf-8')
    returned_data = decipher_response(status, headers, body)
    assert returned_data == data


def test_decipher_response_200_empty():
    status = 200
    headers = {
        "content-type": "application/vnd.schemaregistry.v1+json"
    }
    body = b""
    returned_data = decipher_response(status, headers, body)
    assert returned_data is None


def test_decipher_response_500_no_message():
    status = 500
    headers = {
        "content-type": "application/vnd.schemaregistry.v1+json"
    }
    body = b""
    with pytest.raises(RegistryBrokenError):
        decipher_response(status, headers, body)


def test_decipher_response_500_with_message():
    status = 500
    headers = {
        "content-type": "application/vnd.schemaregistry.v1+json"
    }
    body = json.dumps({
        'error': 12345,
        'message': "I've got reasons"
    }).encode('utf-8')
    with pytest.raises(RegistryBrokenError):
        decipher_response(status, headers, body)


def test_decipher_response_401_no_message():
    status = 401
    headers = {
        "content-type": "application/vnd.schemaregistry.v1+json"
    }
    body = b""
    with pytest.raises(RegistryBadRequestError):
        decipher_response(status, headers, body)


def test_decipher_response_401_with_message():
    status = 401
    headers = {
        "content-type": "application/vnd.schemaregistry.v1+json"
    }
    body = json.dumps({
        'error': 12345,
        'message': "I've got reasons"
    }).encode('utf-8')
    with pytest.raises(RegistryBadRequestError):
        decipher_response(status, headers, body)


def test_decipher_response_301_no_message():
    status = 301
    headers = {
        "content-type": "application/vnd.schemaregistry.v1+json"
    }
    body = b""
    with pytest.raises(RegistryRedirectionError):
        decipher_response(status, headers, body)


def test_decipher_response_301_with_message():
    status = 301
    headers = {
        "content-type": "application/vnd.schemaregistry.v1+json"
    }
    body = json.dumps({
        'error': 12345,
        'message': "I've got reasons"
    }).encode('utf-8')
    with pytest.raises(RegistryRedirectionError):
        decipher_response(status, headers, body)


@pytest.mark.asyncio
async def test_registryapi_get_empty():
    """Test client with a regular GET call with empty response.
    """
    client = MockRegistryApi(url='http://registry:8081')
    response = await client.get('/subjects{/subject}/versions',
                                url_vars={'subject': 'helloworld'})

    assert response is None
    # Check URL formatting
    assert client.url == 'http://registry:8081/subjects/helloworld/versions'
    # Check headers
    assert client.headers['accept'] == make_headers()['accept']
    assert client.headers['content-length'] == '0'


@pytest.mark.asyncio
async def test_registryapi_get_json():
    """Test client with a regular GET call with a JSON response.
    """
    expected_data = {'hello': 'world'}
    client = MockRegistryApi(
        url='http://registry:8081',
        body=json.dumps(expected_data).encode('utf-8'))
    response = await client.get('/subjects{/subject}/versions',
                                url_vars={'subject': 'helloworld'})

    assert response == expected_data


@pytest.mark.asyncio
async def test_register_schema():
    """Test the RegistryApi.register_schema() method.
    """
    input_schema = {
        'type': 'record',
        'name': 'schema1',
        'namespace': 'test-schemas',
        'fields': [
            {'name': 'a', 'type': 'int'}
        ]
    }

    # Body that we expect the registry API to return given the request.
    expected_body = json.dumps({'id': 1}).encode('utf-8')

    client = MockRegistryApi(
        url='http://registry:8081',
        body=expected_body
    )
    schema_id = await client.register_schema(input_schema)
    assert schema_id == 1

    # Test details of the request itself
    assert client.method == 'POST'
    assert client.url == \
        'http://registry:8081/subjects/test-schemas.schema1/versions'
    sent_json = json.loads(client.body)
    assert 'schema' in sent_json
    sent_schema = json.loads(sent_json['schema'])
    assert '__fastavro_parsed' not in sent_schema
    assert sent_schema['name'] == 'test-schemas.schema1'

    # Check that the schema is in the cache and is parsed
    assert client.schemas[1]['name'] == 'test-schemas.schema1'
    assert '__fastavro_parsed' in client.schemas[1]

    # Make a second call to get the schema out
    new_schema_id = await client.register_schema(input_schema)
    assert new_schema_id == schema_id


@pytest.mark.asyncio
async def test_get_schema_by_id():
    """Test the RegistryApi.get_schema_by_id method.
    """
    # Body that we expect the registry API to return given the request.
    input_schema = {
        'type': 'record',
        'name': 'schema1',
        'namespace': 'test-schemas',
        'fields': [
            {'name': 'a', 'type': 'int'}
        ]
    }
    expected_body = json.dumps({'schema': input_schema}).encode('utf-8')

    client = MockRegistryApi(
        body=expected_body
    )

    schema = await client.get_schema_by_id(1)

    # Check that the schema was parsed
    assert schema['name'] == 'test-schemas.schema1'
    assert '__fastavro_parsed' in client.schemas[1]

    # Check that the schem was cached
    assert client.schemas[1]['name'] == 'test-schemas.schema1'

    # Check the request
    assert client.url == 'http://registry:8081/schemas/ids/1'
    assert client.method == 'GET'


@pytest.mark.asyncio
async def test_get_schema_by_subject():
    """Test the RegistryApi.get_schema_by_subject method.
    """
    # Body that we expect the registry API to return given the request.
    expected_body = {
        'schema': {
            'type': 'record',
            'name': 'schema1',
            'namespace': 'test-schemas',
            'fields': [
                {'name': 'a', 'type': 'int'}
            ]
        },
        "subject": "schema1",
        "version": 1,
        "id": 2
    }

    client = MockRegistryApi(
        body=json.dumps(expected_body).encode('utf-8')
    )

    result = await client.get_schema_by_subject('schema1')

    # Check that the schema was parsed
    assert result['schema']['name'] == 'test-schemas.schema1'
    assert '__fastavro_parsed' in result['schema']
    # Check other content of the result
    assert result['version'] == 1
    assert result['id'] == 2
    assert result['subject'] == 'schema1'

    # Check the request
    assert client.url \
        == 'http://registry:8081/subjects/schema1/versions/latest'
    assert client.method == 'GET'


def test_schema_cache():
    cache = SchemaCache()

    schema1 = {
        'type': 'record',
        'name': 'schema1',
        'namespace': 'test-schemas',
        'fields': [
            {'name': 'a', 'type': 'int'}
        ]
    }

    schema2 = {
        'type': 'record',
        'name': 'schema2',
        'namespace': 'test-schemas',
        'fields': [
            {'name': 'a', 'type': 'string'}
        ]
    }

    cache.insert(schema1, 1)
    cache.insert(schema2, 2)

    # test not only that you get the schemas by ID, but that it was
    # parsed by fastavro
    assert cache[1]['name'] == 'test-schemas.schema1'
    assert cache[2]['name'] == 'test-schemas.schema2'

    # Get schemas by the schema itself
    assert cache[schema1] == 1
    assert cache[schema2] == 2

    # Schemas don't exist
    with pytest.raises(KeyError):
        cache[0]
    with pytest.raises(KeyError):
        schemaX = {
            "type": "unknown"
        }
        cache[schemaX]


def test_subject_cache():
    cache = SubjectCache(SchemaCache())

    schema1 = {
        'type': 'record',
        'name': 'schema1',
        'namespace': 'test-schemas',
        'fields': [
            {'name': 'a', 'type': 'int'}
        ]
    }

    schema2 = {
        'type': 'record',
        'name': 'schema2',
        'namespace': 'test-schemas',
        'fields': [
            {'name': 'a', 'type': 'string'}
        ]
    }

    schema3 = {
        'type': 'record',
        'name': 'schema3',
        'namespace': 'test-schemas',
        'fields': [
            {'name': 'a', 'type': 'boolean'}
        ]
    }

    # pre-cache schema1 and schema2
    cache.schema_cache.insert(schema1, 1)
    cache.schema_cache.insert(schema2, 2)

    # Test inserting subject info for a pre-cached schema
    cache.insert('schema1', 25, schema_id=1)
    assert ('schema1', 25) in cache
    assert cache.get_id('schema1', 25) == 1
    assert cache.get_schema('schema1', 25)['name'] == 'test-schemas.schema1'

    cache.insert('schema2', 32, schema=schema2)
    assert ('schema2', 32) in cache
    assert cache.get_id('schema2', 32) == 2
    assert cache.get_schema('schema2', 32)['name'] == 'test-schemas.schema2'

    # Test inserting a subject that does not have a pre-cached schema
    with pytest.raises(ValueError):
        cache.insert('schema3', 13)
    with pytest.raises(ValueError):
        cache.insert('schema3', 13, schema_id=3)
    with pytest.raises(ValueError):
        cache.insert('schema3', 13, schema=schema3)
    cache.insert('schema3', 13, schema=schema3, schema_id=3)
    assert ('schema3', 13) in cache
    assert cache.get_id('schema3', 13) == 3
    assert cache.get_schema('schema3', 13)['name'] == 'test-schemas.schema3'

    # Test getting a non-existent subject or version
    with pytest.raises(ValueError):
        cache.get_id('schema3', 25)
    with pytest.raises(ValueError):
        cache.get_schema('schema18', 25)

    # Test caching 'latest'
    with pytest.raises(TypeError):
        cache.insert('mysubject', 'latest', schema_id=42)
