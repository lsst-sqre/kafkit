"""Tests for the kafkit.utils module."""

import pytest

from kafkit.httputils import format_url


@pytest.mark.parametrize(
    "host,url,url_vars,expected",
    [
        (
            "http://confluent-kafka-cp-schema-registry:8081",
            "/subjects{/subject}/versions",
            {"subject": "helloworld"},
            "http://confluent-kafka-cp-schema-registry:8081/"
            "subjects/helloworld/"
            "versions",
        ),
        # Add domain to url
        (
            "http://confluent-kafka-cp-schema-registry:8081",
            "http://registry:8081/subjects{/subject}/versions",
            {"subject": "helloworld"},
            "http://registry:8081/subjects/helloworld/versions",
        ),
        # Add extra variables
        (
            "http://confluent-kafka-cp-schema-registry:8081",
            "/subjects{/subject}/versions",
            {"subject": "helloworld", "extra": "notused"},
            "http://confluent-kafka-cp-schema-registry:8081/"
            "subjects/helloworld/"
            "versions",
        ),
    ],
)
def test_format_url(host, url, url_vars, expected):
    assert expected == format_url(host=host, url=url, url_vars=url_vars)
