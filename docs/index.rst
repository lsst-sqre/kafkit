######
Kafkit
######

Kafkit helps you write Kafka producers and consumers in Python with asyncio:

- Kafkit provides a client for the Confluent Schema Registry's HTTP API.
  The `~kafkit.registry.aiohttp.RegistryApi` client includes both high-level methods for managing subjects and schemas in a Registry, and direct low-level access to HTTP methods (GET, POST, PUT, PATCH, and DELETE).
  The high-level methods use caching so you can use the client as an integral part of your application's schema management.
  `~kafkit.registry.aiohttp.RegistryApi` is implemented around aiohttp_, but since the base class is designed with a `sans IO architecture <https://sans-io.readthedocs.io>`__, a Registry client can be implemented with any asyncio HTTP library.

- Kafkit provides Avro message serializers and deserializers that integrate with the `Confluent Schema Registry`_: `~kafkit.registry.Deserializer`, `~kafkit.registry.Serializer`, and `~kafkit.registry.PolySerializer`.

- The `~kafkit.registry.manager.RecordNameSchemaManager` is a streamlined tool for serializing messages using the schemas maintained by your app, while also integrating with the `Confluent Schema Registry`_.

- The `kafkit.ssl` module helps you connect to SSL-secured Kafka brokers.

Installation
============

Install Kafkit with aiohttp:

.. code-block:: sh

   pip install kafkit[aiohttp]

User guide
==========

.. toctree::
   :maxdepth: 2

   recordnameschemamanager-howto
   strimzi-ssl-howto

API reference
=============

.. toctree::

   api

Developer guide
===============

.. toctree::
   :maxdepth: 2

   dev/index

Project information
===================

Kafkit is developed on GitHub at https://github.com/lsst-sqre/kafkit.

.. toctree::
   :maxdepth: 1

   changelog
