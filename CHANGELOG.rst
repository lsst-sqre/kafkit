##########
Change log
##########

0.1.1 (2019-02-13)
==================

Several fixes:

- ``RegistryApi.put`` was doing a ``PATCH`` behind the scenes. That's fixed now.
- The ``RegistryApi.put``, ``patch``, and ``delete`` methods weren't returning data. That's fixed now as well.
- All of the RegistryApi's low-level HTTP methods have more thorough unit testing now to avoid these issues in the future.

:jirab:`DM-17879`

0.1.0 (2019-01-30)
==================

Initial release of Kafkit!

This release includes the ``kafkit.registry`` package with a working `Confluent Schema Registry`_ API client implemented with a sans I/O design.
There are two client implementations.
One is designed for aiohttp_ users (``kafkit.registry.aiohttp.RegistryClient``), and the other is for I/O-free unit testing (``kafkit.registry.sansio.MockRegistryApi``).
The clients include schema caches so they can be used as both local stores of schemas, in addition to accessors for remote schemas.
The release also includes a suite of Avro message serializers and deserializers that integrate with `Confluent Schema Registry`_ and the Confluent Wire Format (``kafkit.registry.serializer``).

:jirab:`DM-17058`

.. _aiohttp: https://aiohttp.readthedocs.io/en/stable/
.. _Confluent Schema Registry: https://docs.confluent.io/current/schema-registry/docs/index.html
