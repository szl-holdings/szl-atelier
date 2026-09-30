---
license: apache-2.0
library_name: kernels
tags:
  - governed-ai
  - szl-holdings
  - doctrine-v11
  - kernel
  - hub
---

# szl-kernels

**Reference governance kernels with a separate 3290-by-128 in-domain PPMI/SVD embedding companion.**

The software suite and learned embedding table are distinct artifacts with separate evidence limits. Historical test and embedding-sanity records do not establish current runtime readiness, downstream retrieval quality, or acceleration.

Review snapshot: **2026-09-30 UTC**. This is a documentation review. No new model evaluation, weight download, inference, signature verification, provider publication, runtime check, or release/client qualification was performed.

## Artifact and source identity

- Reviewed [model-card snapshot](https://huggingface.co/SZLHOLDINGS/szl-kernels/tree/f67a26a8141b1436ee2d1de64fb202c493981a2d): `f67a26a8141b1436ee2d1de64fb202c493981a2d`.
- [Canonical source-card/software snapshot](https://github.com/szl-holdings/szl-kernels/blob/7b59de18d35b1edca3c54a4647fb324b918563a8/README.md): `szl-holdings/szl-kernels@7b59de18d35b1edca3c54a4647fb324b918563a8`. This is a source reference, not an attestation of Hub package parity or an approved runtime release.
- Reference Python suite; separate vectors.npz, vocab.json and config.json embedding companion.
- The model mirror is not a hosted Transformers feature-extraction contract.

## Retained evidence and disposition

The model card records 29 tests passing on 2026-08-29 in its named Windows environment and separately records torch.compile fullgraph failures. These historical outcomes are retained, with no current green-test claim.

The embedding receipt reports an in-domain PPMI/SVD table and intrinsic nearest-neighbour sanity. No downstream retrieval benchmark, general embedding quality, bit-identical retraining, GPU speedup, or energy value is established here.

Evidence files at the reviewed immutable model revision:

- [TRAINING_RECEIPT.json](https://huggingface.co/SZLHOLDINGS/szl-kernels/blob/f67a26a8141b1436ee2d1de64fb202c493981a2d/TRAINING_RECEIPT.json)
- [publication.json](https://huggingface.co/SZLHOLDINGS/szl-kernels/blob/f67a26a8141b1436ee2d1de64fb202c493981a2d/publication.json)

## Intended use and limits

Research and inspection of reference software and bounded in-domain embedding behavior.

- The suite is software; trained=true describes only the separate PPMI/SVD embedding companion.
- Intrinsic nearest-neighbour sanity is not a downstream retrieval benchmark or general-purpose embedding qualification.
- Energy needs an actual supported metering receipt. An illustrative number cannot be labelled MEASURED; unavailable energy remains unavailable.
- Historical 29-test/import records and Windows torch.compile failures remain dated observations; tests and model evaluation were not rerun for this card review.
- The retained publication binds an earlier declared file set. It does not bind the subsequently changed README; no replacement source binding is asserted.

The source, model mirror, historical release, derived artifact, and served runtime are separate identities. A public file, a card edit, a matching aggregate result, or a recorded signature is not a new deployment or eligibility decision. Follow each retained record to its named revision and scope.

## License

Apache-2.0 is declared in repository metadata. A [LICENSE file](https://huggingface.co/SZLHOLDINGS/szl-kernels/blob/f67a26a8141b1436ee2d1de64fb202c493981a2d/LICENSE) is listed at the reviewed model revision; this review does not determine upstream or downstream license coverage.

Lambda uniqueness remains Conjecture 1 (open). Historical receipts and failed outcomes are retained; this review does not upgrade them.
