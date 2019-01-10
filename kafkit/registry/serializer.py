"""Avro serialization and deserialization helpers that integrate with the
Confluent Schema Registry.
"""

import struct


def pack_wire_format_prefix(schema_id):
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
    This function assumes that the "magic byte" is always ``0``. See
    https://docs.confluent.io/current/schema-registry/docs/serializer-formatter.html#wire-format
    for details about the wire format.
    """
    # 0 is the magic byte.
    return struct.pack('>bI', 0, schema_id)


def unpack_wire_format_data(data):
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
    This function assumes that the "magic byte" is always ``0``. See
    https://docs.confluent.io/current/schema-registry/docs/serializer-formatter.html#wire-format
    for details about the wire format.
    """
    if len(data) < 5:
        raise RuntimeError(f'Data is too short, length is {len(data)} '
                           'bytes. Must be >= 5.')
    prefix = data[:5]

    # Interpret the Confluent Wire Format prefix
    _, schema_id = struct.unpack('>bI', prefix)
    return schema_id, data[5:]
