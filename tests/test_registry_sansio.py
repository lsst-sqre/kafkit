"""Tests for the kafkit.registry.sansio module.
"""

import json

import pytest

from kafkit.registry.sansio import (make_headers, decipher_response,
                                    RegistryApi)
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
    client = MockRegistryApi(host='http://registry:8081')
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
        host='http://registry:8081',
        body=json.dumps(expected_data).encode('utf-8'))
    response = await client.get('/subjects{/subject}/versions',
                                url_vars={'subject': 'helloworld'})

    assert response == expected_data


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
