"""Manage schemas as avro files based on the record name subject name
strategy.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from kafkit.registry.serializer import PolySerializer

from ..utils import get_avro_fqn

if TYPE_CHECKING:
    from kafkit.registry.sansio import RegistryApi

__all__ = ["RecordNameSchemaManager"]


class RecordNameSchemaManager:
    """A manager for schemas embedded in the application itself in conjunction
    with a Confluent Schema Registry, for the case of a record name subject
    name strategy.

    Parameters
    ----------
    root : `pathlib.Path`
        The root directory containing schemas. Schemas can be located within
        this directory, or in a child directory. Schemas must have a
        ``.json`` filename extension.
    registry : `kafkit.registry.sansio.RegistryApi`
        The Registry API client instance. For an application build with
        ``aiohttp``, use the `kafkit.registry.aiohttp.RegistryApi` type.
    suffix : `str`, optional
        A suffix that is added to the schema name (and thus subject name), for
        example ``_dev1``.

        The suffix creates an alternate subjects in the Schema Registry so
        schemas registered during testing and staging don't affect the
        compatibility continuity of a production subject.

        For production, it's best to not set a suffix.

    Notes
    -----
    The ``RecordNameSchemaManager`` helps you manage Avro serialization in
    your application. This class implements an opinionated workflow that
    combines lower-level Kafkit components such as the
    `~kafkit.registry.sansio.RegistryApi`, serializers and deserializers.
    The key assumptions made by this manager are:

    - Your application holds a local copy of the schemas it serializes and
      deserializes data with. *This is useful so that your application can
      be developed and tested independently of the Schema Registry.*

    - Your application's schemas are located within a directory on the local
      filesystem with ``*.json`` extensions.

    - The Schema Registry subjects that your application uses have the same
      compatibility setting.

    - Subjects follow the **record name** naming strategy
      (``RecordNameStrategy``). That is, the subject name is the
      fully-qualified name of the Avro Schema.

      *Note that this is different from the default naming strategy,*
      ``TopicNameStrategy``, where subjects are named for the topic with
      ``-key`` or ``-value`` suffixes.

    For more information, see :doc:`/guide/recordnameschemamanager-howto` in
    the user guide.
    """

    def __init__(
        self, *, root: Path, registry: RegistryApi, suffix: str = ""
    ) -> None:
        self._registry = registry
        self._root = root
        self._suffix = suffix

        self._logger = logging.getLogger(__name__)

        self._serializer = PolySerializer(registry=self._registry)
        self.schemas: dict[str, Any] = {}

        self._load_schemas()

    def _load_schemas(self) -> None:
        """Load all schemas found in the root directory into the instance
        storage.
        """
        schema_paths = self._root.rglob("*.json")
        for schema_path in schema_paths:
            schema = json.loads(schema_path.read_text())

            if self._suffix:
                schema["name"] = f'{schema["name"]}{self._suffix}'

            fqn = get_avro_fqn(schema)
            self.schemas[fqn] = schema

    async def register_schemas(
        self, *, compatibility: str | None = None
    ) -> None:
        """Register all local schemas with the Confluent Schema Registry.

        Parameters
        ----------
        compatibility : `str`, optional
            The compatibility setting to apply to all subjects. Allowed values:

            - ``"BACKWARD"``
            - ``"BACKWARD_TRANSITIVE"``
            - ``"FORWARD"``
            - ``"FORWARD_TRANSITIVE"``
            - ``"FULL"``
            - ``"FULL_TRANSITIVE"``
            - ``"NONE"``
            - `None`

            If `None` (as opposed to ``"NONE"``), then no compatibility
            setting is set during schema registration:

            - If the subject doesn't already exist, it will inherit the
              Schema Registry's global compatibility setting.
            - If the subject already exists, it will continue to its
              existing compatibility setting.

            Learn more about schema compatibility in the `Confluent
            documentation
            <https://docs.confluent.io/current/schema-registry/avro.html>`__.
        """
        for subject_name, schema in self.schemas.items():
            await self._registry.register_schema(
                schema=schema,
                subject=subject_name,
                compatibility=compatibility,
            )

    async def serialize(self, *, data: Any, name: str) -> bytes:
        """Serialize data using the preregistered schema for a Schema Registry
        subject.

        Parameters
        ----------
        data : `dict`
            An Avro-serializable object.
        name : `str`
            The name of the schema to serialize the ``data`` with. This is also
            the name of the subject that the schema is associated with in the
            Confluent Schema Registry, following the record name strategy

            The specific schema that is used will be the one that was locally
            registered by the RecordNameSchemaManager.

        Returns
        -------
        `bytes`
            The Avro-encoded message in the Confluent Wire Format (which
            identifies the schema in the Schema Registry that was used to
            encode the message).

        Raises
        ------
        ValueError
            Raised if there isn't a locally-available schema with that
            record name / subject name.
        """
        if name not in self.schemas:
            raise ValueError(
                f"Schema named '{name}' not among the locally-registered "
                f"schemas. Available schemas are: {self.schemas.keys()}"
            )

        schema = self.schemas[name]

        try:
            return await self._serializer.serialize(
                data, schema=schema, subject=name
            )
        except ValueError as e:
            raise ValueError(
                f"Cannot serialize data with schema {name}"
            ) from e
