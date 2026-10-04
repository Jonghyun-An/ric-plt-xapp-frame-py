# SPDX-License-Identifier: Apache-2.0
"""Registration failures must remain false when consumed by registerXapp."""
import socket
from types import SimpleNamespace

import pytest
import requests
from mdclogpy import Logger

from ricxappframe.xapp_frame import _BaseXapp
import ricxappframe.xapp_frame as frame


@pytest.fixture
def xapp():
    app = object.__new__(_BaseXapp)
    app.logger = Logger(name="registration-test")
    return app


@pytest.mark.parametrize("error", [
    requests.exceptions.ConnectionError("connection refused"),
    requests.exceptions.Timeout("timed out"),
    requests.exceptions.HTTPError("HTTP error"),
    requests.exceptions.RequestException("request failed"),
])
def test_registration_transport_failure_is_false(xapp, monkeypatch, error):
    def fail(*args, **kwargs):
        raise error
    monkeypatch.setattr(requests, "post", fail)
    assert xapp.do_post("ricplt", "http://example.invalid/{}/register", {}) is False


@pytest.mark.parametrize("status, expected", [(200, True), (201, True), (400, False), (503, False)])
def test_registration_http_status(xapp, monkeypatch, status, expected):
    monkeypatch.setattr(requests, "post", lambda *a, **kw: SimpleNamespace(status_code=status, text=""))
    assert xapp.do_post("ricplt", "http://example.invalid/{}/register", {}) is expected


@pytest.mark.parametrize("namespace, url", [(None, "http://example.invalid"), ("ricplt", None)])
def test_registration_missing_argument(xapp, namespace, url):
    assert xapp.do_post(namespace, url, {}) is False


def test_registration_real_refused_connection(xapp):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        # A bound, non-listening socket refuses connections without a port race.
        assert xapp.do_post("ricplt", "http://127.0.0.1:%d/register" % port, {}) is False


@pytest.mark.parametrize("eventually_succeeds, expected_calls", [(True, 2), (False, 5)])
def test_registration_loop_retries_transport_failures(xapp, monkeypatch, eventually_succeeds, expected_calls):
    calls = []

    def post(*args, **kwargs):
        calls.append(args)
        if eventually_succeeds and len(calls) == 2:
            return SimpleNamespace(status_code=201, text="registered")
        raise requests.exceptions.ConnectionError("registration unavailable")

    monkeypatch.setattr(requests, "post", post)
    monkeypatch.setattr(frame.time, "sleep", lambda seconds: None)
    xapp._keep_registration = True
    xapp._config_data = {"name": "retry-test"}
    xapp.healthcheck = lambda: True
    xapp.register = lambda: xapp.do_post("ricplt", "http://example.invalid/{}/register", {})
    xapp.registerXapp()
    assert len(calls) == expected_calls
