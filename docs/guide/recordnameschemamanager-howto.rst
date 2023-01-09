.. |RecordNameSchemaManager| replace:: `~kafkit.registry.manager.RecordNameSchemaManager`

#################################
Using the RecordNameSchemaManager
#################################

The |RecordNameSchemaManager| is an opinionated tool for managing Avro Schemas with the `Confluent Schema Registry`_ and for serializing data using those schemas.
This page will help you understand what the |RecordNameSchemaManager| does and how to add the |RecordNameSchemaManager| into your application.

Overview of the RecordNameSchemaManager
=======================================

The role of a schema manager
----------------------------

Your application needs to serialize data with the exact Avro schemas that it is developed and tested with, rather than the latest schema for a subject in the `Confluent Schema Registry`_.
It's good practice, therefore, to package schemas with your application.

At the same time, you cannot serialize messages without using the `Confluent Schema Registry`_: the registered ID of a schema is included in every Avro-encoded message (see the `Confluent Wire Format`_).

The |RecordNameSchemaManager| helps you by automatically registering schema maintained inside your app with a `Confluent Schema Registry`_, and automatically associating schemas with their ID in a `Confluent Schema Registry`_ while serializing a message.

The "record name" subject naming strategy
-----------------------------------------

The |RecordNameSchemaManager| specifically adheres to the ``RecordNameStrategy`` option for the Schema Registry's `subject name strategy <https://docs.confluent.io/current/schema-registry/serializer-formatter.html#subject-name-strategy>`__.
Under this naming strategy, the name of a subject in the Schema Registry is the same as the fully-qualified name of the Avro schema.

For example, the following Avro schema would be registered in a subject named ``myapp.a``:

.. code-block:: json

   {
     "type": "record",
     "name": "a",
     "namespace": "myapp",
     "fields": [
       {"name": "field1", "type": "int"},
       {"name": "field2", "type": "string"}
     ]
   }

With the "record name" subject naming strategy, Schema Registry subjects are decoupled from Kafka topics: schemas for a given Schema Registry subject can appear in multiple Kafka topics, and a single Kafka topic can contain messages encoded with schemas from multiple subjects.

By adhering to the "record name" subject naming strategy, the |RecordNameSchemaManager| lets you specify a schema through its fully-qualified name.
Combined with |RecordNameSchemaManager|\ ’s control of schema versioning, this makes serialization applications convenient to write.

.. note::

   Other subject naming strategies exist, such as ``TopicNameStrategy`` and ``TopicRecordNameStrategy``.
   In fact, ``TopicNameStrategy`` (which requires that subjects be named ``{topic}-key`` and ``{topic}-value``) is the default.
   Although schema managers designed around these strategies aren't currently available, but they could be contributed.

How to use the RecordNameSchemaManager
======================================

This section outlines the essential steps for integrating the |RecordNameSchemaManager| with your application.

Step 1. Collect Avro schemas in a local directory
-------------------------------------------------

This workflow assumes that all the Avro schemas your application uses to serialize messages are maintained in the app's codebase.
Gather all those schemas into one directory.

This is a possible file layout:

.. code-block:: text

   .
   └── src
       └── myapp
           ├── __init__.py
           ├── app.py
           └── avro_schemas/
               ├── myapp.a.json
               └── myapp.b.json

Inside your application, store the path to the directory containing the Avro schemas:

.. code-block:: python

   from pathlib import Path

   schema_root = Path(__file__).parent / "avro_schemas"

Step 2. Initialize the RecordNameSchemaManager
----------------------------------------------

The |RecordNameSchemaManager| needs a Schema Registry API client:

.. code-block:: python

   from kafkit.registry.aiohttp import RegistryApi

   async with aiohttp.ClientSession() as http_session:
       registry_api = RegistryApi(
           session=http_session, url="http://localhost:8081"
       )
       ...

See `kafkit.registry.aiohttp.RegistryApi` for details.

Then create the schema manager:

.. code-block:: python

   schema_manager = RecordNameSchemaManager(
       root=schema_root,
       registry=registry_api,
   )

Step 3. Register schemas
------------------------

Next, register the locally-maintained schemas with the Schema Registry using the `~kafkit.registry.manager.RecordNameSchemaManager.register_schemas` method:

.. code-block:: python

   await manager.register_schemas(compatibility="FORWARD")

The ``compatibility`` parameter allows you to set the compatibility settings for each schema's subject.
If you do not wish to update the compatibility settings of subjects, or to use the registry's defaults, leave the ``compatibility`` parameter as `None`.

.. note::

   The ``FORWARD`` setting means that data serialized with the newer schema can be read by an application using an older version of that schema.
   This setting is useful if schemas are managed by producers, and consumers are gradually updated to keep up.

   See Confluent's documentation on `Schema Evolution and Compatibility`_ for information about this and other compatibility options.

It's safe to use the `~kafkit.registry.manager.RecordNameSchemaManager.register_schemas` method with schemas that are already registered.
The schema is automatically associated with its existing ID in the Schema Registry if it was previously registered.

Step 4. Serialize messages using schema names
---------------------------------------------

Now the fun part — serializing messages into Avro:

.. code-block:: python

   data = {"field1": 42, "field2": "Hello world"}
   message = await schema_manager.serialize(data=data, name="myapp.a")

Serializing messages is straightforward because you don't need to maintain schemas or schema IDs in the code for producing messages.
Instead, you only need to declare the name of the schema you are using to serialize data.

The same `~kafkit.registry.manager.RecordNameSchemaManager.serialize` method can serialize both the key and value of a Kafka message.

Now that your data is serialized, you can pass the ``message`` bytes object to `aiokafka.AIOKafkaProducer.send_and_wait`, or similar, method to produce a Kafka message.
