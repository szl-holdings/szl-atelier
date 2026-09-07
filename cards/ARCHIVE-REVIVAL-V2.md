---
license: apache-2.0
tags:
- governed-ai
- provenance
- portfolio-governance
- source-authority
- huggingface
---

# Archive Revival v2

Four archived repositories retained unique executable authority and were restored as source owners:

| Source | Authority retained | Hugging Face presentation |
|---|---|---|
| `szl-atelier` | model, dataset, Space, delivery, and research explorer | canonical `SZLHOLDINGS/szl-atelier` target |
| `szl-mesh` | deterministic disconnected-state and CRDT convergence | composed inside Atelier and Constellation |
| `szl-router` | sovereign-first OpenAI-compatible routing and receipts | composed inside Atelier and Constellation |
| `uds-bundles` | repository-owned UDS and Zarf air-gap bundles | composed inside Atelier and Constellation |

Twenty-four superseded repositories remain read-only consolidation tombstones. Six reproducibility and historical repositories remain immutable evidence. The exact lifecycle map is owned by `szl-holdings/.github/governance/archive-portfolio-v2.json`.

## Topology law

Atelier presents the estate; it does not absorb source ownership. Mesh, Router, and UDS keep their own code, tests, histories, and release boundaries. No new peer Hugging Face Space is created for those capabilities by this wave.

## Truth ladder

```text
CLASSIFIED
≠ UNARCHIVED
≠ SOURCE_PR
≠ MERGED
≠ HUB_PUBLISHED
≠ RUNTIME_READY
≠ EXACT_READBACK_VERIFIED
```

The interactive source graph is available at `/revival/` when the Atelier runtime serves this exact revision.
