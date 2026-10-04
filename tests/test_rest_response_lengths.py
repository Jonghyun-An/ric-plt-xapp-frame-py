# SPDX-License-Identifier: Apache-2.0
"""Check actual HTTP framing with text and binary responses over loopback TCP."""
import http.client

import pytest

from ricxappframe.xapp_rest import ThreadedHTTPServer, initResponse


@pytest.mark.parametrize("payload, mode, expected", [
    ("ASCII", "plain", b"ASCII"),
    ("한글", "plain", "한글".encode("utf-8")),
    ("π🙂", "plain", "π🙂".encode("utf-8")),
    ("", "plain", b""),
    (b"\x00\xff\x80", "binary", b"\x00\xff\x80"),
    (b"", "binary", b""),
])
def test_rest_response_byte_length(payload, mode, expected):
    server = ThreadedHTTPServer("127.0.0.1", 0)

    def respond(name, path, data, ctype):
        response = initResponse()
        response.update(payload=payload, mode=mode)
        return response

    server.handler.add_handler(server.handler, "GET", "byte-length", "/byte-length", respond)
    server.start()
    connection = http.client.HTTPConnection(*server.server.server_address, timeout=3)
    try:
        connection.request("GET", "/byte-length")
        response = connection.getresponse()
        body = response.read()
        assert response.status == 200
        assert body == expected
        assert response.getheader("Content-Length") == str(len(expected))
    finally:
        connection.close()
        server.stop()
