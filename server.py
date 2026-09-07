from __future__ import annotations

import hashlib
import json
import os
import platform
import re
from datetime import datetime, timezone
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

ROOT = Path(__file__).resolve().parent
MAX_BODY_BYTES = 128 * 1024
STARTED_AT = datetime.now(timezone.utc).isoformat()
CAPABILITY_SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")

PUBLIC_ROOT_FILES = frozenset(
    {
        "index.html",
        "app.js",
        "backend-status.js",
        "capability-fabric.js",
        "capability-fabric.css",
        "capabilities.json",
        "frontier.js",
        "frontier-worker.js",
        "style.css",
        "styles.css",
        "models.json",
        "nano-weights.json",
        "unsloth-recipes.json",
        "RELEASE.json",
        "SPACE_PROVENANCE_FRONTIER.json",
        "GOVERNANCE.md",
        "README.md",
        "LICENSE",
    }
)
PUBLIC_DIRECTORIES = frozenset({"cards", "kit", "weights"})
HASHED_ARTIFACTS = (
    "index.html",
    "app.js",
    "backend-status.js",
    "capability-fabric.js",
    "capability-fabric.css",
    "capabilities.json",
    "frontier.js",
    "frontier-worker.js",
    "styles.css",
    "models.json",
    "unsloth-recipes.json",
    "RELEASE.json",
)

startup_errors: list[str] = []


def load_json(name: str) -> Any:
    try:
        return json.loads((ROOT / name).read_text(encoding="utf-8"))
    except (OSError, JSONDecodeError) as exc:
        startup_errors.append(f"{name}:{type(exc).__name__}")
        return None


CATALOG = load_json("models.json")
CAPABILITIES = load_json("capabilities.json")
RELEASE = load_json("RELEASE.json")


def catalog_record_count(catalog: Any) -> int:
    if isinstance(catalog, list):
        return len(catalog)
    if isinstance(catalog, dict):
        for key in ("models", "items", "catalog"):
            records = catalog.get(key)
            if isinstance(records, list):
                return len(records)
    return 0


def capability_items(capabilities: Any) -> list[dict[str, Any]]:
    if not isinstance(capabilities, dict):
        return []
    items = capabilities.get("items")
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def capability_record_count(capabilities: Any) -> int:
    return len(capability_items(capabilities))


def capability_contract_errors(capabilities: Any) -> list[str]:
    if not isinstance(capabilities, dict):
        return ["capabilities.json:ROOT_NOT_OBJECT"]
    if capabilities.get("schema") != "szl.atelier.capability-fabric/v1":
        return ["capabilities.json:SCHEMA_MISMATCH"]
    raw_items = capabilities.get("items")
    if not isinstance(raw_items, list):
        return ["capabilities.json:ITEMS_NOT_ARRAY"]

    errors: list[str] = []
    seen: set[str] = set()
    required_keys = {
        "slug",
        "name",
        "category",
        "one_liner",
        "source_repository",
        "introduced_revision",
        "source_pull_request",
        "source_path",
        "source_state",
        "source_url",
        "api",
        "measured_properties",
        "excluded_authority",
        "audiences",
        "hub_target",
        "hub_publication_state",
        "runtime_state",
        "commercial_role",
    }
    for index, item in enumerate(raw_items):
        prefix = f"capabilities.json:ITEM_{index}"
        if not isinstance(item, dict):
            errors.append(f"{prefix}_NOT_OBJECT")
            continue
        missing = sorted(required_keys - set(item))
        if missing:
            errors.append(f"{prefix}_MISSING_{'_'.join(missing)}")
        slug = item.get("slug")
        if not isinstance(slug, str) or not CAPABILITY_SLUG_RE.fullmatch(slug):
            errors.append(f"{prefix}_SLUG_INVALID")
        elif slug in seen:
            errors.append(f"{prefix}_SLUG_DUPLICATE")
        else:
            seen.add(slug)
        revision = item.get("introduced_revision")
        if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
            errors.append(f"{prefix}_REVISION_INVALID")
        if item.get("source_state") != "MERGED":
            errors.append(f"{prefix}_SOURCE_STATE_UNVERIFIED")
        if not str(item.get("source_repository", "")).startswith("szl-holdings/"):
            errors.append(f"{prefix}_SOURCE_REPOSITORY_INVALID")
        if not str(item.get("source_url", "")).startswith(
            "https://github.com/szl-holdings/"
        ):
            errors.append(f"{prefix}_SOURCE_URL_INVALID")
        if not str(item.get("hub_publication_state", "")).startswith("UNAVAILABLE_"):
            errors.append(f"{prefix}_HUB_STATE_OVERCLAIM")
        if not str(item.get("runtime_state", "")).startswith("UNAVAILABLE_"):
            errors.append(f"{prefix}_RUNTIME_STATE_OVERCLAIM")
        for key in ("api", "measured_properties", "excluded_authority", "audiences"):
            values = item.get(key)
            if not isinstance(values, list) or not values or not all(
                isinstance(value, str) and value.strip() for value in values
            ):
                errors.append(f"{prefix}_{key.upper()}_INVALID")
    return errors


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def readiness_errors() -> list[str]:
    errors = list(startup_errors)
    required = (
        "index.html",
        "models.json",
        "capabilities.json",
        "capability-fabric.js",
        "capability-fabric.css",
        "RELEASE.json",
        "backend-status.js",
    )
    errors.extend(f"{name}:MISSING" for name in required if not (ROOT / name).is_file())

    expected_catalog = 40
    expected_capabilities = 2
    if isinstance(RELEASE, dict):
        expected_catalog = int(
            (RELEASE.get("catalog") or {}).get("expected_records", expected_catalog)
        )
        expected_capabilities = int(
            (RELEASE.get("capabilities") or {}).get(
                "expected_records", expected_capabilities
            )
        )

    observed_catalog = catalog_record_count(CATALOG)
    if observed_catalog != expected_catalog:
        errors.append(
            f"models.json:EXPECTED_{expected_catalog}_OBSERVED_{observed_catalog}"
        )

    observed_capabilities = capability_record_count(CAPABILITIES)
    if observed_capabilities != expected_capabilities:
        errors.append(
            "capabilities.json:"
            f"EXPECTED_{expected_capabilities}_OBSERVED_{observed_capabilities}"
        )
    errors.extend(capability_contract_errors(CAPABILITIES))
    return errors


def observed_source_revision() -> dict[str, Any]:
    for env_name in ("SPACE_COMMIT_SHA", "HF_SPACE_SHA", "GIT_COMMIT"):
        value = os.getenv(env_name, "").strip()
        if value:
            return {
                "status": "OBSERVED_ENVIRONMENT_CLAIM",
                "value": value,
                "source": env_name,
                "meaning": "Must be corroborated against provider state.",
            }
    return {
        "status": "UNAVAILABLE",
        "value": None,
        "source": None,
        "meaning": "Hugging Face does not document a served commit SHA runtime variable.",
    }


def build_information() -> dict[str, Any]:
    artifacts: dict[str, str] = {}
    unavailable: list[str] = []
    for name in HASHED_ARTIFACTS:
        path = ROOT / name
        if path.is_file():
            artifacts[name] = sha256_file(path)
        else:
            unavailable.append(name)
    manifest_hash = artifacts.get("RELEASE.json")
    return {
        "status": "RUNTIME_OBSERVED",
        "service": "szl-atelier-api",
        "backend": "python-fastapi",
        "python": platform.python_version(),
        "started_at": STARTED_AT,
        "space": {
            "id": os.getenv("SPACE_ID") or "LOCAL_OR_UNAVAILABLE",
            "host": os.getenv("SPACE_HOST") or "LOCAL_OR_UNAVAILABLE",
        },
        "source_revision": observed_source_revision(),
        "release_manifest_sha256": manifest_hash,
        "served_artifacts_sha256": artifacts,
        "unavailable_artifacts": unavailable,
        "catalog_records": catalog_record_count(CATALOG),
        "capability_records": capability_record_count(CAPABILITIES),
        "capability_source_authority": "EXTERNAL_REPOSITORIES",
        "capability_hub_publication": "UNAVAILABLE_REQUIRES_EXTERNAL_READBACK",
        "capability_runtime_source_match": "UNAVAILABLE_REQUIRES_EXTERNAL_READBACK",
        "receipt_persistence": "NOT_CONFIGURED",
        "provider_repository_head": "MUST_BE_OBSERVED_EXTERNALLY",
        "release": RELEASE,
    }


app = FastAPI(
    title="SZL Atelier Runtime",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)


@app.middleware("http")
async def runtime_contract_headers(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_BODY_BYTES:
        response = JSONResponse(
            status_code=413,
            content={"status": "rejected", "reason": "REQUEST_BODY_TOO_LARGE"},
        )
    else:
        response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "base-uri 'none'; "
        "connect-src 'self'; "
        "font-src 'self'; "
        "frame-ancestors 'self' https://huggingface.co https://*.huggingface.co; "
        "img-src 'self' data:; "
        "object-src 'none'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "worker-src 'self' blob:"
    )
    response.headers["X-SZL-Backend"] = "python-fastapi"
    response.headers["Cache-Control"] = (
        "no-store"
        if request.url.path in {"/", "/healthz", "/readyz"}
        or request.url.path.startswith("/api/")
        else "public, max-age=300"
    )
    return response


@app.get("/healthz")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "szl-atelier-api",
        "backend": "python-fastapi",
    }


@app.get("/readyz")
def ready():
    errors = readiness_errors()
    payload: dict[str, Any] = {
        "status": "ready" if not errors else "not_ready",
        "service": "szl-atelier-api",
        "catalog_records": catalog_record_count(CATALOG),
        "capability_records": capability_record_count(CAPABILITIES),
        "errors": errors,
    }
    return JSONResponse(status_code=200 if not errors else 503, content=payload)


@app.get("/api/catalog")
def catalog():
    if CATALOG is None:
        raise HTTPException(status_code=503, detail="CATALOG_UNAVAILABLE")
    return JSONResponse(content=CATALOG)


@app.get("/api/capabilities")
def capabilities():
    if capability_contract_errors(CAPABILITIES):
        raise HTTPException(status_code=503, detail="CAPABILITY_FABRIC_UNAVAILABLE")
    return JSONResponse(content=CAPABILITIES)


@app.get("/api/capabilities/{slug}")
def capability(slug: str):
    if not CAPABILITY_SLUG_RE.fullmatch(slug):
        raise HTTPException(status_code=404, detail="CAPABILITY_NOT_FOUND")
    if capability_contract_errors(CAPABILITIES):
        raise HTTPException(status_code=503, detail="CAPABILITY_FABRIC_UNAVAILABLE")
    item = next(
        (row for row in capability_items(CAPABILITIES) if row.get("slug") == slug),
        None,
    )
    if item is None:
        raise HTTPException(status_code=404, detail="CAPABILITY_NOT_FOUND")
    return JSONResponse(content=item)


@app.get("/api/build-info")
def build_info():
    return JSONResponse(content=build_information())


@app.post("/api/frontier/verify")
async def verify_frontier_receipt(request: Request):
    raw = await request.body()
    if len(raw) > MAX_BODY_BYTES:
        raise HTTPException(status_code=413, detail="REQUEST_BODY_TOO_LARGE")
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, JSONDecodeError):
        raise HTTPException(status_code=400, detail="INVALID_JSON") from None

    receipt = payload.get("receipt") if isinstance(payload, dict) else None
    if receipt is None:
        receipt = payload
    if not isinstance(receipt, dict):
        raise HTTPException(status_code=422, detail="RECEIPT_MUST_BE_AN_OBJECT")
    if receipt.get("status") != "MEASURED_LOCAL":
        raise HTTPException(status_code=422, detail="STATUS_MUST_BE_MEASURED_LOCAL")

    limitations = receipt.get("limitations")
    has_limitations = (
        isinstance(limitations, str)
        and bool(limitations.strip())
        or isinstance(limitations, list)
        and any(isinstance(item, str) and item.strip() for item in limitations)
    )
    if not has_limitations:
        raise HTTPException(status_code=422, detail="LIMITATIONS_REQUIRED")

    canonical = json.dumps(
        receipt,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "verification_status": "VERIFIED_STRUCTURE",
        "receipt_sha256": hashlib.sha256(canonical).hexdigest(),
        "claim_scope": "LOCAL_BROWSER_EXPERIMENT",
        "cryptographic_signature": "NOT_PROVIDED",
        "deployment_claim": "NOT_VERIFIED",
        "persistence": "NOT_PERSISTED",
    }


@app.get("/")
def index():
    return FileResponse(ROOT / "index.html")


@app.get("/{asset_path:path}", include_in_schema=False)
def public_asset(asset_path: str):
    if not asset_path or any(part.startswith(".") for part in Path(asset_path).parts):
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    candidate = (ROOT / asset_path).resolve()
    try:
        candidate.relative_to(ROOT)
    except ValueError:
        raise HTTPException(status_code=404, detail="NOT_FOUND") from None
    first_part = Path(asset_path).parts[0]
    allowed = asset_path in PUBLIC_ROOT_FILES or first_part in PUBLIC_DIRECTORIES
    if not allowed or not candidate.is_file():
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return FileResponse(candidate)
