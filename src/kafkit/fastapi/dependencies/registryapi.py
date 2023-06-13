"""A FastAPI dependency that provides a Kafkit RegistryApi client."""

from httpx import AsyncClient

from kafkit.registry.httpx import RegistryApi

__all__ = ["registry_api_dependency", "RegistryApiDependency"]


class RegistryApiDependency:
    """A FastAPI dependency that provides a Kafkit RegistryApi client."""

    def __init__(self) -> None:
        self._registry_api: RegistryApi | None = None

    async def initialize(
        self, *, http_client: AsyncClient, registry_url: str
    ) -> None:
        """Initialize the dependency (call during FastAPI startup)."""
        self._registry_api = RegistryApi(
            http_client=http_client, url=registry_url
        )

    async def __call__(self) -> RegistryApi:
        """Get the dependency (call during FastAPI request handling)."""
        if self._registry_api is None:
            raise RuntimeError("Dependency not initialized")
        return self._registry_api


registry_api_dependency = RegistryApiDependency()
"""The FastAPI dependency callable that provides a Kafkit RegistryApi
client.
"""
