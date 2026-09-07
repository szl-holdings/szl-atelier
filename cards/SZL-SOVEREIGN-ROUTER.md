---
license: apache-2.0
tags:
- inference
- routing
- openai-compatible
- sovereign-ai
- provenance
---

# SZL Sovereign Router

A default-deny, OpenAI-compatible routing and receipt authority owned by `szl-holdings/szl-router`.

## Policy surface

Eligible providers are filtered by model alias, data classification, cost ceiling, exact endpoint allowlist, enabled state, and credential availability. Deterministic ordering is:

```text
sovereignty DESC
priority ASC
cost_tier ASC
provider_id ASC
```

Every successful completion receives a receipt committing the request, route plan, provider attempts, selected provider, upstream model, elapsed time, and response digest without recording credential material.

## Fail-closed boundary

Egress is disabled unless an operator supplies an exact HTTPS hostname allowlist, a validated provider registry, named provider credentials, and `SZL_ROUTER_ENABLE_EGRESS=1`. Literal IPs, localhost, embedded URL credentials, redirects, inherited proxy configuration, arbitrary target URLs, and streaming are rejected in receipt-verified v1.

## Source evidence

- capability source: `szl-holdings/szl-router`;
- receipt-bound gateway: pull request `#47`;
- peer Space created by this wave: **no**;
- presentation: SZL Atelier and SZL Constellation.

```text
SOURCE_MERGED
≠ PROVIDER_CONFIGURED
≠ EGRESS_ENABLED
≠ ANSWER_RECEIPT_EMITTED
```
