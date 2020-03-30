"""Support for connecting to brokers with SSL."""

import ssl
from pathlib import Path

__all__ = ["create_ssl_context"]


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
