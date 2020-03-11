######
Kafkit
######

Kafkit helps you write Kafka producers and consumers in Python with asyncio:

- Kafkit integrates aiokafka_ consumers and producers with the `Confluent Schema Registry`_.
  The ``kafkit.registry.Deserializer`` class can deserialize messages with any schema that's registered in a `Confluent Schema Registry`_.
  The ``kafkit.registry.Serializer`` class can serialize Python objects against a single Avro schema, while the ``kafkit.registry.PolySerializer`` class is flexible enough to handle multiple schemas.

- Kafkit provides Python APIs for working with the Confluent Schema Registry's HTTP API.
  The ``kafkit.registry.aiohttp.RegistryApi`` client includes high-level methods that manage subjects and their schemas in a registry.
  These methods are cached so that the ``kafkit.registry.aiohttp.RegistryApi`` client can be an integral part of your application's schema management.
  Additionally, ``kafkit.registry.aiohttp.RegistryApi`` includes low-level HTTP methods (GET, POST, PUT, PATCH, DELETE) so you can work directly with the Confluent Schema Registry API if you want.

- ``kafkit.registry.aiohttp.RegistryApi`` is implemented with aiohttp_, but that's not the only implementation.
  Kafkit subscribes to the `sans IO architecture <https://sans-io.readthedocs.io>`__ (`gidgethub <https://gidgethub.readthedocs.io/en/latest/>`__ is a popular example) meaning that you can subclass ``kafkit.registry.sansio.RegistryApi`` to integrate with your favorite HTTP client library.
  The ``kafkit.registry.sansio.MockRegistryApi`` is a mock client that you can use in your app's unit tests.

Learn more about Kafkit at https://kafkit.lsst.io.

.. _aiohttp: https://aiohttp.readthedocs.io/en/stable/
.. _aiokafka: https://aiokafka.readthedocs.io/en/stable/
.. _Confluent Schema Registry: https://docs.confluent.io/current/schema-registry/docs/index.html
