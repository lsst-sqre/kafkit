"""Tests for the kafkit.registry.serializer module.
"""

import json
from io import BytesIO

import fastavro
import pytest

from kafkit.registry.serializer import (
    pack_wire_format_prefix, unpack_wire_format_data, Serializer, Deserializer)
from kafkit.registry.sansio import MockRegistryApi


def test_wire_format():
    """Test packing and unpacking the wire format prefix.
    """
    schema_id = 123
    body = b'hello'

    message = pack_wire_format_prefix(schema_id) + body
    print(len(message))

    unpacked_id, unpacked_body = unpack_wire_format_data(message)

    assert schema_id == unpacked_id
    assert body == unpacked_body


def test_unpacking_short_message():
    with pytest.raises(RuntimeError):
        unpack_wire_format_data(b'')


@pytest.mark.asyncio
async def test_serializer():
    """Test the Serializer class.
    """
    client = MockRegistryApi(
        body=json.dumps({'id': 1}).encode('utf-8')
    )
    schema1 = {
        'type': 'record',
        'name': 'schema1',
        'namespace': 'test-schemas',
        'fields': [
            {'name': 'a', 'type': 'int'},
            {'name': 'b', 'type': 'string'}
        ]
    }
    serializer = await Serializer.register(registry=client, schema=schema1)
    assert serializer.id == 1

    message = {'a': 1, 'b': 'helloworld'}
    data = serializer(message)
    assert isinstance(data, bytes)

    # Check that the message can be deserialized
    # First, the wire format prefix
    unpacked_id, unpacked_body = unpack_wire_format_data(data)
    assert unpacked_id == serializer.id
    # Second, the message
    unpacked_schema = client.schemas[unpacked_id]
    message_fh = BytesIO(unpacked_body)
    message_fh.seek(0)
    unpacked_message = fastavro.schemaless_reader(message_fh, unpacked_schema)
    assert unpacked_message == message


@pytest.mark.asyncio
async def test_deserializer():
    """Test the Deserializer class.
    """
    # First schema
    schema1 = {
        'type': 'record',
        'name': 'schema1',
        'namespace': 'test-schemas',
        'fields': [
            {'name': 'a', 'type': 'int'},
            {'name': 'b', 'type': 'string'}
        ]
    }
    schema1_id = 1
    # Second schema
    schema2 = {
        'type': 'record',
        'name': 'schema2',
        'namespace': 'test-schemas',
        'fields': [
            {'name': 'c', 'type': 'int'},
            {'name': 'd', 'type': 'string'}
        ]
    }
    schema2_id = 2
    # insert the schemas directly into the cache
    client = MockRegistryApi()
    client.schemas.insert(schema1, schema1_id)
    client.schemas.insert(schema2, schema2_id)

    # Serialize a couple messages, using the serializer. Since the schema
    # is cached it won't need a mocked response body.
    serializer1 = await Serializer.register(registry=client, schema=schema1)
    serializer2 = await Serializer.register(registry=client, schema=schema2)

    message_1 = {'a': 42, 'b': 'hello'}
    data_1 = serializer1(message_1)

    message_2 = {'c': 13, 'd': 'bonjour'}
    data_2 = serializer2(message_2)

    # Deserialization
    deserializer = Deserializer(registry=client)

    response_1 = await deserializer.deserialize(data_1)
    assert response_1['id'] == schema1_id
    assert response_1['message'] == message_1
    assert 'schema' not in response_1

    response_2 = await deserializer.deserialize(data_2, include_schema=True)
    assert response_2['id'] == schema2_id
    assert response_2['message'] == message_2
    assert 'schema' in response_2
    assert response_2['schema']['name'] == 'test-schemas.schema2'
