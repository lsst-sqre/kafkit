"""Tests for the kafkit.registry.manager module."""

import os
from pathlib import Path

import pytest
from aiohttp import ClientSession

from kafkit.registry.aiohttp import RegistryApi
from kafkit.registry.manager import RecordNameSchemaManager

SCHEMA_ROOT = Path(__file__).parent / "data" / "record_name_schemas"
"""the root path of schemas for testing the RecordNameSchemaManager."""


@pytest.mark.docker
@pytest.mark.skipif(
    os.getenv("SCHEMA_REGISTRY_URL") is None,
    reason="SCHEMA_REGISTRY_URL env var must be configured",
)
@pytest.mark.asyncio
async def test_recordnameschemamanager() -> None:
    """Test the RecordNameSchemaManager using the docker-compose-based
    Confluent Platform service deployment.

    This test follows the expected usage for the manager.
    """
    registry_url = os.getenv("SCHEMA_REGISTRY_URL")
    assert registry_url

    async with ClientSession() as http_session:
        registry = RegistryApi(url=registry_url, session=http_session)
        manager = RecordNameSchemaManager(root=SCHEMA_ROOT, registry=registry)
        await manager.register_schemas(compatibility="FORWARD")

        topic_a_message = {"field1": 42, "field2": "hello"}
        data_a = await manager.serialize(data=topic_a_message, name="kafkit.a")
        assert isinstance(data_a, bytes)

        topic_b_message = {"fieldA": 42, "fieldB": "hello"}
        data_b = await manager.serialize(data=topic_b_message, name="kafkit.b")
        assert isinstance(data_b, bytes)

        # Sanity check that you can't serialize with the wrong schema!
        with pytest.raises(ValueError):
            await manager.serialize(data=topic_b_message, name="kafkit.a")
