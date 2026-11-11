# SPDX-License-Identifier: Apache-2.0
"""Real HTTP parsing of offline provider responses at the application boundary."""
from __future__ import annotations

import http.client
import io
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app as module  # noqa: E402


class WireSocket:
    def __init__(self, wire: bytes):
        self.wire = wire

    def makefile(self, *_args, **_kwargs):
        return io.BytesIO(self.wire)


class WireOpener:
    def __init__(self, wire: bytes):
        self.wire = wire

    def open(self, request, timeout):
        assert timeout == module.PROVIDER_TIMEOUT_SECONDS
        response = http.client.HTTPResponse(WireSocket(self.wire))
        response.url = request.full_url
        response.begin()
        return response


@pytest.mark.parametrize("wire,error_name", [
    (b"", "RemoteDisconnected"),
    (b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n20\r\nsecret-wire-bytes",
     "IncompleteRead"),
])
def test_interrupted_provider_is_unavailable(monkeypatch, wire, error_name):
    monkeypatch.setattr(module, "_cache", {})
    monkeypatch.setattr(module.urllib.request, "build_opener", lambda *_: WireOpener(wire))
    client = TestClient(module.app, raise_server_exceptions=False)
    response = client.get("/api/catalog/space/a11oy", params={"live": "true"})
    assert response.status_code == 200
    value = response.json()
    provider = value["provider"]
    assert provider["state"] == "UNAVAILABLE"
    assert provider["payload"] is None
    assert provider["error"] == f"{error_name}: provider evidence unavailable"
    assert "secret-wire-bytes" not in response.text
    assert provider["receipt_sha256"] == module.receipt({
        "kind": provider["kind"], "slug": provider["slug"], "state": "UNAVAILABLE",
        "measured_at_unix": provider["measured_at_unix"],
    })
    digest = value.pop("receipt_sha256")
    assert digest == module.receipt(value)


def test_complete_provider_response_remains_measured(monkeypatch):
    body = json.dumps({"id": "SZLHOLDINGS/a11oy", "sha": "a" * 40}).encode()
    wire = b"HTTP/1.1 200 OK\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body
    monkeypatch.setattr(module, "_cache", {})
    monkeypatch.setattr(module.urllib.request, "build_opener", lambda *_: WireOpener(wire))
    result = module.fetch_provider("space", "SZLHOLDINGS/a11oy")
    assert result.state == "MEASURED"
    assert result.payload["sha"] == "a" * 40
    assert result.error is None
    assert result.receipt_sha256 == module.receipt(result.payload)
