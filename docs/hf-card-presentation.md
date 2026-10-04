# Nano and kernel card source alignment

These five existing Atelier fallback cards now begin with a short description
of the actual software fixture, its stage, useful routes, and visible limits.
Every original YAML field, license, and complete technical body is preserved
from `cfcd7c3eda58f1b4aef2fbdb02a525d04522ade1`.

The original descriptions are identified as historical source. Their
architecture, comparison, measurement, lineage, and signing language does
not establish a new evaluation or qualify another archive.

## Exact source map

[`publishing/hf-card-presentation.v1.json`](../publishing/hf-card-presentation.v1.json)
records the five model targets, original Git blobs and SHA256 values, output
digests, dated Hub/provider observations, visible limits, and known alternate
README sources. Extracting the bytes between the
`SZL-CARD-TECHNICAL:v1` markers must recover the complete original body;
frontmatter must match its original bytes separately.

| Target | Existing fallback source | Fixture scope |
|---|---|---|
| TinyKhipu-Nano | `cards/TinyKhipu-Nano.md` | Atelier 4→6→2 synthetic MLP |
| ReceiptAgent-Nano | `cards/ReceiptAgent-Nano.md` | Atelier 4→10→4 synthetic MLP |
| Moons-Nano | `cards/Moons-Nano.md` | Atelier 2→8→2 toy MLP |
| MiniEmbed-Nano | `cards/MiniEmbed-Nano.md` | Atelier 64 × 12 reference table |
| szl-khipu-kernels | `cards/szl-khipu-kernels.md` | Python kernel software |

The Nano shapes are bound to this source revision's `nano-weights.json`.
No training, benchmark, served endpoint, or native kernel qualification was
performed for this presentation change.

## Writer and publication boundary

A11oy's existing `.github/workflows/atelier-hub-publish.yml` checks out this
repository and then overlays its own kit. These five paths are absent from
that overlay at the examined A11oy revision
`5e014855a274825f4d46ce91cb3396cabd20f99a`, so their bodies come from this source.

That workflow is an existing broad publisher: it writes Nano READMEs and
exports/uploads NPZ files from `nano-weights.json`, along with other Space and
software files. It is not a card-only operation. This PR does not change or
invoke that workflow, its credentials, artifact writers, or resource scope.

Khipu has separate current Nano and kernel-pack card writers; Forge also writes
TinyKhipu-Nano and ReceiptAgent-Nano cards. In particular, the Atelier Tiny/Receipt
fixtures have different schemas from the Khipu package archives. The source map
therefore records known cross-writers and does not authorize central application
or infer a sole writer. Any later publication needs its own exact-source and
artifact evidence.

The canonical shared holographic mark is a separate publication dependency.
The new cards use the existing Command Lab explorer and make no inference
provider adoption or production readiness claim.

