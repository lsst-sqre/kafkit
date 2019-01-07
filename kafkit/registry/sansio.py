"""Code to help use the Confluent Schema Registry that is not specific to a
particular http client library.

(Inspired by https://github.com/brettcannon/gidgethub and
https://sans-io.readthedocs.io.)
"""

__all__ = ('make_headers',)


def make_headers():
    """Make HTTP headers for the Confluent Schema Registry.

    Returns
    -------
    headers : `dict`
        A dictionary of HTTP headers for a Confluent Schema Registry request.
        All keys are normalized to lowercase for consistency.
    """
    headers = {
        'accept': 'application/vnd.schemaregistry.v1+json'
    }
    return headers
