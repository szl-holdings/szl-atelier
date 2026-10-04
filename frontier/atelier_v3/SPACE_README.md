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

<p><a href="https://huggingface.co/spaces/SZLHOLDINGS/szl-command-lab"><img src="https://raw.githubusercontent.com/szl-holdings/.github/main/profile/assets/szl/logos/szl_mark_holographic.svg" alt="SZL Holdings" width="112" /></a></p>

# SZL Atelier

Explore models, datasets and Spaces through their source ownership and publication evidence. Atelier brings artifact records and bounded public provider observations into one inspectable interface.

**Artifact:** Artifact discovery and evidence review · **Stage:** Source-owned estate interface

[Explore in Command Lab](https://huggingface.co/spaces/SZLHOLDINGS/szl-command-lab) · [Build](https://github.com/szl-holdings/szl-atelier) · [Evidence](https://github.com/szl-holdings/szl-atelier/actions/workflows/hf-space.yml)

## Before you use it

- Declared Hub identities and source records do not establish current runtime success or exact provider readback.
- Public provider metadata readback is opt-in and restricted to curated SZLHOLDINGS identities.
- This application does not execute models, mutate the Hub or grant release or action authority.

<details>
<summary>Technical details and original evidence</summary>

The retained source below is exact and may contain historical observations. Its dates, use restrictions, licenses and evidence boundaries continue to apply.

<!-- SZL-PRESERVED-TECHNICAL-BODY:START -->

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

<!-- SZL-PRESERVED-TECHNICAL-BODY:END -->

</details>
