---
license: apache-2.0
tags:
- crdt
- distributed-systems
- disconnected-operations
- deterministic-systems
- provenance
---

# SZL Mesh Command

A deterministic convergence observatory for disconnected state, owned by `szl-holdings/szl-mesh`.

## What it proves

- vector-clock relationships: `before`, `after`, `equal`, and `concurrent`;
- arrival-order-independent last-writer-wins register selection;
- deterministic conflict evidence;
- separate input and output SHA-256 receipts;
- explicit tombstone handling;
- exact source identity and controlled-file hashes.

## What it does not do

It does not discover peers, open sockets or radios, transmit state, execute commands, mutate a cluster, or claim live mesh connectivity. The topology shown by the source runtime is labeled `DECLARED_DEMO_TOPOLOGY`; unavailable live-network evidence remains `UNAVAILABLE_NOT_ATTEMPTED`.

## Source evidence

- capability source: `szl-holdings/szl-mesh`;
- deterministic convergence command: pull request `#41`;
- peer Space created by this wave: **no**;
- presentation: SZL Atelier and SZL Constellation.

```text
SOURCE_ACTIVE · PRESENTED_IN_ATELIER · NO_NEW_PEER_SPACE
```
