################################################################
How to connect to an SSL-secured Kafka cluster (Strimzi example)
################################################################

Kafkit's `kafkit.ssl` module can help you connect to Kafka brokers that require your aiokafka_\ -based clients to connect with the SSL protocol.
SSL is commonly used to mutually authenticate the client and Kafka brokers: the broker authenticates the client, and the client authenticates the broker.
SSL authentication is also commonly used in conjunction with Kafka's ACL-based *authorization* system, which ensures that specific clients can only perform a specific set of operations.

This page describes how to use `kafkit.ssl` to help connect your aiokafka_ client for the specific case of a Strimzi_\ -based Kafka cluster.
Strimzi_ makes it convenient to deploy secured Kafka clusters in Kubernetes.
The basic ideas in this tutorial, however, apply to any SSL-secured Kafka cluster.

Gathering the SSL client and broker certificates
================================================

In a Strimzi-based deployment, the Kafka broker's SSL certificate and the client's SSL certificates are in separate Kubernetes ``Secret`` resources.

- The Kafka broker's CA certificate is in a secret named ``{clustername}-cluster-ca-cert``, where ``{clustername}`` matches the name of the Strimzi ``Kafka`` resource.

- The client certificates are in a secret named ``{clientname}``, where ``{clientname}`` matches the name of the client's Strimzi ``KafkaUser`` resource.

In your client's Kubernetes ``Deployment`` resource, you can mount these Secrets as files in your pod's filesystem (extraneous ``Deployment`` fields omitted):

.. code-block:: yaml

   apiVersion: apps/v1
   kind: Deployment
   spec:
     template:
       spec:
         containers:
           - name: myapp
             volumeMounts:
               - name: "client-ssl"
                 mountPath: "/var/strimzi-client"
                 readOnly: True
               - name: "broker-ssl"
                 mountPath: "/var/strimzi-broker"
                 readOnly: True
         volumes:
           # Mount the TLS secret created by KafkaUser
           - name: "client-tls"
             secret:
               # matches name of KafkaUser
               secretName: kafkauser-myapp
           - name: "broker-tls"
             secret:
               # matches name of Strimzi cluster CA cert secret
               secretName: "events-cluster-ca-cert"

In your Python application code, you can create paths to the individual certificates and key files:

.. code-block:: python

   from pathlib import Path

   broker_ca_path = Path("/var/strimzi-broker/ca.crt")

   client_cert_path = Path("/var/strimzi-client/user.crt")
   client_key_path = Path("/var/strimzi-client/user.key")

Create the SSLContext
=====================

Both `aiokafka.AIOKafkaConsumer` and `aiokafka.AIOKafkaProducer` use an SSL context (`ssl.SSLContext`) to support SSL communication with the Kafka brokers.
The `kafkit.ssl.create_ssl_context` function lets you create an `~ssl.SSLContext` instance with your certificates and keys:

.. code-block:: python

   from kafkit.ssl import create_ssl_context

   ssl_context = create_ssl_context(
       cluster_ca_path=broker_ca_path,
       client_cert_path=client_cert_path,
       client_key_path=client_key_path,
   )

Using the SSLContext
====================

Finally you can use that ``ssl_context`` as the ``ssl_context`` argument to `aiokafka.AIOKafkaProducer` or `aiokafka.AIOKafkaConsumer`:

.. code-block:: python

   import asyncio
   from aiokafka import AIOKafkaProducer

   producer = AIOKafkaProducer(
       loop=asyncio.get_running_loop(),
       bootstrap_servers="kafka:9093",
       ssl_context=ssl_context,
       security_protocol="SSL",
   )
   await producer.start()

   ...

   await producer.stop()
