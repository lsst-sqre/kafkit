"""Tests for the kafkit.registry.sansio module."""

import json

import pytest

from kafkit.registry.errors import (
    RegistryBadRequestError,
    RegistryBrokenError,
    RegistryRedirectionError,
)
from kafkit.registry.sansio import (
    MockRegistryApi,
    SchemaCache,
    SubjectCache,
    decipher_response,
    make_headers,
)


def test_make_headers() -> None:
    """Test make_headers."""
    headers = make_headers()

    assert headers["accept"] == "application/vnd.schemaregistry.v1+json"


def test_decipher_response_200() -> None:
    """Test deciper_response with a 200 status code."""
    status = 200
    headers = {"content-type": "application/vnd.schemaregistry.v1+json"}
    data = [1, 2, 3]
    body = json.dumps(data).encode("utf-8")
    returned_data = decipher_response(status, headers, body)
    assert returned_data == data


def test_decipher_response_200_empty() -> None:
    """Test deciper_response with a 200 status code and an empty body."""
    status = 200
    headers = {"content-type": "application/vnd.schemaregistry.v1+json"}
    body = b""
    returned_data = decipher_response(status, headers, body)
    assert returned_data is None


def test_decipher_response_500_no_message() -> None:
    """Test deciper_response with a 500 status code and an empty body."""
    status = 500
    headers = {"content-type": "application/vnd.schemaregistry.v1+json"}
    body = b""
    with pytest.raises(RegistryBrokenError):
        decipher_response(status, headers, body)


def test_decipher_response_500_with_message() -> None:
    """Test deciper_response with a 500 status code and an error message."""
    status = 500
    headers = {"content-type": "application/vnd.schemaregistry.v1+json"}
    body = json.dumps({"error": 12345, "message": "I've got reasons"}).encode(
        "utf-8"
    )
    with pytest.raises(RegistryBrokenError):
        decipher_response(status, headers, body)


def test_decipher_response_401_no_message() -> None:
    """Test deciper_response with a 401 status code and an empty body."""
    status = 401
    headers = {"content-type": "application/vnd.schemaregistry.v1+json"}
    body = b""
    with pytest.raises(RegistryBadRequestError):
        decipher_response(status, headers, body)


def test_decipher_response_401_with_message() -> None:
    """Test deciper_response with a 401 status code and an error message."""
    status = 401
    headers = {"content-type": "application/vnd.schemaregistry.v1+json"}
    body = json.dumps({"error": 12345, "message": "I've got reasons"}).encode(
        "utf-8"
    )
    with pytest.raises(RegistryBadRequestError):
        decipher_response(status, headers, body)


def test_decipher_response_301_no_message() -> None:
    """Test deciper_response with a 301 status code and an empty body."""
    status = 301
    headers = {"content-type": "application/vnd.schemaregistry.v1+json"}
    body = b""
    with pytest.raises(RegistryRedirectionError):
        decipher_response(status, headers, body)


def test_decipher_response_301_with_message() -> None:
    """Test deciper_response with a 301 status code and a message."""
    status = 301
    headers = {"content-type": "application/vnd.schemaregistry.v1+json"}
    body = json.dumps({"error": 12345, "message": "I've got reasons"}).encode(
        "utf-8"
    )
    with pytest.raises(RegistryRedirectionError):
        decipher_response(status, headers, body)


@pytest.mark.asyncio
async def test_registryapi_get_empty() -> None:
    """Test client with a regular GET call with empty response."""
    client = MockRegistryApi(url="http://registry:8081")
    response = await client.get(
        "/subjects{/subject}/versions", url_vars={"subject": "helloworld"}
    )

    assert response is None
    # Check URL formatting
    assert client.url == "http://registry:8081/subjects/helloworld/versions"
    # Check headers
    assert client.headers["accept"] == make_headers()["accept"]
    assert client.headers["content-length"] == "0"
    assert client.method == "GET"


@pytest.mark.asyncio
async def test_registryapi_get_json() -> None:
    """Test client with a regular GET call with a JSON response."""
    expected_data = {"hello": "world"}
    client = MockRegistryApi(
        url="http://registry:8081",
        body=json.dumps(expected_data).encode("utf-8"),
    )
    response = await client.get(
        "/subjects{/subject}/versions", url_vars={"subject": "helloworld"}
    )

    assert response == expected_data
    assert client.method == "GET"


@pytest.mark.asyncio
async def test_registryapi_post() -> None:
    """Test RegistryApi.post()."""
    expected_data = {"key": "value"}
    client = MockRegistryApi(
        url="http://registry:8081",
        body=json.dumps(expected_data).encode("utf-8"),
    )
    response = await client.post("/a{/b}", url_vars={"b": "hello"}, data={})

    assert response == expected_data
    assert client.method == "POST"
    assert client.url == "http://registry:8081/a/hello"


@pytest.mark.asyncio
async def test_registryapi_patch() -> None:
    """Test RegistryApi.patch()."""
    expected_data = {"key": "value"}
    client = MockRegistryApi(
        url="http://registry:8081",
        body=json.dumps(expected_data).encode("utf-8"),
    )
    response = await client.patch("/a{/b}", url_vars={"b": "hello"}, data={})

    assert response == expected_data
    assert client.method == "PATCH"
    assert client.url == "http://registry:8081/a/hello"


@pytest.mark.asyncio
async def test_registryapi_put() -> None:
    """Test RegistryApi.put()."""
    expected_data = {"key": "value"}
    client = MockRegistryApi(
        url="http://registry:8081",
        body=json.dumps(expected_data).encode("utf-8"),
    )
    response = await client.put("/a{/b}", url_vars={"b": "hello"}, data={})

    assert response == expected_data
    assert client.method == "PUT"
    assert client.url == "http://registry:8081/a/hello"


@pytest.mark.asyncio
async def test_registryapi_delete() -> None:
    """Test RegistryApi.put()."""
    client = MockRegistryApi(url="http://registry:8081")
    await client.delete("/a{/b}", url_vars={"b": "hello"})

    assert client.method == "DELETE"
    assert client.url == "http://registry:8081/a/hello"


@pytest.mark.asyncio
async def test_register_schema() -> None:
    """Test the RegistryApi.register_schema() method."""
    input_schema = {
        "type": "record",
        "name": "schema1",
        "namespace": "test-schemas",
        "fields": [{"name": "a", "type": "int"}],
    }

    # Body that we expect the registry API to return given the request.
    expected_body = json.dumps({"id": 1}).encode("utf-8")

    client = MockRegistryApi(url="http://registry:8081", body=expected_body)
    schema_id = await client.register_schema(input_schema)
    assert schema_id == 1

    # Test details of the request itself
    assert client.method == "POST"
    assert (
        client.url
        == "http://registry:8081/subjects/test-schemas.schema1/versions"
    )
    sent_json = json.loads(client.body)
    assert "schema" in sent_json
    sent_schema = json.loads(sent_json["schema"])
    assert "__fastavro_parsed" not in sent_schema
    assert "__named_schemas" not in sent_schema
    assert sent_schema["name"] == "test-schemas.schema1"

    # Check that the schema is in the cache and is parsed
    # Value of type "Union[int, Dict[str, Any]]" is not indexable
    cached_schema = client.schema_cache[1]
    assert cached_schema["name"] == "test-schemas.schema1"
    assert "__fastavro_parsed" in cached_schema

    # Make a second call to get the schema out
    new_schema_id = await client.register_schema(input_schema)
    assert new_schema_id == schema_id


@pytest.mark.asyncio
async def test_get_schema_by_id() -> None:
    """Test the RegistryApi.get_schema_by_id method."""
    # Body that we expect the registry API to return given the request.
    input_schema = json.dumps(
        {
            "type": "record",
            "name": "schema1",
            "namespace": "test-schemas",
            "fields": [{"name": "a", "type": "int"}],
        }
    )
    expected_body = json.dumps({"schema": input_schema}).encode("utf-8")

    client = MockRegistryApi(body=expected_body)

    schema = await client.get_schema_by_id(1)

    # Check that the schema was parsed
    assert schema["name"] == "test-schemas.schema1"
    cached_schema = client.schema_cache[1]
    assert "__fastavro_parsed" in cached_schema

    # Check that the schem was cached
    assert cached_schema["name"] == "test-schemas.schema1"

    # Check the request
    assert client.url == "http://registry:8081/schemas/ids/1"
    assert client.method == "GET"


@pytest.mark.asyncio
async def test_get_schema_by_subject() -> None:
    """Test the RegistryApi.get_schema_by_subject method."""
    # Body that we expect the registry API to return given the request.
    expected_body = {
        "schema": json.dumps(
            {
                "type": "record",
                "name": "schema1",
                "namespace": "test-schemas",
                "fields": [{"name": "a", "type": "int"}],
            }
        ),
        "subject": "schema1",
        "version": 1,
        "id": 2,
    }

    client = MockRegistryApi(body=json.dumps(expected_body).encode("utf-8"))

    result = await client.get_schema_by_subject("schema1")

    # Check the request
    assert (
        client.url == "http://registry:8081/subjects/schema1/versions/latest"
    )
    assert client.method == "GET"

    # Check that the schema was parsed
    assert result["schema"]["name"] == "test-schemas.schema1"
    assert "__fastavro_parsed" in result["schema"]
    # Check other content of the result
    assert result["version"] == 1
    assert result["id"] == 2
    assert result["subject"] == "schema1"

    # Check that the schema got cached
    assert ("schema1", 1) in client.subject_cache

    # Get that schema, purely using the cache
    result2 = await client.get_schema_by_subject("schema1", version=1)
    assert result == result2


def test_schema_cache() -> None:
    """Test the SchemaCache."""
    cache = SchemaCache()

    schema1 = {
        "type": "record",
        "name": "schema1",
        "namespace": "test-schemas",
        "fields": [{"name": "a", "type": "int"}],
    }

    schema2 = {
        "type": "record",
        "name": "schema2",
        "namespace": "test-schemas",
        "fields": [{"name": "a", "type": "string"}],
    }

    cache.insert(schema1, 1)
    cache.insert(schema2, 2)

    # test not only that you get the schemas by ID, but that it was
    # parsed by fastavro
    cached_schema1 = cache[1]
    cached_schema2 = cache[2]
    assert cached_schema1["name"] == "test-schemas.schema1"
    assert cached_schema2["name"] == "test-schemas.schema2"

    # Get schemas by the schema itself
    assert cache[schema1] == 1
    assert cache[schema2] == 2

    # Schemas don't exist
    with pytest.raises(KeyError):
        cache[0]
    with pytest.raises(KeyError):
        schemaX = {"type": "unknown"}
        cache[schemaX]


def test_subject_cache() -> None:
    """Test the SubjectCache."""
    cache = SubjectCache(SchemaCache())

    schema1 = {
        "type": "record",
        "name": "schema1",
        "namespace": "test-schemas",
        "fields": [{"name": "a", "type": "int"}],
    }

    schema2 = {
        "type": "record",
        "name": "schema2",
        "namespace": "test-schemas",
        "fields": [{"name": "a", "type": "string"}],
    }

    schema3 = {
        "type": "record",
        "name": "schema3",
        "namespace": "test-schemas",
        "fields": [{"name": "a", "type": "boolean"}],
    }

    # pre-cache schema1 and schema2
    cache.schema_cache.insert(schema1, 1)
    cache.schema_cache.insert(schema2, 2)

    # Test inserting subject info for a pre-cached schema
    cache.insert("schema1", 25, schema_id=1)
    assert ("schema1", 25) in cache
    assert cache.get_id("schema1", 25) == 1
    assert cache.get_schema("schema1", 25)["name"] == "test-schemas.schema1"
    schema1_info = cache.get("schema1", 25)
    assert schema1_info["subject"] == "schema1"
    assert schema1_info["version"] == 25
    assert schema1_info["id"] == 1
    assert schema1_info["schema"]["name"] == "test-schemas.schema1"

    cache.insert("schema2", 32, schema=schema2)
    assert ("schema2", 32) in cache
    assert cache.get_id("schema2", 32) == 2
    assert cache.get_schema("schema2", 32)["name"] == "test-schemas.schema2"

    # Test inserting a subject that does not have a pre-cached schema
    with pytest.raises(ValueError):
        cache.insert("schema3", 13)
    with pytest.raises(ValueError):
        cache.insert("schema3", 13, schema_id=3)
    with pytest.raises(ValueError):
        cache.insert("schema3", 13, schema=schema3)
    cache.insert("schema3", 13, schema=schema3, schema_id=3)
    assert ("schema3", 13) in cache
    assert cache.get_id("schema3", 13) == 3
    assert cache.get_schema("schema3", 13)["name"] == "test-schemas.schema3"

    # Test getting a non-existent subject or version
    with pytest.raises(ValueError):
        cache.get_id("schema3", 25)
    with pytest.raises(ValueError):
        cache.get_schema("schema18", 25)
    with pytest.raises(ValueError):
        cache.get("schema18", 15)

    # Test caching 'latest'
    with pytest.raises(TypeError):
        cache.insert("mysubject", "latest", schema_id=42)  # type: ignore
