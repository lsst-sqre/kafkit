"""Utilities related to Avro schemas and the Confluent Schema Registry."""

from __future__ import annotations

from typing import Any, Mapping

__all__ = ["get_avro_fqn"]


def get_avro_fqn(schema: Mapping[str, Any]) -> str:
    """Get the fully-qualified name of an Avro schema.

    Parameters
    ----------
    schema
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
