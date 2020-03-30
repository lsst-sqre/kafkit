"""Aiohttp client for the Confluent Schema Registry.

This code and architecture is based on https://github.com/brettcannon/gidgethub
See licenses/gidgethub.txt for info.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Mapping, Tuple

from kafkit.registry import sansio

if TYPE_CHECKING:
    from aiohttp import ClientSession

__all__ = ["RegistryApi"]


class RegistryApi(sansio.RegistryApi):
    """A Confluent Schema Registry client that uses aiohttp.

    Parameters
    ----------
    session : `aiohttp.ClientSession`
        An aiohttp client session.
    url : `str`
        The Confluent Schema Registry URL (e.g. http://registry:8081).
    """

    def __init__(self, *, session: ClientSession, url: str) -> None:
        self._session = session
        super().__init__(url=url)

    async def _request(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes
    ) -> Tuple[int, Mapping[str, str], bytes]:
        async with self._session.request(
            method, url, headers=headers, data=body
        ) as response:
            return response.status, response.headers, await response.read()
