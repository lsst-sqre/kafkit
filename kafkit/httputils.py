"""Common code that can be used by registry and broker-oriented applications.

This code is based on on the sans-io code of Gidgethub
(https://github.com/brettcannon/gidgethub) and generalized for Kafkit.
"""

__all__ = ('format_url', 'parse_content_type')

import cgi
import urllib

import uritemplate


def format_url(*, host, url, url_vars):
    """Construct a URL by merging host, path, and variables.

    Parameters
    ----------
    host : `str`
        The host, including protocol and port as necessary. For example,
        ``'http://registry.local:8081'``.
    url : `str`
        A URL, which may be absolute or relative to the host. The URL can be
        templated so that those variables are interpolated with the
        ``url_vars``. See https://uritemplate.readthedocs.io/en/latest/ for
        details about templating.
    url_vars : `dict`
        Variables that are interpolated into the URL.

    Returns
    -------
    url : `str`
        Fully-formatted URL.
    """
    url = urllib.parse.urljoin(host, url)
    return uritemplate.expand(url, **url_vars)


def parse_content_type(content_type):
    """Tease out the content-type and character encoding.

    A default character encoding of UTF-8 is used, so the content-type
    must be used to determine if any decoding is necessary to begin
    with.
    """
    if not content_type:
        return None, "utf-8"
    else:
        type_, parameters = cgi.parse_header(content_type)
        encoding = parameters.get("charset", "utf-8")
        return type_, encoding
