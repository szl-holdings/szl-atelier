---
license: apache-2.0
library_name: numpy
tags:
  - governed-ai
  - szl-holdings
  - doctrine-v11
  - nano
  - measured
---

<!-- SZL-CARD-PRESENTATION:v1 -->
<p><a href="https://huggingface.co/spaces/SZLHOLDINGS/szl-command-lab"><img src="https://raw.githubusercontent.com/szl-holdings/.github/main/profile/assets/szl/logos/szl_mark_holographic.svg" alt="SZL Holdings" width="112" /></a></p>

# MiniEmbed-Nano

A deterministic 64 × 12 NumPy table for inspecting token hashing, pooled vectors, and small retrieval examples.

**Artifact:** Atelier NumPy embedding table · **Stage:** Software / reference

[Explore in Command Lab](https://huggingface.co/spaces/SZLHOLDINGS/szl-command-lab) · [Build](https://github.com/szl-holdings/szl-atelier) · [Evidence](https://github.com/szl-holdings/szl-atelier/blob/cfcd7c3eda58f1b4aef2fbdb02a525d04522ade1/cards/MiniEmbed-Nano.md)

## Before you use it

- This table is not a trained neural embedding model; it does not establish a comparison with a foundation embedding model.
- The five-pair retrieval result is SAMPLE. Historical MEASURED and reproducibility labels below are retained source claims, not new independent validation.
- Bind the exact archive, seed, normalization, loader, and revision before use. Khipu's reference card and this Atelier export have separate evidence.

<details>
<summary>Technical details and evidence</summary>

The original Atelier description is preserved below as historical source. Its architecture, comparison, measurement, and signing language does not qualify another archive or establish a new result.

<!-- SZL-CARD-TECHNICAL:v1:START -->

# MiniEmbed-Nano

A 64×12 embedding whose rows are a function of SHA-256. The vector is the receipt of the token.

**Family.** nano · **Evidence.** MEASURED · **Weights.** numpy · **Params.** 64 × 12

Hub: [SZLHOLDINGS/MiniEmbed-Nano](https://huggingface.co/SZLHOLDINGS/MiniEmbed-Nano)

## The cut

Nobody ships an embedding where retrieval is provenance. MiniEmbed is not BGE, not NV-Embed. Mean-pool of L2 rows, seed 20260721, CPU NumPy.

An embedding you can re-derive bit-exact from the seed. No SGD theater. Cosine is a claim about the table, not a vibe.

### Silhouette → leave → SZL

| Leader | Take, then tweak |
|---|---|
| Anthropic | Honest about what it is not — not a foundation embed. |
| NVIDIA | Tiny table instead of NV-Embed / NeMo retrieval stacks. |
| Unsloth | No LoRA. Construction is `build(seed)` — Unsloth is the wrong tool and we say so. |

Nobody else ships this combination. That is the point of a one-of-one.

## Intended use

Silhouette of receipted retrieval. Teaching and tests.

## Limitations

- Not a neural embed.
- Not comparable to BGE-base 768-d.
- Hit@2 is on five doctrine pairs — SAMPLE.

## Honesty

| Claim | Label |
|---|---|
| This card's numbers | MEASURED |
| Energy / joules | UNAVAILABLE unless a signed meter says MEASURED |
| Λ uniqueness | Conjecture 1 OPEN — not a theorem |
| GGUF as the signed object | FALSE |

Doctrine v11 LOCKED · 749 declarations · 14 axioms · 163 sorries · locked-proven 8.

Apache-2.0. Copyright 2026 SZL Holdings · Stephen P. Lutar Jr. · ORCID [0009-0001-0110-4173](https://orcid.org/0009-0001-0110-4173).

<!-- SZL-CARD-TECHNICAL:v1:END -->

</details>
