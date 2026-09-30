# Six kernel card and provenance corrections

These are source-owned review files for `szl-holdings/szl-atelier`. The six
`cards/szl-*.md` files and matching catalog/index entries now describe software
kernels with limited maturity, scoped evidence, and release-qualified examples.
The model mirror, first-class Kernel Hub package and GitHub source retain
distinct immutable identities.

The `.baseline.json` files contain the exact reviewed Hub provenance bytes.
The `.proposed.json` files correct current artifact absence and current GitHub
reachability while preserving the prior model, claims, source and repository
observations under `historical_provenance_before_correction`. Historical
verification results and surrogate metrics remain unchanged and are scoped as
historical records. `review.json` binds the baselines and proposals by SHA-256,
records the reviewed file inventories, and protects each original training
receipt by its immutable revision and digest.

Run the offline check from the repository root:

```sh
python scripts/validate_kernel_card_review.py
python -m pytest -q tests/test_kernel_card_review.py
```

The validator makes no network request, imports no kernel, and publishes
nothing. An optional `--observed-parents parents.json` compares separately
captured parent revisions for all six repositories; a match establishes only
agreement with those supplied observations.

The existing Atelier v3 exact Space projection excludes these cards and root
catalog records. This review adds no publisher, workflow trigger, release,
deployment, or credential. Canonical code repositories keep their existing
READMEs and release contracts. In particular, the invariants four-file source
binding is unchanged.

Before any later Hub correction, the authorized card owner must re-read the
current provider parents, inspect any drift, and review precisely `README.md`
and `MODEL_PROVENANCE.json`. Preserve `TRAINING_RECEIPT.json` and all unrelated
Hub artifacts. Use the existing approved publication path with exact parent
guards, then read back immutable provider bytes. An observed kernel revision
is not release approval or client qualification. A current GitHub head need
not equal an intentionally older published release; no whole-tree parity or
build-attestation failure is asserted here.
