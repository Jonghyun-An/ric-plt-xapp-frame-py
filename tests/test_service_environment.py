# SPDX-License-Identifier: Apache-2.0
"""Resolve Kubernetes service URLs without requiring optional environment keys."""
import pytest
from mdclogpy import Logger

from ricxappframe.xapp_frame import _BaseXapp


@pytest.mark.parametrize("namespace, value, expected", [
    ("ricxapp", None, ""),
    ("ricxapp", "", ""),
    (None, None, ""),
    ("ricxapp", "tcp://10.0.0.1:4560", "10.0.0.1:4560"),
    ("custom-ns", "tcp://service:8080", "service:8080"),
    ("ricxapp", "10.0.0.1:4560", ""),
])
def test_optional_service_environment(monkeypatch, namespace, value, expected):
    app = object.__new__(_BaseXapp)
    app.logger = Logger(name="service-test")
    app._config_data = {"APP_NAMESPACE": namespace}
    actual_namespace = namespace or "ricxapp"
    key = ("SERVICE_%s_%s_PORT" % (actual_namespace.upper(), "APP-MGR")).replace("-", "_")
    monkeypatch.delenv(key, raising=False)
    if value is not None:
        monkeypatch.setenv(key, value)
    assert app.get_service("app-mgr", "SERVICE_{}_{}_PORT") == expected


def test_service_without_host(monkeypatch):
    app = object.__new__(_BaseXapp)
    app.logger = Logger(name="service-test")
    app._config_data = {}
    assert app.get_service(None, "SERVICE_{}_{}_PORT") == ""
