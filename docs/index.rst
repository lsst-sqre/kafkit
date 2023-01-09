######
Kafkit
######

Kafkit helps you write Kafka producers and consumers in Python with asyncio:

- Kafkit provides a client for the Confluent Schema Registry's HTTP API.
  The `~kafkit.registry.httpx.RegistryApi` client includes both high-level methods for managing subjects and schemas in a Registry, and direct low-level access to HTTP methods (GET, POST, PUT, PATCH, and DELETE).
  The high-level methods use caching so you can use the client as an integral part of your application's schema management.
  The client is implemented for both aiohttp_ and httpx_, but since the base class is designed with a `sans IO architecture <https://sans-io.readthedocs.io>`__, a Registry client can be implemented with any asyncio HTTP library.

- Kafkit provides Avro message serializers and deserializers that integrate with the `Confluent Schema Registry`_: `~kafkit.registry.Deserializer`, `~kafkit.registry.Serializer`, and `~kafkit.registry.PolySerializer`.

- The `~kafkit.registry.manager.RecordNameSchemaManager` is a streamlined tool for serializing messages using the schemas maintained by your app, while also integrating with the `Confluent Schema Registry`_.

- The `kafkit.ssl` module helps you connect to SSL-secured Kafka brokers.

Installation
============

Kafkit can be installed with different HTTP clients for convenience

.. tab-set::

   .. tab-item:: httpx

      .. code-block:: sh

          pip install kafkit[httpx]

   .. tab-item:: aiohttp

      .. code-block:: sh

          pip install kafkit[aiohttp]

   .. tab-item:: No client

      .. code-block:: sh

          pip install kafkit

Kafkit is also available on Conda-Forge at https://github.com/conda-forge/kafkit-feedstock.

.. toctree::
   :hidden:

   guide/index
   API <api>
   changelog
   Developer guide <dev/index>

Project information
===================

Kafkit is developed on GitHub at https://github.com/lsst-sqre/kafkit.
