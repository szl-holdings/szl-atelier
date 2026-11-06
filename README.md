---
title: SZL Atelier
emoji: 🪢
colorFrom: gray
colorTo: green
sdk: docker
app_port: 7860
suggested_hardware: cpu-basic
pinned: true
license: apache-2.0
short_description: Legacy gallery of 40 curated records. Unique cuts.
tags:
  - governed-ai
  - szl-holdings
  - doctrine-v11
  - model-card
  - receipts
  - docker
  - fastapi
  - python
models: [SZLHOLDINGS/SZL-Khipu-1.5B, SZLHOLDINGS/SZL-Khipu-1.5B-GGUF, SZLHOLDINGS/SZL-Forge-1.5B-ReceiptAgent, SZLHOLDINGS/chaski, SZLHOLDINGS/MiniEmbed-Nano, SZLHOLDINGS/Moons-Nano, SZLHOLDINGS/TinyKhipu-Nano, SZLHOLDINGS/ReceiptAgent-Nano]
datasets: [SZLHOLDINGS/szl-lake]
---

# SZL Atelier

<!-- szl:header v1 -->
<!-- Native identity: szl-brand@4309f6fce89179331b0b3ed8c99494e76c5be256; Orbit v2 icon. -->
<p>
  <a href="https://github.com/szl-holdings">
    <img src="https://raw.githubusercontent.com/szl-holdings/szl-brand/4309f6fce89179331b0b3ed8c99494e76c5be256/kit/logos/orbit-v2/suite/szl-icon-32.svg" alt="SZL Holdings — Orbit v2" width="32" height="32" />
  </a>
</p>

**Control before action. Evidence after.**

[Product](https://a-11-oy.com) · [Proof](https://a11oy.net) · [GitHub organization](https://github.com/szl-holdings)
<!-- /szl:header -->

This repository retains a legacy gallery of 40 curated records, GitHub-aligned Python, and browser kernel playgrounds. Its catalog is separate from the current [public SZLHOLDINGS Hub inventory](https://huggingface.co/SZLHOLDINGS).

The active [SZLHOLDINGS/szl-atelier Space](https://huggingface.co/spaces/SZLHOLDINGS/szl-atelier) serves artifact discovery and evidence review from [`frontier/atelier_v3`](frontier/atelier_v3/README.md). Its [publication contract](frontier/atelier_v3/PUBLICATION.json) maps nine controlled files from that directory. The root gallery files documented below are outside that projection.

> **Space visibility (observed 2026-11-06).** The Hub reports this Space as private, so the link answers HTTP 401 to anonymous visitors. a11oy's `publishing/space-fold-registry.json` marks it `FOLD` (pending) into [a11oy.net/atelier](https://a11oy.net/atelier/), while the lifecycle policy in `szl-holdings/.github` still declares it public. Until the owner settles that, the `hf-space` publisher cannot complete its anonymous runtime readback.

YAML `emoji` is Hub metadata, not product chrome. System fonts. No Google Fonts. Gold is OPEN. Never green-as-proven. Never a fabricated joule.

**Legacy root runtime:** Docker/FastAPI for the curated gallery. The canonical Space uses the separate v3 projection linked above.

| Origin | Role |
|---|---|
| [szl-holdings/szl-atelier](https://github.com/szl-holdings/szl-atelier) | Source of the legacy gallery and separate active v3 Space projection |
| [a11oy.net/atelier](https://a11oy.net/atelier/) | Curated legacy gallery on the proof registry |
| [a-11-oy.com/atelier](https://a-11-oy.com/atelier) | Product surface |
| [SZLHOLDINGS/szl-khipu](https://huggingface.co/spaces/SZLHOLDINGS/szl-khipu) | Sibling Gradio hologram |

## Legacy gallery runtime contract

In the root Docker/FastAPI runtime, the gallery frontend and Python backend are served from one origin. `/healthz` proves that the FastAPI process is responding; `/readyz` fails closed unless the catalog and release manifest are present and the expected 40 records load; `/api/build-info` reports hashes for the bytes served by the container. `/api/frontier/verify` validates the structure and scope of browser-generated frontier receipts without pretending that a local measurement is a production deployment or a cryptographic signature.

Receipt persistence is **NOT CONFIGURED**. Verification requests are not stored. Provider repository state and served runtime state remain separate evidence and are checked during release.

## Run locally

`server.py` serves the gallery files that sit next to it, so run it from a checkout (Python 3.12 or newer):

```bash
python -m venv .venv && . .venv/bin/activate
python -m pip install -e '.[test]'
python -m uvicorn server:app --host 127.0.0.1 --port 7860
curl -s http://127.0.0.1:7860/readyz
# {"status":"ready","service":"szl-atelier-api","catalog_records":40,"errors":[]}
```

The v3 Space application has its own pins and run instructions in [`frontier/atelier_v3/README.md`](frontier/atelier_v3/README.md); the `kit/` scripts are described in [`kit/README.md`](kit/README.md).

## Test

```bash
python -m pytest -q    # tests/ and frontier/atelier_v3/tests
node --test frontier/atelier_v3/tests/provider_readback.test.cjs
```

CI installs hash locks rather than ranges: `requirements/ci/runtime-contract.txt` for `ci.yml` (which also builds and smoke-tests the Docker image), `requirements/ci/atelier-v3.txt` for the v3 qualification and the Space writer, and `requirements/docker/runtime.txt` inside the root image. Each lock records the `uv pip compile` command that regenerates it.

## The cut

Anthropic taught refuse. NVIDIA taught kernels and joules. Unsloth taught cheap QLoRA. SZL spends all three on a typed plan, a fail-closed gate, and a training receipt you can verify without trusting us.

## Legacy evidence labels

These labels are retained from the legacy catalog. They do not qualify current public Hub models or the active v3 Space.

| Claim | Existing legacy label |
|---|---|
| 40 curated catalog records | CATALOG |
| Python API and readiness contract | RUNTIME-OBSERVED only when `/readyz` returns 200 |
| Nano silhouettes (moons, embed, λ*) | MEASURED in the legacy gallery |
| Nano silhouettes (tiny-khipu, receipt) | SYNTHETIC: holdout 1.00 on data separable by design |
| SZL-Khipu-1.5B owner-run eval (2026-07-14): plan-valid 11/11, grounding 4/5, abstain 2/6 (blocker), 0 hallucinated citations on 11 named cases | REPORTED from the owner-signed eval receipt; not re-run or retrained here |
| MiniEmbed hit@2 0.40 | SAMPLE on five pairs. Hub analogy UNAVAILABLE |
| Λ uniqueness | Conjecture 1 OPEN |
| Energy / CUDA | UNAVAILABLE |
| GGUF | derived, never the signed object |

## Proof boundary

What this repository's CI checks: the root runtime loads all 40 catalog records and fails readiness closed otherwise, both on the runner and inside the shipped image; frontier receipts are checked for structure and scope only; the v3 package is built byte-for-byte from one GitHub commit, and the publisher refuses drift between that package, the Hub commit and the running Space.

What it does not establish: model quality or benchmark validity for any catalog entry; that the Hub Space currently runs a given commit (only an `hf-space` run ending in `EXACT_READBACK_VERIFIED` shows that); cryptographic signatures on browser receipts; any energy figure.

Doctrine v11 LOCKED · 749/14/163 · locked-proven 8. Apache-2.0. Copyright 2026 SZL Holdings · Stephen P. Lutar Jr. · ORCID [0009-0001-0110-4173](https://orcid.org/0009-0001-0110-4173).
