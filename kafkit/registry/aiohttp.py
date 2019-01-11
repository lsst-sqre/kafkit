"""Aiohttp client for the Confluent Schema Registry.

This code and architecture is based on https://github.com/brettcannon/gidgethub
See licenses/gidgethub.txt for info.
"""

__all__ = ('RegistryApi')

from . import sansio


class RegistryApi(sansio.RegistryApi):
    """A Confluent Schema Registry client that uses aiohttp.

    Parameters
    ---------
    session : `aiohittp.ClientSession`
        An aiohttp client session.
    url : `str`
        The Confluent Schema Registry URL (e.g. http://registry:8081).
    """

    def __init__(self, *, session, url):
        self._session = session
        super().__init__(url=url)

    async def _request(self, method, url, headers, body):
        async with self._session.request(
                method, url, headers=headers, data=body) as response:
            return response.status, response.headers, await response.read()
