"""Tests for the kafkit.ssl module."""

from __future__ import annotations

import ssl
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from kafkit.ssl import concatenate_certificates, create_ssl_context

if TYPE_CHECKING:
    from _pytest.tmpdir import TempPathFactory


@pytest.fixture(scope="session")
def cluster_ca_path() -> Path:
    """A cluster CA certificate, as created by Strimzi."""
    return Path(__file__).parent / "data" / "ssl" / "cluster.ca.crt"


@pytest.fixture(scope="session")
def client_cert_path() -> Path:
    """A client certificate, as created by Stimzi."""
    return Path(__file__).parent / "data" / "ssl" / "client.crt"


@pytest.fixture(scope="session")
def client_ca_cert_path() -> Path:
    """A client CA certificate, as created by Strimzi."""
    return Path(__file__).parent / "data" / "ssl" / "client.ca.crt"


@pytest.fixture(scope="session")
def client_key_path() -> Path:
    """A demo client key certificate, as created by Strimzi."""
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


def test_concatenate_certificates(
    tmp_path_factory: TempPathFactory,
    cluster_ca_path: Path,
    client_cert_path: Path,
    client_key_path: Path,
    client_ca_cert_path: Path,
) -> None:
    """Test the create_ssl_context scenario where a client CA and certificate
    must be concatenated together.
    """
    temp_dir = tmp_path_factory.mktemp("concatenate_certificates")
    client_path = temp_dir / "client.crt"
    concatenate_certificates(
        output_path=client_path,
        cert_path=client_cert_path,
        ca_path=client_ca_cert_path,
    )
    ssl_context = create_ssl_context(
        cluster_ca_path=cluster_ca_path,
        client_cert_path=client_path,
        client_key_path=client_key_path,
    )
    assert isinstance(ssl_context, ssl.SSLContext)
