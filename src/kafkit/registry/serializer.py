"""Avro serialization and deserialization helpers that integrate with the
Confluent Schema Registry.
"""

from __future__ import annotations

import struct
from io import BytesIO
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

import fastavro

if TYPE_CHECKING:
    from kafkit.registry.sansio import RegistryApi

__all__ = [
    "Serializer",
    "PolySerializer",
    "Deserializer",
]


class Serializer:
    """An Avro message serializer that writes in the Confluent Wire Format.

    Use the `Serializer.register` class method to create a Serializer instance.

    Parameters
    ----------
    schema : `dict`
        An Avro schema.
    schema_id : `int`
        The ID of ``schema`` in a Schema Registry.

    Notes
    -----
    A `Serializer` instance is dedicated to serializing messages of a single
    schema. The serializer is a callable. Send the message to the serializer
    to encode it.

    This is an example using the MockRegistryApi client. Real-world
    applications would use the `kafkit.registry.aiohttp.RegistryApi` instead.

    >>> from kafkit.registry.sansio import MockRegistryApi
    >>> client = MockRegistryApi()

    For demonstration purposes, assume the schema is already cached:

    >>> schema = {
    ...    'type': 'record',
    ...    'name': 'schema1',
    ...    'namespace': 'test-schemas',
    ...    'fields': [
    ...        {'name': 'a', 'type': 'int'},
    ...        {'name': 'b', 'type': 'string'}
    ...    ]
    ... }
    >>> client.schemas.insert(schema, 1)
    >>> serializer = await Serializer.register(
    ...     registry=client,
    ...     schema=schema)

    Serialize messages:

    >>> data = serializer({'a': 42, 'b': 'Hello world!'})

    This serializer works well as ``key_serializer`` or ``value_serializer``
    parameters to the `aiokafka.AIOKafkaProducer`. See
    https://aiokafka.readthedocs.io/en/stable/examples/serialize_and_compress.html
    """

    def __init__(self, *, schema: Dict[str, Any], schema_id: int) -> None:
        self.schema = fastavro.parse_schema(schema)
        self.id = schema_id

    @classmethod
    async def register(
        cls,
        *,
        registry: RegistryApi,
        schema: Dict[str, Any],
        subject: Optional[str] = None,
    ) -> Serializer:
        """Create a serializer ensuring that the schema is registered with the
        schema registry.

        Parameters
        ----------
        registry : `kafkit.registry.sansio.RegistryApi`
            A registry client.
        schema : `dict`
            An Avro schema.
        subject : `str`, optional
            The name of the Schema Registry subject that the schema is
            registered under. If not provided, the schema is automatically
            set from the fully-qualified name of the schema (the ``'name'``
            field of the schema's record type). See
            `kafkit.registry.sansio.RegistryApi.register_schema` for details.

        Returns
        -------
        serializer : `Serializer`
            A serializer instance.

        Notes
        -----
        It's safe to call this method even if you know that the schema has been
        registered before. This process is necessary to get the schema's ID,
        and won't create a new schema if an identical schema is already
        registered.
        """
        id_ = await registry.register_schema(schema, subject=subject)
        return cls(schema=schema, schema_id=id_)

    def __call__(self, data: Any) -> bytes:
        """Serialize a dataset in the Confluent Schema Registry Wire format,
        which is an Avro-encoded message with a schema-identifying prefix.

        Parameters
        ----------
        data : object
            An Avro-serializable object. The object must conform to the schema.

        Returns
        -------
        message : `bytes`
            Message in the Confluent Schema Registry wire format.
        """
        return _make_message(data=data, schema_id=self.id, schema=self.schema)


class PolySerializer:
    """An Avro message serializer that can write messages for multiple schemas
    in the Confluent Wire Format.

    Parameters
    ----------
    registry : `kafkit.registry.sansio.RegistryApi`
        A registry client.
    """

    def __init__(self, *, registry: RegistryApi) -> None:
        self._registry = registry

    async def serialize(
        self,
        data: Any,
        schema: Optional[Dict[str, Any]] = None,
        schema_id: Optional[int] = None,
        subject: Optional[str] = None,
    ) -> bytes:
        """Serialize data given a schema.

        Parameters
        ----------
        data
            An Avro-serializable object. The object must conform to the schema.
        schema_id : `int`, optional
            The ID of the schema in the Schema Registry. Even if a ``schema``
            is also provided, this method will always obtain the schema through
            the registry client. If this parameter isn't set then the
            ``schema`` parmeter is used.
        schema : `dict`, optional
            An Avro schema. This parameter is ignored if the ``schema_id``
            parameter is set. If necessary (because the schema isn't found in
            the registry) this schema is registered with
            the schema registry. By default, the schema is registered under a
            subject named after the fully-qualified name of the schema. This
            default can be overriden by setting the ``subject`` parameter.
        subject : `str`, optional
            If the ``schema`` parameter is set **and** that schema needs to
            be newly registered with the schema registry, the schema is
            registered under this subject name. This is optional; by default
            the schema is registered under a subject named after the fully
            qualified name of the schema.

        Returns
        -------
        message : `bytes`
            Message in the Confluent Schema Registry `wire format
            <https://docs.confluent.io/current/schema-registry/docs/serializer-formatter.html#wire-format>`_.
        """
        if schema_id is not None:
            schema = await self._registry.get_schema_by_id(schema_id)
        elif schema is not None:
            schema_id = await self._registry.register_schema(
                schema=schema, subject=subject
            )
        if schema is None or schema_id is None:
            raise RuntimeError("Pass either a schema or schema_id parameter.")
        return _make_message(data=data, schema_id=schema_id, schema=schema)


def _make_message(
    *, schema_id: int, schema: Dict[str, Any], data: Any
) -> bytes:
    """Make a message in the Confluent Wire Format."""
    message_fh = BytesIO()
    # Write the Confluent Wire Format prefix.
    message_fh.write(pack_wire_format_prefix(schema_id))
    # Write the Avro-encoded message
    fastavro.schemaless_writer(message_fh, schema, data)
    message_fh.seek(0)
    return message_fh.read()


class Deserializer:
    """An Avro message deserializer that understands the Confluent Wire Format
    and obtains schemas on-demand from a Confluent Schema Registry.

    Parameters
    ----------
    registry : `kafkit.registry.sansio.RegistryApi`
        A registry client.

    Notes
    -----
    The Deserializer works exclusively with Avro-encoded messages in the
    `Confluent Wire Format
    <https://docs.confluent.io/current/schema-registry/docs/serializer-formatter.html#wire-format>`_.
    This means that schemas for messages must be
    available from a `Confluent Schema Registry
    <https://docs.confluent.io/current/schema-registry/docs/index.html>`_.

    When an encoded message is deserialized in the `~Deserializer.deserialize`
    method, it does the following steps:

    1. Unpacks the wire format prefix to discover the ID of the
       message's schema in the schema registry.
    2. Obtains the schema from the `~kafkit.registry.sansio.RegistryApi`.
       Schemas are cached, so this is a fast operation.
    3. Decodes the message using
       `fastavro.schemaless_reader <fastavro._read_py.schemaless_reader>`.

    **Why not implement a __call__ method?**

    The `Serializer` implements a ``__call__`` method so that it can be used
    as a key or value serializer by the aiokafka producer. This Deserializer
    doesn't do that because `Deserializer.deserialize` is a coroutine
    (internally it works with the asynchronous
    `~kafkit.registry.sansio.RegistryApi`) and magic methods can't be
    coroutines. It's not the end of the world, though, just call
    `~Deserializer.deserialize` manually on by bytes obtained by the consumer.
    """

    def __init__(self, *, registry: RegistryApi) -> None:
        self._registry = registry

    async def deserialize(
        self, data: bytes, include_schema: bool = False
    ) -> Dict[str, Any]:
        """Deserialize a message.

        Parameters
        ----------
        data : `bytes`
            The encoded message, usually obtained directly from a Kafka
            consumer. The message must be in the Confluent Wire Format.
        include_schema : `bool`, optional
            If `True`, the schema itself is included in the returned value.
            This is useful if your application operates on many different
            types of messages, and needs a convenient way to introspect
            a message's type.

        Returns
        -------
        message_info : `dict`
            The deserialized message is wrapped in a dictionary to include
            metadata. The keys are:

            ``'id'``
                The ID of the schema (an `int`) in the Schema Registry. This
                uniquely identifies the message's schema.
            ``'message'``
                The message itself, as a decoded Python object.
            ``'schema'``
                The schema, as a Python object. This key is only included
                when ``include_schema`` is `True`.
        """
        schema_id, message_data = unpack_wire_format_data(data)
        schema = await self._registry.get_schema_by_id(schema_id)

        message_fh = BytesIO(message_data)
        message_fh.seek(0)
        message = fastavro.schemaless_reader(message_fh, schema)
        result = {"id": schema_id, "message": message}
        if include_schema:
            result["schema"] = schema
        return result


def pack_wire_format_prefix(schema_id: int) -> bytes:
    """Create the bytes prefix for a Confluent Wire Format message.

    Parameters
    ----------
    schema_id : `int`
        The ID of a schema in the Confluent Schema Registry.

    Returns
    -------
    prefix : `bytes`
        The wire format prefix.

    Notes
    -----
    This function assumes that the "magic byte" is always ``0``. See the
    `Confluent documentation
    <https://docs.confluent.io/current/schema-registry/docs/serializer-formatter.html#wire-format>`_
    for details about the wire format.
    """
    # 0 is the magic byte.
    return struct.pack(">bI", 0, schema_id)


def unpack_wire_format_data(data: bytes) -> Tuple[int, bytes]:
    """Unpackage the bytes of a Confluent Wire Format message to get the
    schema ID and message body.

    Parameters
    ----------
    data : `bytes`
        The Confluent Wire Format message.

    Returns
    -------
    schema_id : `int`
        The ID of the message's schema in the Schema Registry.
    message_body : `bytes`
        The Avro-encoded body of the message.

    Notes
    -----
    This function assumes that the "magic byte" is always ``0``. See the
    `Confluent documentation
    <https://docs.confluent.io/current/schema-registry/docs/serializer-formatter.html#wire-format>`_
    for details about the wire format.
    """
    if len(data) < 5:
        raise RuntimeError(
            f"Data is too short, length is {len(data)} " "bytes. Must be >= 5."
        )
    prefix = data[:5]

    # Interpret the Confluent Wire Format prefix
    _, schema_id = struct.unpack(">bI", prefix)
    return schema_id, data[5:]
