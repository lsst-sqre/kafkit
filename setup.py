from setuptools import setup, find_packages
from pathlib import Path

package_name = 'kafkit'
description = (
    'Kafkit helps you write Kafka producers and consumers in '
    'Python with asyncio')
author = 'Association of Universities for Research in Astronomy'
author_email = 'sqre-admin@lists.lsst.org'
license = 'MIT'
url = 'https://github.com/lsst-sqre/kafkit'
pypi_classifiers = [
    'Development Status :: 4 - Beta',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
]
keywords = ['lsst', 'kafka']
readme = Path(__file__).parent / 'README.rst'

# Core dependencies
install_requires = [
    'uritemplate',
    'fastavro',
]

# For aiohttp extra
aiohttp_requires = [
    'aiohttp'
]

# Test dependencies
tests_require = [
    'pytest==4.0.2',
    'pytest-flake8==1.0.2',
    'pytest-asyncio==0.10.0',
]
tests_require += install_requires

# Sphinx documentation dependencies
docs_require = [
    'documenteer[pipelines]>=0.4.0,<0.5.0',
]

# Optional dependencies (like for dev)
extras_require = {
    # For development environments
    'dev': tests_require + docs_require + aiohttp_requires,

    'aiohttp': aiohttp_requires
}

# Setup-time dependencies
setup_requires = [
    'pytest-runner>=4.2.0,<5.0.0',
    'setuptools_scm',
]

setup(
    name=package_name,
    description=description,
    long_description=readme.read_text(),
    author=author,
    author_email=author_email,
    url=url,
    license=license,
    classifiers=pypi_classifiers,
    keywords=keywords,
    packages=find_packages(exclude=['docs', 'tests']),
    install_requires=install_requires,
    tests_require=tests_require,
    setup_requires=setup_requires,
    extras_require=extras_require,
    use_scm_version=True
)
