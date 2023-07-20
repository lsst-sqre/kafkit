#################
Development guide
#################

This page provides procedures and guidelines for developing and contributing to Kafkit.

Scope of contributions
======================

Kafkit is an open source package, meaning that you can contribute to Kafkit itself, or fork Kafkit for your own purposes.

Since Kafkit is intended for internal use by Rubin Observatory, community contributions can only be accepted if they align with Rubin Observatory's aims.
For that reason, it's a good idea to propose changes with a new `GitHub issue`_ before investing time in making a pull request.

Kafkit is developed by the LSST SQuaRE team.

.. _GitHub issue: https://github.com/lsst-sqre/kafkit/issues/new

.. _dev-environment:

Setting up a local development environment
==========================================

To develop Kafkit, create a virtual environment with your method of choice (like virtualenvwrapper) and then clone or fork, and install:

.. code-block:: sh

   git clone https://github.com/lsst-sqre/kafkit.git
   cd kafkit
   make init

This init step does three things:

1. Installs Kafkit in an editable mode with its "dev" extra that includes test and documentation dependencies.
2. Installs pre-commit and tox.
3. Installs the pre-commit hooks.

.. _pre-commit-hooks:

Pre-commit hooks
================

The pre-commit hooks, which are automatically installed by running the :command:`make init` command on :ref:`set up <dev-environment>`, ensure that files are valid and properly formatted.
Some pre-commit hooks automatically reformat code:

``ruff``
    Automatically fixes common issues in code and sorts imports.

``black``
    Automatically formats Python code.

``blacken-docs``
    Automatically formats Python code in reStructuredText documentation and docstrings.

When these hooks fail, your Git commit will be aborted.
To proceed, stage the new modifications and proceed with your Git commit.

.. _dev-run-tests:

Running tests
=============

One way to test the library is by running pytest_ from the root of the source repository:

.. code-block:: sh

   pytest

You can also run tox_, which tests the library the same way that the CI workflow does:

.. code-block:: sh

   tox run

To see a listing of test environments, run:

.. code-block:: sh

   tox list

.. _dev-build-docs:

Building documentation
======================

Documentation is built with Sphinx_:

.. _Sphinx: https://www.sphinx-doc.org/en/master/

.. code-block:: sh

   tox run -e docs

The build documentation is located in the :file:`docs/_build/html` directory.

.. _dev-change-log:

Updating the change log
=======================

Each pull request should update the change log (:file:`CHANGELOG.md`).
The change log is maintained with scriv_.

To create a new change log fragment, run:

.. code-block:: sh

   scriv create

This creates a new file in the :file:`changelog.d` directory.
Edit this file to describe the changes in the pull request.
If sections don't apply to the change you can delete them.

.. _style-guide:

Style guide
===========

Code
----

- The code style follows :pep:`8`, though in practice lean on Black and ruff to format the code for you.

- Use :pep:`484` type annotations.
  The ``tox -e typing`` test environment, which runs mypy_, ensures that the project's types are consistent.

- Write tests for Pytest_.

Documentation
-------------

- Follow the `LSST DM User Documentation Style Guide`_, which is primarily based on the `Google Developer Style Guide`_.

- Document the Python API with numpydoc-formatted docstrings.
  See the `LSST DM Docstring Style Guide`_.

- Follow the `LSST DM ReStructuredTextStyle Guide`_.
  In particular, ensure that prose is written **one-sentence-per-line** for better Git diffs.

.. _`LSST DM User Documentation Style Guide`: https://developer.lsst.io/user-docs/index.html
.. _`Google Developer Style Guide`: https://developers.google.com/style/
.. _`LSST DM Docstring Style Guide`: https://developer.lsst.io/python/style.html
.. _`LSST DM ReStructuredTextStyle Guide`: https://developer.lsst.io/restructuredtext/style.html
