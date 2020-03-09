"""Support for connecting to brokers with SSL."""

__all__ = ["create_ssl_context", "concatenate_certificates"]

import ssl
from pathlib import Path
from typing import List


def create_ssl_context(
    *, cluster_ca_path: Path, client_cert_path: Path, client_key_path: Path
) -> ssl.SSLContext:
    """Create an SSL context for a client connecting to secured Kafka brokers.

    Parameters
    ----------
    cluster_ca_path : `pathlib.Path`
        Path to the cluster CA certificate.
    client_cert_path : `pathlib.Path`
        Path to the client certificate.
    client_key_path : `pathlib.Path`
        Path to the client key.

    Returns
    -------
    ssl.SSLContext
        An SSL context for a Kafka client.
    """
    # Create a SSL context on the basis that we're the client authenticating
    # the server (the Kafka broker).
    ssl_context = ssl.create_default_context(
        purpose=ssl.Purpose.SERVER_AUTH, cafile=str(cluster_ca_path)
    )
    # Add the certificates that the Kafka broker uses to authenticate us.
    ssl_context.load_cert_chain(
        certfile=str(client_cert_path), keyfile=str(client_key_path)
    )
    return ssl_context


def concatenate_certificates(
    *, output_path: Path, cert_path: Path, ca_path: Path
) -> None:
    """Concatenate a certificate with a CA and save to an output path.

    Parameters
    ----------
    cert_path : `pathlib.Path`
        The certificate path.
    ca_path : `pathlib.Path`
        The CA path.
    output_path : `pathlib.Path`
        Path where the concatenated certificate is written.
    """
    certificates: List[str] = []
    for p in [cert_path, ca_path]:
        cert = p.read_text()
        if not cert.endswith("\n"):
            cert += "\n"
        certificates.append(cert)
    certificate = "".join(certificates)
    output_path.write_text(certificate)
