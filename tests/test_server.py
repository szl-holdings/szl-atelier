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


def test_readiness_requires_full_catalog_and_capability_fabric():
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["catalog_records"] == 40
    assert response.json()["capability_records"] == 2
    assert response.json()["errors"] == []


def test_catalog_and_build_info_are_runtime_observable():
    catalog = client.get("/api/catalog")
    build = client.get("/api/build-info")
    assert catalog.status_code == 200
    assert build.status_code == 200
    assert build.json()["status"] == "RUNTIME_OBSERVED"
    assert build.json()["catalog_records"] == 40
    assert build.json()["capability_records"] == 2
    assert len(build.json()["release_manifest_sha256"]) == 64
    assert build.json()["receipt_persistence"] == "NOT_CONFIGURED"
    assert build.json()["capability_source_authority"] == "EXTERNAL_REPOSITORIES"
    assert build.json()["capability_hub_publication"].startswith("UNAVAILABLE_")
    assert build.json()["capability_runtime_source_match"].startswith("UNAVAILABLE_")


def test_capability_fabric_preserves_source_and_provider_truth_boundaries():
    response = client.get("/api/capabilities")
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema"] == "szl.atelier.capability-fabric/v1"
    assert payload["status"] == "SOURCE_MERGED_HUB_RUNTIME_UNVERIFIED"
    assert payload["presentation_owner"] == "szl-holdings/szl-atelier"
    assert payload["truth_boundary"] == (
        "SOURCE_MERGED != HUB_PUBLISHED != RUNTIME_READY != EXACT_SOURCE_MATCH"
    )

    items = payload["items"]
    assert len(items) == 2
    assert {item["slug"] for item in items} == {
        "uds-bundle-observatory",
        "mesh-convergence-lab",
    }
    assert {item["source_repository"] for item in items} == {
        "szl-holdings/uds-bundles",
        "szl-holdings/szl-mesh",
    }
    for item in items:
        assert item["source_state"] == "MERGED"
        assert len(item["introduced_revision"]) == 40
        assert all(character in "0123456789abcdef" for character in item["introduced_revision"])
        assert item["source_url"].startswith("https://github.com/szl-holdings/")
        assert item["hub_target"] == "SZLHOLDINGS/szl-atelier"
        assert item["hub_publication_state"].startswith("UNAVAILABLE_")
        assert item["runtime_state"].startswith("UNAVAILABLE_")
        assert item["commercial_role"] == "CAPABILITY_NOT_PEER_FLAGSHIP"
        assert item["measured_properties"]
        assert item["excluded_authority"]


def test_capability_detail_is_exact_and_unknown_slug_fails_closed():
    uds = client.get("/api/capabilities/uds-bundle-observatory")
    mesh = client.get("/api/capabilities/mesh-convergence-lab")
    missing = client.get("/api/capabilities/not-a-capability")
    malformed = client.get("/api/capabilities/UPPERCASE")

    assert uds.status_code == 200
    assert uds.json()["source_repository"] == "szl-holdings/uds-bundles"
    assert uds.json()["source_pull_request"] == 47
    assert mesh.status_code == 200
    assert mesh.json()["source_repository"] == "szl-holdings/szl-mesh"
    assert mesh.json()["source_pull_request"] == 39
    assert missing.status_code == 404
    assert missing.json()["detail"] == "CAPABILITY_NOT_FOUND"
    assert malformed.status_code == 404


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
    assert 'id="capability-fabric"' in index.text
    assert 'src="./capability-fabric.js"' in index.text
    assert 'href="./capability-fabric.css"' in index.text
    assert client.get("/frontier-worker.js").status_code == 200
    assert client.get("/capability-fabric.js").status_code == 200
    assert client.get("/capability-fabric.css").status_code == 200
    assert client.get("/capabilities.json").status_code == 200
    assert client.get("/server.py").status_code == 404
    assert client.get("/.git/config").status_code == 404


def test_capability_frontend_uses_same_origin_api_and_no_browser_storage():
    javascript = client.get("/capability-fabric.js").text
    assert 'fetch("/api/capabilities"' in javascript
    assert 'fetch("http://' not in javascript
    assert 'fetch("https://' not in javascript
    assert "fetch('http://" not in javascript
    assert "fetch('https://" not in javascript
    assert "localStorage" not in javascript
    assert "sessionStorage" not in javascript
    assert "document.cookie" not in javascript
    assert "innerHTML" not in javascript
    assert "textContent" in javascript
