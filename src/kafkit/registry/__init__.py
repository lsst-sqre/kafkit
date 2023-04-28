"""Serialization and desierialization of Avro messsages using the Confluent
Schema Registry.
"""

from kafkit.registry.errors import (
    RegistryBadRequestError,
    RegistryBrokenError,
    RegistryError,
    RegistryHttpError,
    RegistryRedirectionError,
)
from kafkit.registry.serializer import (
    Deserializer,
    MessageInfo,
    PolySerializer,
    Serializer,
)

__all__ = [
    "Deserializer",
    "MessageInfo",
    "Serializer",
    "PolySerializer",
    "RegistryBadRequestError",
    "RegistryBrokenError",
    "RegistryError",
    "RegistryHttpError",
    "RegistryRedirectionError",
]
