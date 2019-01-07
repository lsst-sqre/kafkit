"""Tests for the kafkit.registry.sansio module.
"""

from kafkit.registry.sansio import make_headers


def test_make_headers():
    headers = make_headers()

    assert headers['accept'] == 'application/vnd.schemaregistry.v1+json'
