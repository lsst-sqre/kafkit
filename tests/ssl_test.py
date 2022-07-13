"""Tests for the kafkit.ssl module."""

from __future__ import annotations

import ssl
from pathlib import Path

import pytest

from kafkit.ssl import create_ssl_context


@pytest.fixture(scope="session")
def cluster_ca_path() -> Path:
    """Provide a cluster CA certificate, as created by Strimzi."""
    return Path(__file__).parent / "data" / "ssl" / "cluster.ca.crt"


@pytest.fixture(scope="session")
def client_cert_path() -> Path:
    """Provide a client certificate, as created by Stimzi."""
    return Path(__file__).parent / "data" / "ssl" / "client.crt"


@pytest.fixture(scope="session")
def client_key_path() -> Path:
    """Provide a demo client key certificate, as created by Strimzi."""
    return Path(__file__).parent / "data" / "ssl" / "client.key"


def test_create_ssl_context(
    cluster_ca_path: Path, client_cert_path: Path, client_key_path: Path
) -> None:
    """Test create_ssl_context (mostly a smoke test)."""
    ssl_context = create_ssl_context(
        cluster_ca_path=cluster_ca_path,
        client_cert_path=client_cert_path,
        client_key_path=client_key_path,
    )
    assert isinstance(ssl_context, ssl.SSLContext)
