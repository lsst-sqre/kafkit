"""Schema managers register schemas with the registry and enable conventient
serialization and deserialization of messages.
"""

from ._pydantic import PydanticSchemaManager
from ._recordname import RecordNameSchemaManager

__all__ = ["RecordNameSchemaManager", "PydanticSchemaManager"]
