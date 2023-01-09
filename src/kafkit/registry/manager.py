"""Combined local and registry-based schema management."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional

from kafkit.registry.errors import RegistryBadRequestError
from kafkit.registry.sansio import CompatibilityType
from kafkit.registry.serializer import PolySerializer

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
        self._logger = logging.getLogger(__name__)
        self._root = root
        self._registry = registry
        self._suffix = suffix

        self._serializer = PolySerializer(registry=self._registry)
        self.schemas: Dict[str, Any] = {}

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

            fqn = self._get_fqn(schema)
            self.schemas[fqn] = schema

    @staticmethod
    def _get_fqn(schema: Mapping[str, Any]) -> str:
        """Get the fully-qualified name of an Avro schema.

        Parameters
        ----------
        schema : `dict`
            The Avro schema.

        Returns
        -------
        str
            The fully-qualified name.

        Notes
        -----
        The decision sequence is:

        - If the ``name`` field includes a period (``.``), the ``name`` field
          is treated as a fully-qualified name.
        - Otherwise, if the schema includes a ``namespace`` field, the
          fully-qualified name is ``{{namespace}}.{{name}}``.
        - Otherwise, the ``name`` is treated as the fully-qualified name.
        """
        if "." not in schema["name"] and "namespace" in schema:
            fqn = ".".join((schema["namespace"], schema["name"]))
        else:
            fqn = schema["name"]
        assert isinstance(fqn, str)
        return fqn

    async def register_schemas(
        self, *, compatibility: Optional[str] = None
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
        if isinstance(compatibility, str):
            try:
                CompatibilityType[compatibility]
            except KeyError:
                raise ValueError(
                    f"Compatibility setting {compatibility!r} is not in the "
                    f"allowed set: {[v.value for v in CompatibilityType]}"
                )
        for subject_name, schema in self.schemas.items():
            await self._register_schema(
                subject_name=subject_name,
                schema=schema,
                desired_compatibility=compatibility,
            )

    async def _register_schema(
        self,
        *,
        subject_name: str,
        schema: Dict[str, Any],
        desired_compatibility: Optional[str],
    ) -> int:
        """Register a schema with the Schema Registry

        Parameters
        ----------
        subject_name : `str`
            The name of a subject in the Confluent Schema Registry, which
            may already exist or not.
        desired_compatibility : `str`
            A subject compatibility setting. See docs for `register_schemas`
            for possible values.

        Returns
        -------
        int
            Unique ID of the schema in the Schema in the Schema Registry.

        Notes
        -----
        This method can be safely run multiple times with the same schema; in
        each instance the same schema ID will be returned.
        """
        schema_id = await self._registry.register_schema(
            schema, subject=subject_name
        )

        if desired_compatibility is not None:
            await self._set_subject_compatibility(
                subject_name=subject_name, compatibility=desired_compatibility
            )
        return schema_id

    async def _set_subject_compatibility(
        self, *, subject_name: str, compatibility: str
    ) -> None:
        """Set the compatibility for a Schema Registry subject.

        Parameters
        ----------
        subject_name : `str`
            The name of a subject that exists in the Confluent Schema Registry.
        compatibility : `str`
            A subject compatibility setting. See docs for `register_schemas`
            for possible values.
        """
        try:
            subject_config = await self._registry.get(
                "/config{/subject}", url_vars={"subject": subject_name}
            )
        except RegistryBadRequestError:
            self._logger.info(
                "No existing configuration for this subject: %s", subject_name
            )
            # Create a mock config that forces a reset
            subject_config = {"compatibilityLevel": None}

        self._logger.debug(
            "Current config subject=%s config=%s", subject_name, subject_config
        )

        if subject_config["compatibilityLevel"] != compatibility:
            await self._registry.put(
                "/config{/subject}",
                url_vars={"subject": subject_name},
                data={"compatibility": compatibility},
            )
            self._logger.info(
                "Reset subject compatibility level. "
                "subject=%s compatibility=%s",
                subject_name,
                compatibility,
            )
        else:
            self._logger.debug(
                "Existing subject compatibility level is good. "
                "subject=%s compatibility=%s",
                subject_name,
                compatibility,
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

        encoded_message = await self._serializer.serialize(
            data, schema=schema, subject=name
        )

        return encoded_message
