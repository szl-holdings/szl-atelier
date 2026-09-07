---
license: apache-2.0
tags:
- uds
- zarf
- air-gap
- supply-chain
- provenance
---

# UDS Bundle Observatory

A read-only inspection and validation surface for repository-owned UDS and Zarf manifests, owned by `szl-holdings/uds-bundles`.

## Measured locally

- strict UTF-8 YAML and JSON parsing;
- duplicate-key, non-finite-number, alias, depth, byte, file-count, and traversal controls;
- resolved repository-root containment that rejects paths escaping configured source roots;
- local manifest inventory and source hashes;
- structural findings for credential-like values, mutable image tags, and declared remote references;
- deterministic validation receipts.

## Deliberately unavailable

The observatory does not deploy packages, access Kubernetes, push OCI artifacts, execute shell commands, fetch arbitrary URLs, or infer signature success from a declared field. Signature verification is reported as `UNAVAILABLE_NOT_ATTEMPTED`; deployment is `NOT_ATTEMPTED`.

## Source evidence

- capability source: `szl-holdings/uds-bundles`;
- source-bound Bundle Observatory: pull request `#52`;
- peer Space created by this wave: **no**;
- presentation: SZL Atelier and SZL Constellation.

```text
SOURCE_ACTIVE · READ_ONLY_VALIDATION · NO_PUBLIC_EFFECTOR
```
