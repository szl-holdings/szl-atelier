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

This repository retains a legacy gallery of 40 curated records, GitHub-aligned Python, and browser kernel playgrounds. Its catalog is separate from the current [public SZLHOLDINGS Hub inventory](https://huggingface.co/SZLHOLDINGS).

The active [SZLHOLDINGS/szl-atelier Space](https://huggingface.co/spaces/SZLHOLDINGS/szl-atelier) serves artifact discovery and evidence review from [`frontier/atelier_v3`](frontier/atelier_v3/README.md). Its [publication contract](frontier/atelier_v3/PUBLICATION.json) maps nine controlled files from that directory. The root gallery files documented below are outside that projection.

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

## The cut

Anthropic taught refuse. NVIDIA taught kernels and joules. Unsloth taught cheap QLoRA. SZL spends all three on a typed plan, a fail-closed gate, and a training receipt you can verify without trusting us.

## Legacy evidence labels

These labels are retained from the legacy catalog. They do not qualify current public Hub models or the active v3 Space.

| Claim | Existing legacy label |
|---|---|
| 40 curated catalog records | CATALOG |
| Python API and readiness contract | RUNTIME-OBSERVED only when `/readyz` returns 200 |
| Nano silhouettes (moons, embed, tiny-khipu, receipt, λ*) | MEASURED in the legacy gallery |
| SZL-Khipu-1.5B plan-valid 11/11, grounding 4/5, abstain 2/6, hallu 0 | SIGNED — not retrained here |
| MiniEmbed hit@2 0.40 | SAMPLE on five pairs. Hub analogy UNAVAILABLE |
| Λ uniqueness | Conjecture 1 OPEN |
| Energy / CUDA | UNAVAILABLE |
| GGUF | derived, never the signed object |

Doctrine v11 LOCKED · 749/14/163 · locked-proven 8. Apache-2.0. Copyright 2026 SZL Holdings · Stephen P. Lutar Jr. · ORCID [0009-0001-0110-4173](https://orcid.org/0009-0001-0110-4173).
