"""Common code that can be used by registry and broker-oriented applications.

This code is based on on the sans-io code of Gidgethub
(https://github.com/brettcannon/gidgethub) and generalized for Kafkit.
"""

import urllib.parse
from collections.abc import Mapping
from email.message import Message

import uritemplate

__all__ = ["format_url", "parse_content_type"]


def format_url(*, host: str, url: str, url_vars: Mapping[str, str]) -> str:
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
    return uritemplate.expand(url, dict(url_vars))


def parse_content_type(
    content_type: str | None,
) -> tuple[str | None, str]:
    """Tease out the content-type and character encoding.

    A default character encoding of UTF-8 is used, so the content-type
    must be used to determine if any decoding is necessary to begin
    with.
    """
    if content_type is None:
        return None, "utf-8"
    else:
        m = Message()
        m["content-type"] = content_type
        return m.get_content_type(), m.get_param("charset", "utf-8")
