# SPDX-License-Identifier: Apache-2.0
"""Atelier v3: bounded, read-only artifact evidence service."""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Final, Literal

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from catalog import catalog_rows, find_artifact

ROOT: Final = Path(__file__).resolve().parent
STATIC: Final = ROOT / "static"
CONTROLLED: Final = (
    ROOT / "app.py",
    ROOT / "catalog.py",
    STATIC / "index.html",
    STATIC / "app.js",
    STATIC / "styles.css",
)
SOURCE_RE = re.compile(r"^[0-9a-f]{40}$")
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}/[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
KINDS: Final = {"model": "models", "dataset": "datasets", "space": "spaces"}
MAX_PROVIDER_BYTES: Final = 512_000
PROVIDER_TIMEOUT_SECONDS: Final = 6.0
CACHE_TTL_SECONDS: Final = 120.0


class ProviderResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state: Literal["MEASURED", "UNAVAILABLE"]
    kind: Literal["model", "dataset", "space"]
    slug: str
    measured_at_unix: int
    payload: dict[str, Any] | None = None
    error: str | None = None
    receipt_sha256: str


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Reject redirects so the allowlisted provider host cannot drift."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise urllib.error.HTTPError(req.full_url, code, "redirect rejected", headers, fp)


_cache_lock = threading.Lock()
_cache: dict[tuple[str, str], tuple[float, ProviderResult]] = {}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def receipt(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def source_revision() -> dict[str, str]:
    raw = os.getenv("SOURCE_REVISION", "").strip().lower()
    if SOURCE_RE.fullmatch(raw):
        return {"state": "MEASURED", "revision": raw}
    return {"state": "UNAVAILABLE", "revision": "UNAVAILABLE"}


def controlled_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in CONTROLLED:
        relative = path.relative_to(ROOT).as_posix()
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "UNAVAILABLE"
    return hashes


def normalize_provider(kind: str, slug: str, raw: dict[str, Any]) -> dict[str, Any]:
    """Expose a small stable subset instead of relaying arbitrary provider JSON."""

    card_data = raw.get("cardData") if isinstance(raw.get("cardData"), dict) else {}
    siblings = raw.get("siblings") if isinstance(raw.get("siblings"), list) else []
    return {
        "id": raw.get("id") or raw.get("modelId") or slug,
        "kind": kind,
        "private": bool(raw.get("private", False)),
        "disabled": bool(raw.get("disabled", False)),
        "gated": raw.get("gated", False),
        "sha": raw.get("sha") if isinstance(raw.get("sha"), str) else None,
        "last_modified": raw.get("lastModified"),
        "likes": raw.get("likes") if isinstance(raw.get("likes"), int) else None,
        "downloads": raw.get("downloads") if isinstance(raw.get("downloads"), int) else None,
        "license": card_data.get("license") if isinstance(card_data.get("license"), str) else None,
        "pipeline_tag": raw.get("pipeline_tag") if isinstance(raw.get("pipeline_tag"), str) else None,
        "runtime_stage": raw.get("runtime", {}).get("stage") if isinstance(raw.get("runtime"), dict) else None,
        "files": sorted(
            item.get("rfilename")
            for item in siblings[:200]
            if isinstance(item, dict) and isinstance(item.get("rfilename"), str)
        ),
    }


def fetch_provider(kind: str, slug: str) -> ProviderResult:
    if kind not in KINDS or not SLUG_RE.fullmatch(slug):
        raise ValueError("provider identity is outside the exact allowlist shape")
    cache_key = (kind, slug)
    now_mono = time.monotonic()
    with _cache_lock:
        cached = _cache.get(cache_key)
        if cached and now_mono - cached[0] < CACHE_TTL_SECONDS:
            return cached[1]

    quoted_slug = "/".join(urllib.parse.quote(part, safe="") for part in slug.split("/", 1))
    url = f"https://huggingface.co/api/{KINDS[kind]}/{quoted_slug}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "szl-atelier-v3/1.0",
        },
        method="GET",
    )
    measured_at = int(time.time())
    try:
        opener = urllib.request.build_opener(NoRedirect())
        with opener.open(request, timeout=PROVIDER_TIMEOUT_SECONDS) as response:
            final = urllib.parse.urlsplit(response.geturl())
            if final.scheme != "https" or final.hostname != "huggingface.co":
                raise ValueError("provider origin drifted")
            body = response.read(MAX_PROVIDER_BYTES + 1)
            if len(body) > MAX_PROVIDER_BYTES:
                raise ValueError("provider response exceeded byte limit")
            raw = json.loads(body.decode("utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("provider response was not an object")
            payload = normalize_provider(kind, slug, raw)
            result = ProviderResult(
                state="MEASURED",
                kind=kind,
                slug=slug,
                measured_at_unix=measured_at,
                payload=payload,
                receipt_sha256=receipt(payload),
            )
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        public_error = f"{type(exc).__name__}: provider evidence unavailable"[:160]
        result = ProviderResult(
            state="UNAVAILABLE",
            kind=kind,
            slug=slug,
            measured_at_unix=measured_at,
            error=public_error,
            receipt_sha256=receipt({"kind": kind, "slug": slug, "state": "UNAVAILABLE", "measured_at_unix": measured_at}),
        )
    with _cache_lock:
        _cache[cache_key] = (now_mono, result)
    return result


app = FastAPI(
    title="SZL Atelier v3",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)


@app.middleware("http")
async def security_headers(request: Request, call_next):  # noqa: ANN001
    response: Response = await call_next(request)
    response.headers.update(
        {
            "Cache-Control": "no-store" if request.url.path.startswith("/api/") else "public, max-age=300",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        }
    )
    return response


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "szl-atelier-v3"}


@app.get("/readyz")
def readyz(response: Response) -> dict[str, Any]:
    missing = [path.relative_to(ROOT).as_posix() for path in CONTROLLED if not path.is_file()]
    state = "READY" if not missing else "NOT_READY"
    if missing:
        response.status_code = 503
    return {"status": state, "missing": missing, "source": source_revision()}


@app.get("/api/source")
def source() -> dict[str, Any]:
    value = {
        "schema": "szl.atelier-source/v1",
        "repository": "szl-holdings/szl-atelier",
        "source": source_revision(),
        "controlled_files": controlled_hashes(),
        "provider_authority": "Hugging Face public read-only metadata API",
        "mutation_authority": False,
        "secrets_recorded": False,
    }
    value["receipt_sha256"] = receipt(value)
    return value


@app.get("/api/catalog")
def catalog(
    group: str | None = Query(default=None, max_length=48, pattern=r"^[a-z0-9-]+$"),
    kind: str | None = Query(default=None, max_length=16, pattern=r"^[a-z-]+$"),
    q: str | None = Query(default=None, max_length=64),
) -> dict[str, Any]:
    rows = catalog_rows()
    if group:
        rows = [row for row in rows if row["group"] == group]
    if kind:
        rows = [row for row in rows if row["kind"] == kind]
    if q:
        needle = q.casefold().strip()
        rows = [row for row in rows if needle in f"{row['slug']} {row['title']} {row['summary']}".casefold()]
    rows.sort(key=lambda row: (str(row["group"]), str(row["kind"]), str(row["slug"])))
    value = {"schema": "szl.atelier-catalog/v1", "count": len(rows), "items": rows}
    value["receipt_sha256"] = receipt(value)
    return value


@app.get("/api/catalog/{kind}/{slug}")
def artifact(kind: str, slug: str, live: bool = Query(default=False)) -> dict[str, Any]:
    if kind not in {"model", "dataset", "space", "capability", "research"}:
        raise HTTPException(status_code=404, detail="unknown artifact kind")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", slug):
        raise HTTPException(status_code=404, detail="unknown artifact")
    item = find_artifact(kind, slug)
    if item is None:
        raise HTTPException(status_code=404, detail="unknown artifact")
    provider: dict[str, Any] = {"state": "UNAVAILABLE", "reason": "live provider readback not requested"}
    if live and kind in KINDS and item.hub_slug:
        provider = fetch_provider(kind, item.hub_slug).model_dump(mode="json")
    value = {"schema": "szl.atelier-artifact/v1", "artifact": item.public(), "provider": provider}
    value["receipt_sha256"] = receipt(value)
    return value


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html", media_type="text/html")


@app.get("/app.js")
def javascript() -> FileResponse:
    return FileResponse(STATIC / "app.js", media_type="text/javascript")


@app.get("/styles.css")
def stylesheet() -> FileResponse:
    return FileResponse(STATIC / "styles.css", media_type="text/css")


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"status": "ERROR", "detail": exc.detail})
