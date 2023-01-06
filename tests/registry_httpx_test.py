"""Tests for the kafkit.registry.httpx module."""

from __future__ import annotations

import os

import pytest
from httpx import AsyncClient

from kafkit.registry.httpx import RegistryApi

schema_a = {
    "type": "record",
    "name": "a",
    "namespace": "kafkit.httpx",
    "fields": [
        {"name": "field1", "type": "int"},
        {"name": "field2", "type": "string"},
    ],
}


@pytest.mark.docker
@pytest.mark.skipif(
    os.getenv("SCHEMA_REGISTRY_URL") is None,
    reason="SCHEMA_REGISTRY_URL env var must be configured",
)
@pytest.mark.asyncio
async def test_httpxapi() -> None:
    """Test that the httpx RegistryApi can connect to the Schema Registry."""
    registry_url = os.getenv("SCHEMA_REGISTRY_URL")
    assert registry_url

    async with AsyncClient() as http_client:
        registry = RegistryApi(http_client=http_client, url=registry_url)
        schema_a_id = await registry.register_schema(schema_a)
        assert isinstance(schema_a_id, int)
