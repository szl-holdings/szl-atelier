# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app as module  # noqa: E402

client = TestClient(module.app)


def test_health_and_readiness(monkeypatch) -> None:
    monkeypatch.setenv("SOURCE_REVISION", "a" * 40)
    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.json() == {"status": "ok", "service": "szl-atelier-v3"}

    ready = client.get("/readyz")
    assert ready.status_code == 200
    assert ready.json()["status"] == "READY"
    assert ready.json()["missing"] == []
    assert ready.json()["source"]["witness"] == "environment"


def test_readiness_fails_closed_without_source_witness(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("SOURCE_REVISION", raising=False)
    monkeypatch.setattr(module, "SOURCE_FILE", tmp_path / "SOURCE_REVISION")
    ready = client.get("/readyz")
    assert ready.status_code == 503
    assert ready.json()["status"] == "NOT_READY"
    assert "SOURCE_REVISION" in ready.json()["missing"]


def test_source_revision_file_fallback(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("SOURCE_REVISION", raising=False)
    source_file = tmp_path / "SOURCE_REVISION"
    source_file.write_text("b" * 40 + "\n", encoding="ascii")
    monkeypatch.setattr(module, "SOURCE_FILE", source_file)
    assert module.source_revision() == {
        "state": "MEASURED",
        "revision": "b" * 40,
        "witness": "SOURCE_REVISION",
    }


def test_malformed_source_revision_file_is_unavailable(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("SOURCE_REVISION", raising=False)
    source_file = tmp_path / "SOURCE_REVISION"
    source_file.write_text("not-a-commit\n", encoding="ascii")
    monkeypatch.setattr(module, "SOURCE_FILE", source_file)
    assert module.source_revision() == {
        "state": "UNAVAILABLE",
        "revision": "UNAVAILABLE",
        "witness": "UNAVAILABLE",
    }


def test_catalog_is_deterministic_and_source_owned() -> None:
    first = client.get("/api/catalog")
    second = client.get("/api/catalog")
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    payload = first.json()
    assert payload["count"] == len(payload["items"])
    assert payload["count"] >= 6
    assert all(str(item["source_repository"]).startswith("szl-holdings/") for item in payload["items"])
    unsigned = dict(payload)
    digest = unsigned.pop("receipt_sha256")
    expected = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
    assert digest == expected


def test_filters_are_bounded() -> None:
    response = client.get("/api/catalog", params={"group": "flagships", "q": "A11oy"})
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["items"][0]["slug"] == "a11oy"
    assert client.get("/api/catalog", params={"group": "../secrets"}).status_code == 422
    assert client.get("/api/catalog", params={"q": "x" * 65}).status_code == 422


def test_artifact_detail_does_not_fetch_provider_by_default(monkeypatch) -> None:
    def forbidden(*_args, **_kwargs):
        raise AssertionError("provider network must not be used")

    monkeypatch.setattr(module, "fetch_provider", forbidden)
    response = client.get("/api/catalog/space/a11oy")
    assert response.status_code == 200
    assert response.json()["provider"]["state"] == "UNAVAILABLE"


def test_unknown_and_malformed_artifacts_fail_closed() -> None:
    assert client.get("/api/catalog/space/not-real").status_code == 404
    assert client.get("/api/catalog/space/%2e%2e").status_code in {404, 422}
    assert client.get("/api/catalog/unknown/a11oy").status_code == 404


def test_source_receipt_contains_no_environment_values(monkeypatch) -> None:
    monkeypatch.setenv("SOURCE_REVISION", "a" * 40)
    monkeypatch.setenv("HF_TOKEN", "hf_" + "x" * 40)
    response = client.get("/api/source")
    assert response.status_code == 200
    text = response.text
    assert "hf_" not in text
    payload = response.json()
    assert payload["source"] == {
        "state": "MEASURED",
        "revision": "a" * 40,
        "witness": "environment",
    }
    assert payload["mutation_authority"] is False
    assert payload["secrets_recorded"] is False


def test_security_headers_and_local_assets() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in response.headers["content-security-policy"]
    html = response.text
    assert "https://" not in html
    assert "http://" not in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert client.get("/app.js").status_code == 200
    assert client.get("/styles.css").status_code == 200


def test_provider_slug_and_kind_validation() -> None:
    for bad in ("owner", "../repo", "owner/repo/extra", "owner/<script>"):
        try:
            module.fetch_provider("model", bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"bad provider slug accepted: {bad}")
    try:
        module.fetch_provider("capability", "owner/repo")
    except ValueError:
        pass
    else:
        raise AssertionError("unsupported provider kind accepted")
