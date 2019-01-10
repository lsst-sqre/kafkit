"""Tests for the kafkit.registry.serializer module.
"""

import pytest

from kafkit.registry.serializer import (
    pack_wire_format_prefix, unpack_wire_format_data)


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
