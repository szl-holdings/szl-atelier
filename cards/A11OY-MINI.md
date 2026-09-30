---
license: apache-2.0
library_name: gguf
tags:
  - governed-ai
  - szl-holdings
  - doctrine-v11
  - doctrine
  - hub
---

# A11OY-MINI

**Derived Chaski GGUF artifacts with dated envelope checks, observed semantic failures, and HOLD disposition.**

Legacy Chaski GGUFs, the Chaski-R2 Q4_K_M text artifact and its BF16 projector have distinct lineage and qualification limits. The 2026-09-24 owner-local envelope result is 5/5 drafts and 6/6 refusal prefixes; the 2026-09-25 qualitative review records semantic failures.

Review snapshot: **2026-09-30 UTC**. This is a documentation review. No new model evaluation, weight download, inference, signature verification, provider publication, runtime check, or release/client qualification was performed.

## Artifact and source identity

- Reviewed [model-card snapshot](https://huggingface.co/SZLHOLDINGS/A11OY-MINI/tree/7ea56236ea7988b3915b5ef07548cb2c3930a3cf): `7ea56236ea7988b3915b5ef07548cb2c3930a3cf`.
- [Canonical source-card/software snapshot](https://github.com/szl-holdings/szl-forge/blob/5b3dfdf9beafe0d6d1e6043ca005ec4b17c45204/a11oy-mini/card/README.md): `szl-holdings/szl-forge@5b3dfdf9beafe0d6d1e6043ca005ec4b17c45204`. This is a source reference, not an attestation of Hub package parity or an approved runtime release.
- Legacy Chaski F16/Q4_K_M GGUFs remain separate from the Chaski-R2 Q4_K_M text artifact and BF16 projector.
- Historical inventory `c936dc749743c94586706345a0142c79094a581c` and observed artifact revision `0619dd65b92a135501af35b3c4e3b4e762be1d7d` are not the current card snapshot.

## Retained evidence and disposition

An owner-local artifact-bound observation on **2026-09-24** reported **5/5 draft envelopes** and **6/6 refusal prefixes** for the R2 Q4_K_M text artifact. Its record is `UNSIGNED_HONEST`, with `HOLD`, `publication_eligible=false`, `autonomy_eligible=false`, and `promotion_effect=NONE`.

The retained **2026-09-25** coding-agent qualitative semantic review records `SEMANTIC_FAILURES_OBSERVED`: outputs treated artifact presence or training loss as evaluation and asserted unsupported job/completion states. It is not an exhaustive semantic scorer or an independent human evaluation; **semantic_pass_rate is null**. Other cases were not assigned semantic PASS. The envelope counts do not override these findings. No vision qualification follows.

Evidence files at the reviewed immutable model revision:

- [evidence/2026-09-24-native-cuda/receipt.json](https://huggingface.co/SZLHOLDINGS/A11OY-MINI/blob/7ea56236ea7988b3915b5ef07548cb2c3930a3cf/evidence/2026-09-24-native-cuda/receipt.json)
- [evidence/2026-09-24-native-cuda/semantic_review.json](https://huggingface.co/SZLHOLDINGS/A11OY-MINI/blob/7ea56236ea7988b3915b5ef07548cb2c3930a3cf/evidence/2026-09-24-native-cuda/semantic_review.json)

## Intended use and limits

Inspection of retained research artifacts and evidence; the documented disposition remains HOLD, without production or autonomy qualification.

- HOLD; publication_eligible=false; autonomy_eligible=false; promotion_effect=NONE in the retained native observation and semantic review.
- The 2026-09-25 qualitative review found artifact-presence-as-evaluation, training-loss-as-evaluation and unsupported job-state claims. No semantic pass rate is established.
- Legacy GGUFs retain deprecated failed-parent lineage. R2 text checks do not qualify the BF16 vision projector or vision use.
- The Sept 17 unbound gate, Sept 24 artifact-bound observation and current documentation snapshot are separate evidence identities.
- Apache-2.0 is declared; no standalone LICENSE file is listed at the reviewed model revision. Artifact license coverage was not independently verified.

The source, model mirror, historical release, derived artifact, and served runtime are separate identities. A public file, a card edit, a matching aggregate result, or a recorded signature is not a new deployment or eligibility decision. Follow each retained record to its named revision and scope.

## License

Apache-2.0 is declared in repository metadata. No standalone LICENSE file is listed at the reviewed model revision; artifact license coverage was not independently verified.

Lambda uniqueness remains Conjecture 1 (open). Historical receipts and failed outcomes are retained; this review does not upgrade them.
