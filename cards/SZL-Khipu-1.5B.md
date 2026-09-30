---
license: apache-2.0
library_name: transformers
tags:
  - governed-ai
  - szl-holdings
  - doctrine-v11
  - navigator
  - signed
---

# SZL-Khipu-1.5B

**Proposal-only retrieval plans over supplied synthetic handles; the historical 2/6 abstention blocker remains visible.**

An external controller must reject citations outside the offered candidates and independently gate execution. The owner-run 11-case evaluation observed zero hallucinated citations; this result describes only those named cases.

Review snapshot: **2026-09-30 UTC**. This is a documentation review. No new model evaluation, weight download, inference, signature verification, provider publication, runtime check, or release/client qualification was performed.

## Artifact and source identity

- Reviewed [model-card snapshot](https://huggingface.co/SZLHOLDINGS/SZL-Khipu-1.5B/tree/724d251459cc987f33985c5799f5f3a9e02f4cd2): `724d251459cc987f33985c5799f5f3a9e02f4cd2`.
- [Canonical source-card/software snapshot](https://github.com/szl-holdings/szl-forge/blob/5b3dfdf9beafe0d6d1e6043ca005ec4b17c45204/khipu/card/README.md): `szl-holdings/szl-forge@5b3dfdf9beafe0d6d1e6043ca005ec4b17c45204`. This is a source reference, not an attestation of Hub package parity or an approved runtime release.
- Merged model.safetensors, adapter files, schema and owner-signed training/evaluation receipts are distinct from the separately distributed GGUF derivatives.
- No weights were downloaded or rehashed, and no model or controller was executed for this card review.

## Retained evidence and disposition

The retained owner-signed evaluation record dated **2026-07-14** reports **11/11** schema-valid plans, **4/5** grounding-correct cases, **2/6** abstention-correct cases and **zero** hallucinated citations on its small synthetic harness. These are owner-run counts, not an independent benchmark or a citation guarantee. The **2/6 abstention blocker** remains controlling for autonomous or high-stakes use.

The **2026-09-24** owner-reported Q4_K_M rerun matched those aggregate counts on the same 11 named cases. It is evidence about a separate derived runtime artifact on reused fixtures; it does not establish general behavior equivalence.

`weightsArtifactSha256` and `adapterSha256` are directory digests over sorted safetensors filenames plus their bytes. They must not be compared directly with an individual-file LFS digest or treated as covering a GGUF. The retained card source binding does not bind later README edits; no new binding is created here.

Evidence files at the reviewed immutable model revision:

- [eval_receipt.signed.json](https://huggingface.co/SZLHOLDINGS/SZL-Khipu-1.5B/blob/724d251459cc987f33985c5799f5f3a9e02f4cd2/eval_receipt.signed.json)
- [training_receipt.signed.json](https://huggingface.co/SZLHOLDINGS/SZL-Khipu-1.5B/blob/724d251459cc987f33985c5799f5f3a9e02f4cd2/training_receipt.signed.json)
- [szl-source-binding.json](https://huggingface.co/SZLHOLDINGS/SZL-Khipu-1.5B/blob/724d251459cc987f33985c5799f5f3a9e02f4cd2/szl-source-binding.json)

## Intended use and limits

Controller-bound retrieval-planning research over supplied candidates; model output remains a proposal.

- The owner-run evaluation dated 2026-07-14 reports plan validity 11/11, grounding 4/5, abstention 2/6 and zero hallucinated citations on a small synthetic harness.
- Abstention 2/6 remains a blocker for autonomous or high-stakes use; no general citation, factuality or safety guarantee is established.
- The signed safetensors digests hash sorted filenames plus bytes. They are distinct from individual-file LFS digests and do not cover derived GGUF files.
- The 2026-09-24 owner-reported Q4_K_M rerun matched aggregate counts on the same 11 named cases; it does not establish general behavior equivalence.
- The reviewed README has changed since its retained source-binding record. This review creates no replacement binding or release qualification.

The source, model mirror, historical release, derived artifact, and served runtime are separate identities. A public file, a card edit, a matching aggregate result, or a recorded signature is not a new deployment or eligibility decision. Follow each retained record to its named revision and scope.

## License

Apache-2.0 is declared in repository metadata. A [LICENSE file](https://huggingface.co/SZLHOLDINGS/SZL-Khipu-1.5B/blob/724d251459cc987f33985c5799f5f3a9e02f4cd2/LICENSE) is listed at the reviewed model revision; this review does not determine upstream or downstream license coverage.

Lambda uniqueness remains Conjecture 1 (open). Historical receipts and failed outcomes are retained; this review does not upgrade them.
