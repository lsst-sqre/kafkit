import os

import kafkit
import lsst_sphinx_bootstrap_theme

# Common links and substitutions =============================================

rst_epilog = """
.. _aiohttp: https://aiohttp.readthedocs.io/en/stable/
.. _aiokafka: https://aiokafka.readthedocs.io/en/stable/
.. _Confluent Schema Registry: https://docs.confluent.io/current/schema-registry/docs/index.html
.. _Confluent Wire Format: https://docs.confluent.io/current/schema-registry/docs/serializer-formatter.html#wire-format
.. _mypy: http://www.mypy-lang.org
.. _pre-commit: https://pre-commit.com
.. _pytest: https://docs.pytest.org/en/latest/
.. _Schema Evolution and Compatibility: https://docs.confluent.io/current/schema-registry/avro.html
.. _Strimzi: https://strimzi.io
.. _tox: https://tox.readthedocs.io/en/latest/
"""

# Extensions =================================================================

extensions = [
    "sphinx.ext.autodoc",
    # "sphinx.ext.autodoc.typehints",
    "sphinx.ext.napoleon",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx-prompt",
    "sphinx_automodapi.automodapi",
    "sphinx_automodapi.smart_resolver",
    "documenteer.sphinxext",
]

# General configuration ======================================================

source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "Kafkit"
copyright = (
    "2019-2020 "
    "Association of Universities for Research in Astronomy, Inc. (AURA)"
)
author = "LSST Data Management"

version = kafkit.__version__
release = version

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build", "README.rst"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# The reST default role cross-links Python (used for this markup: `text`)
default_role = "py:obj"

# Intersphinx ================================================================

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "aiohttp": ("https://aiohttp.readthedocs.io/en/stable/", None),
    "aiokafka": ("https://aiokafka.readthedocs.io/en/stable/", None),
    "fastavro": ("https://fastavro.readthedocs.io/en/latest/", None),
}

intersphinx_timeout = 10.0  # seconds
intersphinx_cache_limit = 5  # days

# Linkcheck builder ==========================================================

linkcheck_retries = 2

# linkcheck_ignore = [r'^https://jira.lsstcorp.org/browse/']

linkcheck_timeout = 15

# HTML builder ===============================================================

templates_path = [
    "_templates",
    lsst_sphinx_bootstrap_theme.get_html_templates_path(),
]

html_theme = "lsst_sphinx_bootstrap_theme"
html_theme_path = [lsst_sphinx_bootstrap_theme.get_html_theme_path()]

html_context = {
    # Enable "Edit in GitHub" link
    "display_github": True,
    # https://{{ github_host|default("github.com") }}/{{ github_user }}/
    #     {{ github_repo }}/blob/
    #     {{ github_version }}{{ conf_py_path }}{{ pagename }}{{ suffix }}
    "github_user": "lsst-sqre",
    "github_repo": "kafkit",
    "conf_py_path": "docs/",
    # GITHUB_REF is available in GitHub Actions, but master is a safe default
    "github_version": os.getenv("GITHUB_REF", default="master") + "/",
}

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {"logotext": project}

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = f"{project} v{version}"

# A shorter title for the navigation bar.  Default is the same as html_title.
html_short_title = project

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = False

# Do not copy reST source for each page into the build
html_copy_source = False

# If false, no module index is generated.
html_domain_indices = True

# If false, no index is generated.
html_use_index = True

# API Reference ==============================================================

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_keyword = True  # TODO
napoleon_use_param = True
napoleon_use_rtype = True

autosummary_generate = True

automodapi_toctreedirnm = "api"
automodsumm_inherited_members = True

# Docstrings for classes and methods are inherited from parents.
autodoc_inherit_docstrings = True

# Class documentation should only contain the class docstring and
# ignore the __init__ docstring, account to LSST coding standards.
autoclass_content = "class"

# Default flags for automodapi directives. Special members are dunder
# methods.
autodoc_default_options = {
    "show-inheritance": True,
    "special-members": True,
}

# Render inheritance diagrams in SVG
graphviz_output_format = "svg"

graphviz_dot_args = [
    "-Nfontsize=10",
    "-Nfontname=Helvetica Neue, Helvetica, Arial, sans-serif",
    "-Efontsize=10",
    "-Efontname=Helvetica Neue, Helvetica, Arial, sans-serif",
    "-Gfontsize=10",
    "-Gfontname=Helvetica Neue, Helvetica, Arial, sans-serif",
]

# TODO extension =============================================================

todo_include_todos = False
