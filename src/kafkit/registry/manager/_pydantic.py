"""Schema management that uses Pydantic models as the Python representation
of schemas.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterable, Optional, Type

from ..serializer import PolySerializer
from ..utils import get_avro_fqn

if TYPE_CHECKING:
    from dataclasses_avroschema.avrodantic import AvroBaseModel

    from kafkit.registry.sansio import RegistryApi

__all__ = ["PydanticSchemaManager"]


@dataclass
class CachedSchema:
    """A cached schema and model."""

    schema: dict[str, Any]
    """The Avro schema derived from the model."""

    model: Type[AvroBaseModel]
    """The Pydantic model."""


class PydanticSchemaManager:
    """A manager for schemas that are represented as Pydantic models in Python,
    and translated into Avro for the Confluent Schema Registry.

    Parameters
    ----------
    registry
        The Registry API client instance. For an application build with
        ``aiohttp``, use the `kafkit.registry.aiohttp.RegistryApi` type.
    suffix
        A suffix that is added to the schema name (and thus subject name), for
        example ``_dev1``.

        The suffix creates alternate subjects in the Schema Registry so
        schemas registered during testing and staging don't affect the
        compatibility continuity of a production subject.

        For production, it's best to not set a suffix.
    """

    def __init__(self, *, registry: RegistryApi, suffix: str = "") -> None:
        self._registry = registry
        self._suffix = suffix

        self._logger = logging.getLogger(__name__)

        self._serializer = PolySerializer(registry=self._registry)

        # A mapping of fully-qualified schema names to models.
        self._models: dict[str, CachedSchema] = {}

    async def register_models(
        self,
        models: Iterable[Type[AvroBaseModel]],
        compatibility: Optional[str] = None,
    ) -> None:
        """Register the models with the registry.

        Parameters
        ----------
        models
            The models to register.
        """
        for model in models:
            await self.register_model(model, compatibility=compatibility)

    async def register_model(
        self, model: Type[AvroBaseModel], compatibility: Optional[str] = None
    ) -> None:
        """Register the model with the registry.

        Parameters
        ----------
        model
            The model to register.
        """
        cached_schema = self._cache_model(model)
        schema_fqn = get_avro_fqn(cached_schema.schema)

        await self._registry.register_schema(
            schema=cached_schema.schema,
            subject=schema_fqn,
            compatibility=compatibility,
        )

    async def serialize(self, data: AvroBaseModel) -> bytes:
        """Serialize the data.

        Parameters
        ----------
        data
            The data to serialize.
        """
        schema_fqn = self._get_model_fqn(data)

        if schema_fqn in self._models:
            avro_schema = self._models[schema_fqn].schema
        else:
            cached_model = self._cache_model(data)
            avro_schema = cached_model.schema

        return await self._serializer.serialize(
            data, schema=avro_schema, subject=schema_fqn
        )

    def _cache_model(
        self, model: AvroBaseModel | Type[AvroBaseModel]
    ) -> CachedSchema:
        schema_fqn = self._get_model_fqn(model)
        avro_schema = model.avro_schema_to_python()

        self._models[schema_fqn] = CachedSchema(avro_schema, model)

        return self._models[schema_fqn]

    def _get_model_fqn(
        self, model: AvroBaseModel | Type[AvroBaseModel]
    ) -> str:
        try:
            name = model.Meta.schema_name
        except AttributeError:
            name = model.__class__.__name__

        try:
            namespace = model.Meta.namespace
        except AttributeError:
            namespace = None

        if namespace:
            name = f"{namespace}.{name}"

        if self._suffix:
            name += self._suffix

        return name
