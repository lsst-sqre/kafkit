"""Tests for the PydanticSchemaManager class."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from enum import Enum

import pytest
from dataclasses_avroschema.avrodantic import AvroBaseModel
from httpx import AsyncClient
from pydantic import Field

from kafkit.registry import UnmanagedSchemaError
from kafkit.registry.httpx import RegistryApi
from kafkit.registry.manager import PydanticSchemaManager


def current_datetime() -> datetime:
    """Return the current datetime."""
    return datetime.now(tz=timezone.utc)


class SlackMessageType(Enum):
    """The type of Slack message."""

    app_mention = "app_mention"
    message = "message"


class SlackChannelType(Enum):
    """The type of Slack channel."""

    channel = "channel"  # public channel
    group = "group"  # private channel
    im = "im"  # direct message
    mpim = "mpim"  # multi-persion direct message


class SquarebotMessage(AvroBaseModel):
    """Model for a Slack message produced by Squarebot."""

    type: SlackMessageType = Field(description="The Slack message type.")

    channel: str = Field(
        description=(
            "ID of the channel where the message was sent "
            "(e.g., C0LAN2Q65)."
        )
    )

    channel_type: SlackChannelType = Field(
        description="The type of channel (public, direct im, etc..)"
    )

    user: str | None = Field(
        description="The ID of the user that sent the message (eg U061F7AUR)."
    )

    text: str = Field(description="Content of the message.")

    ts: str = Field(description="Timestamp of the message.")

    event_ts: str = Field(description="When the event was dispatched.")

    class Meta:
        """Metadata for the model."""

        namespace = "squarebot"
        schema_name = "message"


class SquarebotHeartbeat(AvroBaseModel):
    """Model for a Squarebot heartbeat message."""

    timestamp: datetime = Field(
        description="The timestamp of the heartbeat.",
        default_factory=current_datetime,
    )

    class Meta:
        """Metadata for the model."""

        namespace = "squarebot"
        schema_name = "heartbeat"


AVRO_SCHEMA = {
    "type": "record",
    "name": "schema1",
    "namespace": "test-schemas",
    "fields": [
        {"name": "a", "type": "int"},
        {"name": "b", "type": "string"},
    ],
}


@pytest.mark.docker
@pytest.mark.skipif(
    os.getenv("SCHEMA_REGISTRY_URL") is None,
    reason="SCHEMA_REGISTRY_URL env var must be configured",
)
@pytest.mark.asyncio
async def test_pydantic_schema_manager() -> None:
    """Test that the Pydantic Schema Manager can register a schema based on
    a Pydantic model, and serialize/deserialize Pydantic models.
    """
    registry_url = os.getenv("SCHEMA_REGISTRY_URL")
    assert registry_url

    async with AsyncClient() as http_client:
        registry = RegistryApi(http_client=http_client, url=registry_url)
        manager = PydanticSchemaManager(registry=registry)

        # Register the schema
        await manager.register_model(SquarebotMessage, compatibility="FORWARD")

        # Check the cache
        assert manager._models.get("squarebot.message") is not None
        assert manager._models["squarebot.message"].model == SquarebotMessage

        input_message = SquarebotMessage.fake()

        # Serialize the message
        serialized_data = await manager.serialize(input_message)

        # Deserialize the message
        output_message = await manager.deserialize(serialized_data)

        # Check that the deserialized message is the same as the input
        assert isinstance(output_message, SquarebotMessage)
        assert output_message == input_message

        # Automatically register the heartbeat schema and send a heartbeat
        _ = await manager.serialize(SquarebotHeartbeat())

        # Register a non-Pydantic schema to demonstrate handling
        # unmanaged schemas
        schema_id = await manager._registry.register_schema(
            schema=AVRO_SCHEMA,
            subject="test-schemas.schema1",
        )
        unmanaged_message = await manager._serializer.serialize(
            {"a": 1, "b": "test"},
            schema_id=schema_id,
        )
        with pytest.raises(UnmanagedSchemaError):
            await manager.deserialize(unmanaged_message)


@pytest.mark.docker
@pytest.mark.skipif(
    os.getenv("SCHEMA_REGISTRY_URL") is None,
    reason="SCHEMA_REGISTRY_URL env var must be configured",
)
@pytest.mark.asyncio
async def test_pydantic_schema_manager_suffixed() -> None:
    """Test that the Pydantic Schema Manager can set a subject name suffix."""
    registry_url = os.getenv("SCHEMA_REGISTRY_URL")
    assert registry_url

    async with AsyncClient() as http_client:
        registry = RegistryApi(http_client=http_client, url=registry_url)
        manager = PydanticSchemaManager(registry=registry, suffix="_v1")

        # Register the schema
        await manager.register_model(SquarebotMessage, compatibility="FORWARD")

        # Check the cache
        assert manager._models.get("squarebot.message_v1") is not None
        assert (
            manager._models["squarebot.message_v1"].model == SquarebotMessage
        )

        input_message = SquarebotMessage.fake()

        # Serialize the message
        serialized_data = await manager.serialize(input_message)

        # Deserialize the message
        output_message = await manager.deserialize(serialized_data)

        # Check that the deserialized message is the same as the input
        assert isinstance(output_message, SquarebotMessage)
        assert output_message == input_message

        # Automatically register the heartbeat schema and send a heartbeat
        _ = await manager.serialize(SquarebotHeartbeat())

        # Register a non-Pydantic schema to demonstrate handling
        # unmanaged schemas
        schema_id = await manager._registry.register_schema(
            schema=AVRO_SCHEMA,
            subject="test-schemas.schema1",
        )
        unmanaged_message = await manager._serializer.serialize(
            {"a": 1, "b": "test"},
            schema_id=schema_id,
        )
        with pytest.raises(UnmanagedSchemaError):
            await manager.deserialize(unmanaged_message)
