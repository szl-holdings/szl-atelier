# Leader Study: szl-atelier (OUROBOROS spaces batch-2 census, lap P5)

Status: [PROPOSE-ONLY] documentation study. No code, CI, label, or Space changes are proposed by this document. Every statement below is bounded by the repo's own measured labels; nothing is promoted from REPORTED/SAMPLE/UNAVAILABLE to MEASURED.

## 1. What szl-atelier is today (measured from the repository, commit a73c198)

- A legacy gallery of 40 curated records (CATALOG label), served by a root Docker/FastAPI runtime with a fail-closed readiness contract (/readyz fails unless all 40 records load), plus the separate active v3 Space projection (nine controlled files published byte-for-byte from one GitHub commit; the publisher refuses drift between package, Hub commit, and running Space).
- An evidence-label taxonomy that is the repo's honesty backbone: CATALOG, RUNTIME-OBSERVED, MEASURED, SYNTHETIC, REPORTED, SAMPLE, UNAVAILABLE; GGUF is derived, never the signed object; Energy/CUDA UNAVAILABLE; Lambda uniqueness is Conjecture 1 OPEN; receipt persistence for browser frontier receipts is NOT CONFIGURED (honestly disclosed).
- Known owner-terrain conflict (observed 2026-11-06, recorded in README): the Space reads private (HTTP 401 anonymous) while the .github lifecycle policy still declares it public, and the a11oy space-fold-registry marks it FOLD (pending); the hf-space publisher cannot complete anonymous runtime readback until the owner settles it. This study takes no side; it is owner terrain.

## 2. Leaders studied (web-verified 2026-11-24)

### L1. Hugging Face Model Cards (Hub conventions and model-index)
What they have: a machine-readable YAML metadata block (license, tags, linked datasets/models), an ecosystem-wide card convention, and a model-index schema that reports structured, per-dataset benchmark results inside the card, versioned with the repo, so downstream tooling can parse and compare results without reading prose.
What we already match on: pinned provenance, explicit license metadata, honest non-claims, linked models/datasets in card frontmatter.
Gap: the 40 records carry prose evidence labels but no machine-readable per-record results index; a consumer cannot programmatically enumerate which records have which class of evidence.

### L2. Model Cards for Model Reporting (Mitchell et al., arXiv 1810.03993) and the TensorFlow Model Card Toolkit lineage
What they have: a standardized card schema (intended use, out-of-scope use, factors, metrics, evaluation data, ethical considerations, caveats) plus tooling that generates cards from a structured spec, making the narrative itself auditable rather than free-form.
What we already match on: quantitative honesty, explicit caveats, refusal to launder claims.
Gap: per-record narrative structure (intended use, out-of-scope use, measurement plan) is not standardized across the 40 records; the gallery proves what records ARE, not what each is FOR and NOT for.

### L3. Linux Foundation AI & Data Model Openness Framework (MOF)
What they have: a public taxonomy grading models by which artifacts are actually released (code, weights, data, logs, cards), producing a completeness/openness level instead of a binary open/closed claim; published as a framework the ecosystem can cite.
What we already match on: artifact-level honesty (we distinguish MEASURED from REPORTED from UNAVAILABLE, GGUF from the signed object).
Gap: the gallery does not encode per-record artifact completeness (which of: signed receipts, GGUF-only weights, eval receipts, data lineage exist for each record); a reader must infer it from label prose.

### L4. AI Verify (Singapore IMDA / AI Verify Foundation)
What they have: a claim-check process: stated claims are mapped to independently measured results by a testing toolkit, and the verification outcome (verified / not verified / not testable) is published, with public annual reports on what was measured and how.
What we already match on: the owner-run eval receipts are labeled REPORTED (the 2026-07-14 SZL-Khipu-1.5B eval: plan-valid 11/11, grounding 4/5, abstain 2/6 blocker, 0 hallucinated citations) and explicitly not re-run here; nothing is presented as re-verified.
Gap: there is no claimed-vs-evidenced map per record; the label discipline exists, but no artifact connects each public claim to its receipt or to an explicit not-re-verified note in a single place.

## 3. Gap analysis (atelier vs leaders)

The atelier is already stronger than all four leaders on one axis: it never presents derived or reported artifacts as measured, and its v3 projection refuses drift by construction. The leaders are stronger on three axes: machine-readability of results (L1), standardized per-record narrative schema (L2), artifact-completeness grading (L3), and a claim-check artifact class (L4). None of the four leaders require weakening any atelier label to absorb.

## 4. Absorb candidates (all UNAPPROVED; each needs its own propose-only implementation lap and fresh gates)

- A1 (from L1): add a machine-readable per-record evidence index (JSON/YAML) enumerating record id, evidence class, receipt pointer. Labels unchanged; index can only reference existing receipts.
- A2 (from L2): add a per-record card schema v0 (intended use, out-of-scope use, measurements available, caveats) for the 40 records, narrative-only, CI-checkable for structure only.
- A3 (from L3): add an artifact-completeness field per record (signed receipts / GGUF-only / eval receipt present / data lineage present) using the repo's OWN label vocabulary, no external branding.
- A4 (from L4): add a claimed-vs-evidenced map connecting each public claim to its receipt or explicit not-re-verified note; nothing gets promoted.

## 5. Open questions (owner ruling required; not decidable by this lane)

- A5: Space visibility conflict (private Space vs public lifecycle policy vs FOLD pending): which way does the owner want it settled? Any change is owner terrain; this study only records the tension.
- A6: Should the gallery surface deeper links to the hologram sibling Space (szl-khipu Gradio hologram), or keep surfaces strictly separated as today?

## 6. Non-goals

No code changes; no CI changes; no label taxonomy changes; no claim promotion; no Space writes; no settings or protection changes; nothing in this document presented as MEASURED that is not; this document adds a study only and recommends nothing else; zero merges.