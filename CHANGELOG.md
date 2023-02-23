# Change log

## 0.3.0 (2023-02-23)

New features:

- New [HTTPX](https://www.python-httpx.org) support with `kafkit.registry.httpx.RegistryApi`, in addition to the existing aiohttp support.
- Documentation is now built with the new Rubin Observatory user guide theme and Sphinx configuration.
- The `__named_schemas` annotation added by FastAvro is now stripped, in addition to `__fastavro_parsed`. Via @hhromic 🎉
- Kafkit is now also available on Conda-Forge (feedstock URL: https://github.com/conda-forge/kafkit-feedstock).

## 0.2.1 (2022-07-15)

A `py.typed` file is now included to advertise type annotations in Kafkit.

## 0.2.0 (2022-07-15)

- Python versions 3.7 and earlier are no longer supported because Kafkit is adopting the `annotations` import from `__future__` and native support for `importlib.metadata`.
  Kafkit is explicitly tested with Python 3.8, 3.9, and 3.10.

- We've added a `kafkit.ssl` module to help connect to Kafka brokers over TLS.
  The associated documentation includes a tutorial for working with the SSL certificates generated in a Kafka cluster managed by [Strimzi](https://strimzi.io).

- The brand-new `kafkit.registry.manager.RecordNameSchemaManager` provides a streamlined workflow for serializing Avro messages using Avro schemas that are maintained in your app's codebase.
  The manager handles schema registration for you.
  To serialize a message, you simply need to provide the data and the name of the schema.

- A new `kafkit.registry.sansio.CompatibilityType` Enum helps you write use valid Schema Registry compatibility types.

- We've significantly improved Kafkit's packaging and infrastructure:

  - Migrate packaging metadata from `setup.py` to `pyproject.toml` (Kafkit continues to be a setuptools-based project).
  - Tox now runs tasks like tests, in conjunction with the existing Pytest set up.
  - Pre-commit hooks lint and format the code base.
  - Code style is now handled by Black (and in the documentation with blacken-docs).
  - **Full support for type annotations!** `tox -e typing` validates Kafkit's type annotations with Mypy.
  - We've migrated from Travis CI to GitHub Actions.

- The documentation now includes a development guide.

## 0.1.1 (2019-02-13)

Several fixes:

- `RegistryApi.put` was doing a `PATCH` behind the scenes. That's fixed now.
- The `RegistryApi.put`, `patch`, and `delete` methods weren't returning data. That's fixed now as well.
- All of the RegistryApi's low-level HTTP methods have more thorough unit testing now to avoid these issues in the future.

## 0.1.0 (2019-01-30)

Initial release of Kafkit!

This release includes the `kafkit.registry` package with a working [Confluent Schema Registry](https://docs.confluent.io/current/schema-registry/docs/index.html) API client implemented with a sans I/O design.
There are two client implementations.
One is designed for [aiohttp](https://aiohttp.readthedocs.io/en/stable/) users (`kafkit.registry.aiohttp.RegistryClient`), and the other is for I/O-free unit testing (`kafkit.registry.sansio.MockRegistryApi`).
The clients include schema caches so they can be used as both local stores of schemas, in addition to accessors for remote schemas.
The release also includes a suite of Avro message serializers and deserializers that integrate with [Confluent Schema Registry](https://docs.confluent.io/current/schema-registry/docs/index.html) and the Confluent Wire Format (`kafkit.registry.serializer`).
