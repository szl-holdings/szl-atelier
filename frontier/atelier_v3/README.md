# SZL Atelier v3

A source-bound, read-only artifact constellation for the SZL Holdings public estate.

Atelier composes discovery. It does not become the source owner of the models, datasets, Spaces, delivery systems, or research records that it displays.

## Run locally

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r frontier/atelier_v3/requirements.txt
SOURCE_REVISION="$(git rev-parse HEAD)" \
  python -m uvicorn app:app --app-dir frontier/atelier_v3 --host 127.0.0.1 --port 7860
```

Open `http://127.0.0.1:7860`.

## API

| Route | Purpose |
|---|---|
| `GET /healthz` | Process liveness only |
| `GET /readyz` | Controlled-file availability and source identity |
| `GET /api/source` | Exact source revision, controlled-file hashes, and receipt |
| `GET /api/catalog` | Deterministic curated catalog with bounded filters |
| `GET /api/catalog/{kind}/{slug}` | Exact artifact evidence; provider readback is opt-in |

`live=true` is accepted only for curated model, dataset, or Space entries that carry an exact `SZLHOLDINGS/...` Hub identity. The adapter rejects redirects, arbitrary hosts, arbitrary URLs, oversized bodies, malformed JSON, unsupported kinds, and malformed slugs.

## Evidence states

- `DECLARED`: source-controlled metadata, not independently measured.
- `MEASURED`: observed by the bounded adapter during this response.
- `PARTIAL`: some required evidence exists and some is unavailable.
- `UNAVAILABLE`: not requested, not reachable, malformed, or otherwise not proven.

A provider readback does not prove model quality, benchmark validity, runtime source alignment, or deployment readiness.

## Authority boundary

The service exposes no POST, PUT, PATCH, or DELETE endpoint. It has no Hub token path, no repository token path, no model execution, no subprocess or shell execution, no arbitrary fetch target, no analytics, no cookies, and no browser persistence.

The state equation is deliberately non-collapsible:

```text
CLASSIFIED != UNARCHIVED != SOURCE_PR != MERGED != HUB_PUBLISHED != RUNTIME_READY != EXACT_READBACK_VERIFIED
```

## Container

```bash
docker build -f frontier/atelier_v3/Dockerfile -t szl-atelier-v3 .
docker run --rm -p 7860:7860 -e SOURCE_REVISION="$(git rev-parse HEAD)" szl-atelier-v3
```

The image runs as UID/GID `10001:10001`.

## Test

```bash
python -m pytest -q frontier/atelier_v3/tests
```
