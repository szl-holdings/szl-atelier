from fastapi.testclient import TestClient

from server import app

client = TestClient(app)


def test_health_and_security_headers():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "szl-atelier-api",
        "backend": "python-fastapi",
    }
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-szl-backend"] == "python-fastapi"


def test_readiness_requires_full_catalog():
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["catalog_records"] == 40
    assert response.json()["errors"] == []


def test_catalog_and_build_info_are_runtime_observable():
    catalog = client.get("/api/catalog")
    build = client.get("/api/build-info")
    assert catalog.status_code == 200
    assert build.status_code == 200
    assert build.json()["status"] == "RUNTIME_OBSERVED"
    assert build.json()["catalog_records"] == 40
    assert len(build.json()["release_manifest_sha256"]) == 64
    assert build.json()["receipt_persistence"] == "NOT_CONFIGURED"


def test_frontier_receipt_scope_is_fail_closed():
    valid = client.post(
        "/api/frontier/verify",
        json={
            "receipt": {
                "status": "MEASURED_LOCAL",
                "limitations": ["Browser experiment; no production claim."],
                "metrics": {"coverage": 0.5},
            }
        },
    )
    assert valid.status_code == 200
    assert valid.json()["verification_status"] == "VERIFIED_STRUCTURE"
    assert valid.json()["persistence"] == "NOT_PERSISTED"

    overclaim = client.post(
        "/api/frontier/verify",
        json={"status": "PRODUCTION_PROVEN", "limitations": ["none"]},
    )
    assert overclaim.status_code == 422
    assert overclaim.json()["detail"] == "STATUS_MUST_BE_MEASURED_LOCAL"


def test_only_allowlisted_static_assets_are_served():
    index = client.get("/")
    assert index.status_code == 200
    assert "backend-status.js" in index.text
    assert client.get("/frontier-worker.js").status_code == 200
    assert client.get("/server.py").status_code == 404
    assert client.get("/.git/config").status_code == 404

