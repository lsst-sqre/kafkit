# Kafkit

Kafkit helps you write Kafka producers and consumers in Python with asyncio:

- Kafkit provides a client for the Confluent Schema Registry's HTTP API.
  The `RegistryApi` client includes both high-level methods for managing subjects and schemas in a Registry, and direct low-level access to HTTP methods (GET, POST, PUT, PATCH, and DELETE).
  The high-level methods use caching so you can use the client as an integral part of your application's schema management.
  `RegistryApi` is implemented around [aiohttp](https://aiohttp.readthedocs.io/en/stable/), but since the base class is designed with a [sans IO architecture](https://sans-io.readthedocs.io), a Registry client can be implemented with any asyncio HTTP library.

- Kafkit provides Avro message serializers and deserializers that integrate with the [Confluent Schema Registry](https://docs.confluent.io/current/schema-registry/docs/index.html): `Deserializer`, `Serializer`, and `PolySerializer`.

- The `RecordNameSchemaManager` is a streamlined tool for serializing messages using the schemas maintained by your app, while also integrating with the [Confluent Schema Registry](https://docs.confluent.io/current/schema-registry/docs/index.html).

- The `kafkit.ssl` module helps you connect to SSL-secured Kafka brokers.

Learn more about Kafkit at https://kafkit.lsst.io.
