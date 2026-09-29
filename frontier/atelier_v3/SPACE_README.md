---
title: SZL Atelier
emoji: 🧵
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: true
license: apache-2.0
short_description: Source-bound discovery for SZL models, data, and Spaces.
---

# SZL Atelier

A governed artifact constellation for the SZL Holdings public estate.

Atelier presents source ownership, declared Hub identity, controlled-file commitments, and bounded public provider evidence. It does not execute models, mutate Hugging Face, copy source authority, or turn a declared artifact into a runtime-success claim.

## Evidence contract

```text
SOURCE_PR
!= MERGED
!= HUB_PUBLISHED
!= RUNTIME_READY
!= EXACT_READBACK_VERIFIED
```

The running application exposes:

- `/healthz`
- `/readyz`
- `/api/source`
- `/api/catalog`
- `/api/catalog/{kind}/{slug}`

Public Hugging Face metadata readback is opt-in and restricted to curated `SZLHOLDINGS/...` identities. Redirects, arbitrary hosts, arbitrary paths, oversized responses, unsupported artifact kinds, malformed slugs, and mutation methods fail closed.

Source authority remains in the linked GitHub repositories. SZL Constellation composes estate navigation; Atelier composes artifact evidence.

## Source

This Space is published from [github.com/szl-holdings/szl-atelier](https://github.com/szl-holdings/szl-atelier) (`frontier/atelier_v3`) by the committed workflow `.github/workflows/hf-space.yml`, after `ci` passes on `main`. The exact GitHub commit is in `SOURCE_REVISION`, and `PUBLICATION_RECEIPT.json` records the SHA-256 of each file published with it.
