"""Tests for the PydanticSchemaManager class."""

from __future__ import annotations

import os
from enum import Enum
from typing import Optional

import pytest
from dataclasses_avroschema.avrodantic import AvroBaseModel
from httpx import AsyncClient
from pydantic import Field

from kafkit.registry.httpx import RegistryApi
from kafkit.registry.manager import PydanticSchemaManager


class SlackMessageType(str, Enum):
    """The type of Slack message."""

    app_mention = "app_mention"
    message = "message"


class SlackChannelType(str, Enum):
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

    user: Optional[str] = Field(
        description="The ID of the user that sent the message (eg U061F7AUR)."
    )

    text: str = Field(description="Content of the message.")

    ts: str = Field(description="Timestamp of the message.")

    event_ts: str = Field(description="When the event was dispatched.")

    class Meta:
        """Metadata for the model."""

        namespace = "squarebot"
        schema_name = "message"


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
