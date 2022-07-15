"""Kafkit helps you write Kafka producers and consumers in Python with asyncio.
"""

__all__ = ["__version__", "version_info"]

from importlib.metadata import PackageNotFoundError, version
from typing import List

__version__: str
"""The version string of Kafkit (PEP 440 / SemVer compatible)."""

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # package is not installed
    __version__ = "0.0.0"

version_info: List[str] = __version__.split(".")
"""The decomposed version, split across "``.``."

Use this for version comparison.
"""
