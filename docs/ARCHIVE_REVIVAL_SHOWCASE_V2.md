# Archive Revival v2 showcase

## Objective

Present the reviewed archive-revival portfolio through one coherent Hugging Face-facing surface without turning each restored capability into a peer product or transferring source ownership into Atelier.

The canonical disposition remains:

```text
szl-holdings/.github/governance/archive-portfolio-v2.json
```

That manifest classifies 34 archived repositories into four restored source owners, twenty-four consolidation tombstones, and six immutable historical records.

## Restored source owners

| Repository | Unique maintained authority | Presentation decision |
|---|---|---|
| `szl-holdings/szl-atelier` | model, dataset, Space, delivery, and research exploration | one canonical Atelier Space target |
| `szl-holdings/szl-mesh` | disconnected-state and CRDT convergence | source-owned; composed inside Atelier and Constellation |
| `szl-holdings/szl-router` | sovereign-first OpenAI-compatible routing and receipts | source-owned; composed inside Atelier and Constellation |
| `szl-holdings/uds-bundles` | UDS/Zarf air-gap bundle definitions and validation | source-owned; composed inside Atelier and Constellation |

The three capability repositories do not acquire new peer Spaces from this wave. Their source code, tests, release histories, security boundaries, and runtime identities remain in their own GitHub repositories.

## Static showcase contract

The `/revival/` surface consists only of local assets:

```text
revival/index.html
revival/styles.css
revival/app.js
revival/catalog.json
```

The frontend performs one same-origin read of `catalog.json`. External URLs are navigation links only; there is no external script, stylesheet, analytics, cookie, browser-storage, WebSocket, EventSource, or unbounded runtime retrieval.

The catalog carries no provider credential, live runtime claim, mutable source revision, or copied archive map. Instead, it points to the canonical governance manifest and records explicit unavailable states until exact provider readback exists.

## Source cards

Four source-bound cards are added under `cards/`:

- `ARCHIVE-REVIVAL-V2.md` — portfolio lifecycle and truth ladder;
- `SZL-MESH-COMMAND.md` — deterministic convergence capability;
- `SZL-SOVEREIGN-ROUTER.md` — default-deny inference routing capability;
- `UDS-BUNDLE-OBSERVATORY.md` — bounded air-gap bundle inspection capability.

The cards summarize public contracts; they do not copy implementation source into Atelier.

## Accessibility and responsive contract

The surface must remain usable from 320 CSS pixels through ultrawide displays and must provide:

- no page-level horizontal overflow;
- local wrapping for identifiers and evidence strings;
- keyboard-operable source and audience controls;
- visible focus;
- 48-pixel primary/coarse-pointer targets;
- reduced-motion behavior;
- increased-contrast behavior;
- forced-colors support;
- zoom/reflow support;
- print output without decorative orbit effects.

## Publication and truth boundary

A source merge can qualify files for the canonical Atelier publisher. It does not prove that the Hub received them or that the Space serves them.

A complete publication receipt must independently verify:

1. exact protected-main source revision;
2. exact Hugging Face commit;
3. byte-for-byte values for all controlled revival files;
4. Space runtime readiness;
5. live response availability for `/revival/`;
6. live catalog byte digest;
7. runtime source identity, where the Atelier deployment contract exposes it.

The state ladder is deliberately non-collapsible:

```text
CLASSIFIED
≠ UNARCHIVED
≠ SOURCE_PR
≠ MERGED
≠ HUB_PUBLISHED
≠ RUNTIME_READY
≠ EXACT_READBACK_VERIFIED
```
