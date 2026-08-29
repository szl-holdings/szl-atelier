#!/usr/bin/env python3
"""Export MEASURED nano silhouettes as .npz. Does not retrain 1.5B. Energy UNAVAILABLE."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "nano-weights.json"
OUT = ROOT / "weights"


def arr(x) -> np.ndarray:
    return np.asarray(x, dtype=np.float64)


def main() -> None:
    src = json.loads(SRC.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    seed = np.int64(src["seed"])

    m = src["miniEmbed"]
    np.savez_compressed(
        OUT / "mini_embed.npz",
        table=arr(m["table"]),
        V=np.int64(m["V"]),
        d=np.int64(m["d"]),
        seed=np.int64(m["seed"]),
        retrievalHitAt2=np.float64(m["retrievalHitAt2"]),
    )
    mo = src["moons"]
    np.savez_compressed(
        OUT / "moons.npz",
        w1=arr(mo["w1"]),
        b1=arr(mo["b1"]),
        w2=arr(mo["w2"]),
        b2=arr(mo["b2"]),
        holdoutAcc=np.float64(mo["holdoutAcc"]),
        silhouette=np.float64(mo["silhouette"]),
        seed=seed,
    )
    k = src["tinyKhipu"]
    np.savez_compressed(
        OUT / "tiny_khipu.npz",
        w1=arr(k["w1"]),
        b1=arr(k["b1"]),
        w2=arr(k["w2"]),
        b2=arr(k["b2"]),
        holdoutAcc=np.float64(k["holdoutAcc"]),
        abstainRecall=np.float64(k["abstainRecall"]),
        navigateRecall=np.float64(k["navigateRecall"]),
        seed=seed,
    )
    r = src["receiptAgent"]
    np.savez_compressed(
        OUT / "receipt_agent.npz",
        w1=arr(r["w1"]),
        b1=arr(r["b1"]),
        w2=arr(r["w2"]),
        b2=arr(r["b2"]),
        holdoutAcc=np.float64(r["holdoutAcc"]),
        seed=seed,
    )
    g = src["lambdaGate"]
    np.savez_compressed(
        OUT / "lambda_gate.npz",
        w=np.float64(g["w"]),
        b=np.float64(g["b"]),
        lambdaStar=np.float64(g["lambdaStar"]),
        holdoutAcc=np.float64(g["holdoutAcc"]),
        falseOpenRate=np.float64(g["falseOpenRate"]),
        seed=seed,
    )
    print("wrote", sorted(p.name for p in OUT.glob("*.npz")))


if __name__ == "__main__":
    main()
