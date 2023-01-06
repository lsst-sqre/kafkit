"""Httpx client for the Confluent Schema Registry.

This code and architecture is based on https://github.com/brettcannon/gidgethub
See licenses/gidgethub.txt for info.
"""

from __future__ import annotations

from typing import Mapping, Tuple

from httpx import AsyncClient

from . import sansio

__all__ = ["RegistryApi"]


class RegistryApi(sansio.RegistryApi):
    """A Confluent Schema Registry client that uses httpx.

    Parameters
    ----------
    http_client
        The async httpx client.
    """

    def __init__(self, *, http_client: AsyncClient, url: str) -> None:
        self._client = http_client
        super().__init__(url=url)

    async def _request(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes
    ) -> Tuple[int, Mapping[str, str], bytes]:
        response = await self._client.request(
            method, url, headers=headers, content=body
        )
        return response.status_code, response.headers, response.read()
