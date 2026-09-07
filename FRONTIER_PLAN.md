# SZL Atelier v3 — governed artifact showcase

SZL Atelier is the estate's source-bound Hugging Face artifact explorer. It composes model, dataset, Space, research, and delivery evidence without becoming the source owner of the assets it displays.

## Delivery boundary

`SOURCE_PR != MERGED != HUB_PUBLISHED != RUNTIME_READY != EXACT_READBACK_VERIFIED`

The implementation must fail closed on unavailable provider evidence, use local-only frontend assets, bind every response to the exact source revision, and publish only through the canonical writer for `SZLHOLDINGS/szl-atelier`.
