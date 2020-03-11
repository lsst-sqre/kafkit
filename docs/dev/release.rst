#################
Release procedure
#################

This page gives an overview of how Kafkit releases are made.
This information is only useful for maintainers.

Kafkit's releases are largely automated through GitHub Actions (see the `ci.yaml`_ workflow file for details).
When a semantic version tag is pushed to GitHub, `Kafkit is released to PyPI`_ with that version.
Similarly, documentation is built and pushed for each version (see https://kafkit.lsst.io/v).

.. _`Kafkit is released to PyPI`: https://pypi.org/project/kafkit/
.. _`ci.yaml`: https://github.com/lsst-sqre/kafkit/blob/master/.github/workflows/ci.yaml

.. _regular-release:

Regular releases
================

Regular releases happen from the ``master`` branch after changes have been merged.
From the ``master`` branch you can release a new major version (``X.0.0``), a new minor version of the current major version (``X.Y.0``), or a new patch of the current major-minor version (``X.Y.Z``).
See :ref:`backport-release` to patch an earlier major-minor version.

Release tags are semantic version identifiers following the :pep:`440` specification.

1. Change log and documentation
-------------------------------

Each PR should include updates to the change log.
If the change log or documentation needs additional updates, now is the time to make those changes through the regular branch-and-PR development method against the ``master`` branch.

In particular, replace the "Unreleased" section headline with the semantic version and date.
See :ref:`dev-change-log` in the *Developer guide* for details.

2. Tag the release
------------------

At the HEAD of the ``master`` branch, create and push a tag with the semantic version:

.. code-block:: sh

   git tag -s X.Y.Z -m "X.Y.Z"
   git push --tags

The tag **must** follow the :pep:`440` specification since Kafkit uses setuptools_scm_ to set version metadata based on Git tags.
In particular, **don't** prefix the tag with ``v``.

.. _setuptools_scm: https://github.com/pypa/setuptools_scm

The `ci.yaml`_ GitHub Actions workflow uploads the new release to PyPI and documentation to https://kafkit.lsst.io.

.. _backport-release:

Backport releases
=================

The regular release procedure works from the main line of development on the ``master`` Git branch.
To create a release that patches an earlier major or minor version, you need to release from a **release branch.**

Creating a release branch
-------------------------

Release branches are named after the major and minor components of the version string: ``X.Y``.
If the release branch doesn't already exist, check out the latest patch for that major-minor version:

.. code-block:: sh

   git checkout X.Y.Z
   git checkout -b X.Y
   git push -u

Developing on a release branch
------------------------------

Once a release branch exists, it becomes the "master" branch for patches of that major-minor version.
Pull requests should be based on, and merged into, the release branch.

If the development on the release branch is a backport of commits on the ``master`` branch, use ``git cherry-pick`` to copy those commits into a new pull request against the release branch.

Releasing from a release branch
-------------------------------

Releases from a release branch are equivalent to :ref:`regular releases <regular-release>`, except that the release branch takes the role of the ``master`` branch.
