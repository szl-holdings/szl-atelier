# Reflow and fixed controls

The named `atelier-page` container encloses the page layout. The skip link and
ambient overlay are sibling elements outside that container, so they remain
relative to the viewport even on query engines that apply layout containment.
The existing viewport queries remain the fallback for engines without container
queries.

The CSSWG weakened container-query containment in
[issue 10544](https://github.com/w3c/csswg-drafts/issues/10544). Current Edge does
not reproduce the older fixed-position containment behavior with
`container-type: inline-size` alone. Treat the earlier review finding as a
compatibility issue, not a witnessed defect in current Edge.

Local regression measurements on 2026-09-29 used headless Edge 154.0.4258.37 at
source `31d71e2ea437d066188402cb767206c488d0d39c` and this wrapper change:

- Native current-engine behavior and a separate profile with explicit
  `contain: layout` on the query container. The latter emulates the relevant
  legacy containment rule; an older browser binary was not tested.
- At a 1280 by 900 viewport, after scrolling 800 pixels and focusing the skip
  link with scroll prevention, the legacy profile originally placed the skip
  link and ambient overlay at -800 pixels and made the overlay 3111 pixels tall.
  The wrapper change kept both at 0 pixels and the overlay at 900 pixels in
  both profiles.
- Widths 320, 375, 768, 1280, and 1440 pixels, plus CSS zoom factors 2 and 4 at
  width 1280: zero horizontal overflow before and after. CSS zoom was supplied
  through the same-origin stylesheet; native browser zoom was not tested.
- Audience switching, A11oy filtering, detail-dialog opening and Escape closing
  remained functional. The harness did not bypass the application CSP.

These are local browser measurements. Provider publication and hosted runtime
readback must be checked separately at the merged source revision.
