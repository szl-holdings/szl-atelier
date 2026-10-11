# Atelier v3 native artifact interface

The active Space serves `frontier/atelier_v3/static/index.html`, `styles.css`,
and `app.js`. The root gallery and `revival/` sources remain separate historical
interfaces. The v3 `PUBLICATION.json` continues mapping the same nine source
files; its publisher still owns generated source identity and delivery receipts.

The HTML references the same `/styles.css` and `/app.js` routes with query
versions equal to each file's SHA-256. Fresh HTML therefore requests its current
asset versions instead of reusing the preceding cached URLs. The existing
five-minute cache policy is unchanged; these query versions are source bindings,
not a claim that historical asset bodies remain hosted. Recompute the two query
values after changing either static file; the source tests reject stale values.

## Presentation and interaction

The interface uses the approved native 32px Orbit icon, graphite and paper
surfaces, a restrained holographic edge, and canonical coral action roles.
System polarity initializes the theme; the explicit theme control changes only
the current page. No browser storage or external resource is needed.

The source badge says **Reported source** when the backend provides a valid
40-character revision. That observation does not establish independent source
verification or Hub publication. Provider readback stays explicit, bounded and
read only; accessible status text explains the result while retaining its raw
response and existing abort/late-response guards.

Artifact cards use article and heading semantics with native buttons. The
constellation is a valid list and labels its 12-item preview limit. Search and
collection filters can be cleared; unavailable catalog data can be retried
without duplicating collection options. The slash shortcut respects editing
controls, modifiers and an open dialog. No-script users receive local catalog
and source links, with inactive JavaScript controls hidden.

## Exact native assets

`NATIVE_PRESENTATION.json` records the immutable token and icon revisions,
paths, hashes and embedding locations. The styles contain the exact token bytes
between managed comments; the image contains the original SVG bytes in a data
URI allowed by the existing CSP. This is a **two-asset embedded subset**, not a
full KANCHAY installation. The icon has 8px clear space and is not recolored,
redrawn, shadowed or distorted.

Brand artwork is © 2026 SZL Holdings,
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), reproduced without
modification. Component code is Apache-2.0. The canonical brand source manifest
has not been rewritten to describe this subset.

## Local checks

The existing `atelier-v3.yml` source gate runs the Python suite, including the
new exact-asset/package checks, and the expanded provider-readback JavaScript
fixture. The original source, publisher, dependency, CSP and authority checks
remain intact.

`tools/verify_atelier_native.mjs` takes `PREVIEW_BASE_URL` (localhost only),
`EXPECTED_SOURCE_REVISION`, and `PLAYWRIGHT_MODULE_PATH`. An optional
`CHROMIUM_EXECUTABLE` selects an installed local browser, and
`NATIVE_REPORT_DIR` places evidence outside the checkout. Serve the existing v3
application with `SOURCE_REVISION` set to that exact source commit.

The browser verifier covers dark and light layouts, 320–1440px widths, CSS zoom
at 200% and 400%, forced colors, no-script access, actual catalog controls,
keyboard/dialog behavior, explicit provider-result fixtures, failed-catalog
recovery, valid empty catalogs, and malformed source identity. All non-GET or
outside-origin browser requests are blocked. Provider-readback URLs are fulfilled
locally by clearly identified fixtures before they reach the server. No actual
provider, model, inference or business call is performed.

Reports distinguish dirty preview trees from committed sources and never claim
live parity. Final publication and runtime qualification remain the responsibility
of the existing closed-package publisher.
