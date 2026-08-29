#!/usr/bin/env python3
"""CPU-train WILLAY + Chaski silhouettes. Measure kernels. No 1.5B retrain.

Evidence: MEASURED on synthetic overlapping features (not linearly separable
by design). ROADMAP stays empty. STUB stays STUB. Joblib stays quarantined.
Energy UNAVAILABLE. Lambda = Conjecture 1 OPEN.

  python train_cohort.py                 # fit silhouettes + measure kernels
  python train_cohort.py --kernels-only  # re-measure organs, keep MLP packs
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

SEED = 20260721
rng = np.random.default_rng(SEED)
KERNELS_ONLY = "--kernels-only" in sys.argv

HERE = Path(__file__).resolve().parent
if (HERE / "kernels").is_dir():
    # Space kit copy: public/space/kit/train_cohort.py
    KERNELS = HERE / "kernels"
    SPACE = HERE.parent
    WEIGHTS = SPACE / "weights"
    NANO = Path("/workspace/src/lib/nano-weights.json")
    if not NANO.exists():
        NANO = SPACE / "nano-weights.json"
    SPACE_NANO = SPACE / "nano-weights.json"
    KIT_NANO = HERE / "nano-weights.json" if (HERE / "nano-weights.json").exists() else SPACE / "nano-weights.json"
    ROOT = NANO.parents[2] if NANO.name == "nano-weights.json" and NANO.parent.name == "lib" else SPACE
else:
    ROOT = HERE.parent
    KERNELS = ROOT / "public/space/kit/kernels"
    NANO = ROOT / "src/lib/nano-weights.json"
    SPACE_NANO = ROOT / "public/space/nano-weights.json"
    KIT_NANO = ROOT / "public/kit/nano-weights.json"
    WEIGHTS = ROOT / "public/space/weights"


def sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.clip(z, -40, 40)
    return 1.0 / (1.0 + np.exp(-z))


def softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def mlp_train(x: np.ndarray, y: np.ndarray, h: int, k: int, epochs: int, lr: float):
    n, d = x.shape
    w1 = rng.normal(0, 0.4, (d, h))
    b1 = np.zeros(h)
    w2 = rng.normal(0, 0.4, (h, k))
    b2 = np.zeros(k)
    yoh = np.eye(k)[y.astype(int)]
    hist = []
    for ep in range(epochs):
        h1 = np.tanh(x @ w1 + b1)
        logits = h1 @ w2 + b2
        p = softmax(logits)
        loss = float(-np.mean(np.sum(yoh * np.log(p + 1e-9), axis=1)))
        dz2 = (p - yoh) / n
        dw2 = h1.T @ dz2
        db2 = dz2.sum(axis=0)
        dh1 = dz2 @ w2.T * (1 - h1**2)
        dw1 = x.T @ dh1
        db1 = dh1.sum(axis=0)
        w1 -= lr * dw1
        b1 -= lr * db1
        w2 -= lr * dw2
        b2 -= lr * db2
        pred = p.argmax(axis=1)
        acc = float((pred == y).mean())
        hist.append({"epoch": ep + 1, "loss": round(loss, 6), "acc": round(acc, 6)})
    return {"w1": w1, "b1": b1, "w2": w2, "b2": b2, "hist": hist}


def mlp_predict(pack, x: np.ndarray) -> np.ndarray:
    h1 = np.tanh(x @ pack["w1"] + pack["b1"])
    return softmax(h1 @ pack["w2"] + pack["b2"])


def arr(a: np.ndarray):
    return np.asarray(a).astype(float).round(6).tolist()


def noisy(row: list[float], sigma: float = 0.14) -> list[float]:
    x = np.asarray(row, dtype=np.float64) + rng.normal(0, sigma, len(row))
    return np.clip(x, 0, 1).tolist()


def split_xy(rows, labs, frac=0.8):
    x = np.array(rows, dtype=np.float64)
    y = np.array(labs, dtype=np.int64)
    perm = rng.permutation(len(y))
    x, y = x[perm], y[perm]
    cut = int(frac * len(y))
    return x[:cut], y[:cut], x[cut:], y[cut:]


def pack_mlp(trained, xte, yte, labels: list[str], extra: dict | None = None):
    p = mlp_predict(trained, xte)
    pred = p.argmax(1)
    acc = float((pred == yte).mean())
    per = {}
    for i, name in enumerate(labels):
        m = yte == i
        per[name] = float((pred[m] == i).mean()) if m.any() else 0.0
    out = {
        "w1": arr(trained["w1"]),
        "b1": arr(trained["b1"]),
        "w2": arr(trained["w2"]),
        "b2": arr(trained["b2"]),
        "holdoutAcc": round(acc, 4),
        "perClass": {k: round(v, 4) for k, v in per.items()},
        "epochs": len(trained["hist"]),
        "finalLoss": trained["hist"][-1]["loss"],
        "nTrain": int(len(trained["hist"]) and True) and None,
        "curve": trained["hist"][::12],
        "labels": labels,
    }
    if extra:
        out.update(extra)
    out["nTest"] = int(len(yte))
    return out, acc, per


willay_pack = chaski_pack = c5050_pack = cr2_pack = None
willay_acc = chaski_acc = c5050_acc = cr2_acc = None
willay_per = chaski_per = c5050_per = cr2_per = None

if not KERNELS_ONLY:
    # ---------------------------------------------------------------------------
    # WILLAY — TELL (1) vs SILENCE (0)
    # features: inflate_lean, launder_gguf, lambda_proven, unlabeled_number, receipt
    # Unique cut: the mouth that refuses marketing. Not a mascot.
    # ---------------------------------------------------------------------------
    w_rows, w_labs = [], []
    for _ in range(140):
        w_rows.append(noisy([rng.uniform(0.0, 0.28), rng.uniform(0.0, 0.28), rng.uniform(0.0, 0.22), rng.uniform(0.0, 0.25), rng.uniform(0.72, 1.0)]))
        w_labs.append(1)
    for _ in range(50):
        w_rows.append(noisy([rng.uniform(0.7, 1.0), rng.uniform(0.0, 0.4), rng.uniform(0.0, 0.4), rng.uniform(0.2, 0.8), rng.uniform(0.0, 0.5)]))
        w_labs.append(0)
    for _ in range(50):
        w_rows.append(noisy([rng.uniform(0.0, 0.4), rng.uniform(0.7, 1.0), rng.uniform(0.0, 0.35), rng.uniform(0.2, 0.8), rng.uniform(0.0, 0.55)]))
        w_labs.append(0)
    for _ in range(50):
        w_rows.append(noisy([rng.uniform(0.0, 0.35), rng.uniform(0.0, 0.35), rng.uniform(0.75, 1.0), rng.uniform(0.1, 0.6), rng.uniform(0.0, 0.5)]))
        w_labs.append(0)
    for _ in range(50):
        w_rows.append(noisy([rng.uniform(0.0, 0.4), rng.uniform(0.0, 0.4), rng.uniform(0.0, 0.4), rng.uniform(0.7, 1.0), rng.uniform(0.0, 0.45)]))
        w_labs.append(0)
    for _ in range(40):
        w_rows.append(noisy([rng.uniform(0.35, 0.7), rng.uniform(0.3, 0.65), rng.uniform(0.2, 0.55), rng.uniform(0.3, 0.7), rng.uniform(0.45, 0.75)]))
        w_labs.append(0)

    wxtr, wytr, wxte, wyte = split_xy(w_rows, w_labs)
    willay = mlp_train(wxtr, wytr, h=8, k=2, epochs=280, lr=0.32)
    willay_pack, willay_acc, willay_per = pack_mlp(
        willay,
        wxte,
        wyte,
        ["SILENCE", "TELL"],
        extra={"nTrain": int(len(wytr)), "features": ["inflate_lean", "launder_gguf", "lambda_proven", "unlabeled_number", "receipt"]},
    )
    print("WILLAY holdout", willay_acc, "per", willay_per, "nTrain", len(wytr), "nTest", len(wyte))

    # ---------------------------------------------------------------------------
    # CHASKI lineage — CARRY (1) vs DROP (0)
    # Mix is the identity. We do not overwrite R1 with R2.
    # ---------------------------------------------------------------------------
    def chaski_data(carry_n: int, drop_n: int):
        rows, labs = [], []
        for _ in range(carry_n):
            rows.append(noisy([rng.uniform(0.65, 1.0), rng.uniform(0.6, 1.0), rng.uniform(0.0, 0.32), rng.uniform(0.0, 0.7), rng.uniform(0.55, 1.0)]))
            labs.append(1)
        n_unsigned = drop_n // 3
        for _ in range(n_unsigned):
            rows.append(noisy([rng.uniform(0.0, 0.35), rng.uniform(0.3, 1.0), rng.uniform(0.0, 0.6), rng.uniform(0.0, 0.8), rng.uniform(0.0, 0.7)]))
            labs.append(0)
        n_author = drop_n // 3
        for _ in range(n_author):
            rows.append(noisy([rng.uniform(0.3, 0.8), rng.uniform(0.3, 0.9), rng.uniform(0.7, 1.0), rng.uniform(0.2, 0.9), rng.uniform(0.2, 0.8)]))
            labs.append(0)
        for _ in range(drop_n - n_unsigned - n_author):
            rows.append(noisy([rng.uniform(0.2, 0.7), rng.uniform(0.0, 0.28), rng.uniform(0.2, 0.7), rng.uniform(0.0, 0.8), rng.uniform(0.0, 0.6)]))
            labs.append(0)
        return split_xy(rows, labs)

    def train_courier(name: str, carry_n: int, drop_n: int, mix: str):
        xtr, ytr, xte, yte = chaski_data(carry_n, drop_n)
        pack = mlp_train(xtr, ytr, h=8, k=2, epochs=260, lr=0.33)
        out, acc, per = pack_mlp(
            pack,
            xte,
            yte,
            ["DROP", "CARRY"],
            extra={
                "nTrain": int(len(ytr)),
                "mix": mix,
                "features": ["signed", "payload", "author_verb", "vision", "handle"],
            },
        )
        print(name, "holdout", acc, "per", per, "mix", mix, "nTrain", len(ytr), "nTest", len(yte))
        return out, acc, per

    chaski_pack, chaski_acc, chaski_per = train_courier("chaski", 180, 80, "70/30 carry/drop")
    c5050_pack, c5050_acc, c5050_per = train_courier("chaski-5050", 130, 130, "50/50 cutting")
    cr2_pack, cr2_acc, cr2_per = train_courier("chaski-r2", 90, 170, "35/65 drop-heavy R2")


# ---------------------------------------------------------------------------
# Kernel MEASURED smokes — SOFTWARE, not SGD
# ---------------------------------------------------------------------------
sys.path.insert(0, str(KERNELS.parent))
from kernels.yarqa import yarqa_attn, canal_bounds  # noqa: E402
from kernels.maskmod import maskmod_attn  # noqa: E402
from kernels.ouroboros import loop_tax  # noqa: E402
from kernels.nemo_rules import rule_check, RULE_IDS  # noqa: E402
from kernels.blocked import deny_by_default  # noqa: E402
from kernels.receipt_attn import tiled_attn  # noqa: E402
from kernels.block_kv import make_cache, witness_swap  # noqa: E402
from kernels.formulas import run_all, digest_run  # noqa: E402
from kernels.governed_norm import rms_norm  # noqa: E402
from kernels.lambda_gate import check_a1, check_a2, check_a3, check_a4, uniform_weights, wgm  # noqa: E402
from kernels.doctrine import DOCTRINE, proven_trust, advisory  # noqa: E402
from kernels.chain import UnifiedReceiptChain, DIGEST_NOTE  # noqa: E402

krng = np.random.default_rng(SEED)
S, D, N = 8, 4, 3
Q = krng.normal(size=(S, D))
K = krng.normal(size=(S, D))
V = krng.normal(size=(S, D))
_out, _probs, leaked = yarqa_attn(Q, K, V, n_canals=N)
assert leaked < 1e-12

_m_out, _m_probs, future_causal = maskmod_attn(Q, K, V, kind="causal")
_m_out, _m_probs, future_prefix = maskmod_attn(Q, K, V, kind="prefix")

tax = loop_tax([{"ok": False, "ms": 220}, {"ok": True, "ms": 900}], 1300, 4)

ok_r1, v_r1 = rule_check("how good is this?", "MMLU 92%")
ok_r4, v_r4 = rule_check("is lambda proven?", "Λ is a theorem, certified.")
ok_ok, v_ok = rule_check("how good?", "Unknown. Not yet measured.")

gate_block = deny_by_default(allow=False, hard_deny=False, lambda_pass=True)
gate_deny = deny_by_default(allow=True, hard_deny=True, lambda_pass=True)
gate_open = deny_by_default(allow=True, hard_deny=False, lambda_pass=True)

tiled = tiled_attn(Q, K, V, br=4, bc=4)
cache = make_cache(n_logical=8, n_physical=6, dim=4, seed=11)
w_diff = witness_swap(cache, 0, 1)
cache_same = make_cache(n_logical=8, n_physical=6, dim=4, seed=11)
w_same = witness_swap(cache_same, 0, 6)
oob = False
try:
    make_cache(n_logical=8, n_physical=6, dim=4, seed=11).swap(0, 99)
except ValueError:
    oob = True

rows = run_all(seed=11)
numeric_rows = [r for r in rows if r["family"] == "numeric"]
puriq_rows = [r for r in rows if r["family"] == "puriq_locked8"]
X = krng.normal(0.0, 1.0, size=(4, 8))
_y, unit_rms, _d = rms_norm(X, np.ones(8))
axes = 0.2 + krng.random(6) * 0.7
wts = uniform_weights(6)
chain = UnifiedReceiptChain()
chain.emit("khipu", "knot", {"i": 0})
chain.emit("khipu", "knot", {"i": 1})
chain_ok, chain_depth, _brk = chain.verify()

kernel_measures = {
    "yarqaLeaked": float(leaked),
    "maskmodCausalFutureMass": float(future_causal),
    "maskmodPrefixFutureMass": float(future_prefix),
    "ouroborosModelMs": tax["modelMs"],
    "ouroborosOverheadMs": tax["overheadMs"],
    "ouroborosOverheadLabel": tax["honesty"]["overheadMs"],
    "nemoR1CatchesUnlabeled": (not ok_r1) and ("R1_no_fabrication_label" in v_r1),
    "nemoR4CatchesTheorem": (not ok_r4) and ("R4_lambda_not_theorem" in v_r4),
    "nemoHonestUnknownPasses": ok_ok,
    "denyDefaultBlocks": gate_block["blocked"] is True and gate_block["output"] is None,
    "hardDenyDominates": gate_deny["blocked"] is True,
    "allowOpens": gate_open["blocked"] is False,
    "ruleIds": list(RULE_IDS),
    "bounds": canal_bounds(S, N).tolist(),
    "receiptAttnResidual": float(tiled.residual),
    "blockKvWitnessChanged": bool(w_diff["changed"]),
    "blockKvSamePhysicalUnchanged": not bool(w_same["changed"]),
    "blockKvFailClosed": oob,
    "formulasNumericOk": all(r["ok"] for r in numeric_rows),
    "formulasNumericN": len(numeric_rows),
    "formulasLocked8Ok": all(r["ok"] for r in puriq_rows),
    "formulasLocked8N": len(puriq_rows),
    "formulasLockedIds": [r["id"] for r in puriq_rows],
    "formulasDigest": digest_run(rows),
    "governedNormUnitRms": float(unit_rms),
    "lambdaA1": bool(check_a1(axes, wts)),
    "lambdaA2": bool(check_a2(axes, wts)),
    "lambdaA3": bool(check_a3(wts, 0.55)),
    "lambdaA4": bool(check_a4(axes, wts)),
    "lambdaZeroAxis": float(wgm(axes * np.array([1, 1, 0, 1, 1, 1]), wts)),
    "provenTrust": bool(proven_trust),
    "advisory": bool(advisory),
    "lockedDeclarations": int(DOCTRINE["lockedDeclarations"]),
    "uniqueAxioms": int(DOCTRINE["uniqueAxioms"]),
    "trackedSorries": int(DOCTRINE["trackedSorries"]),
    "digestAlgNote": DIGEST_NOTE,
    "chainVerify": bool(chain_ok),
    "chainDepth": int(chain_depth),
}
print("KERNELS", json.dumps({k: v for k, v in kernel_measures.items() if k not in ("bounds", "digestAlgNote", "formulasDigest")}))


# ---------------------------------------------------------------------------
# Merge into nano-weights.json (do not touch moons / 1.5B)
# ---------------------------------------------------------------------------
payload = json.loads(NANO.read_text())
payload["kernelMeasuredAt"] = datetime.now(timezone.utc).isoformat()
payload["kernelMeasures"] = kernel_measures
if not KERNELS_ONLY:
    payload["cohortTrainedAt"] = datetime.now(timezone.utc).isoformat()
    payload["willay"] = willay_pack
    payload["chaski"] = chaski_pack
    payload["chaski5050"] = c5050_pack
    payload["chaskiR2"] = cr2_pack

text = json.dumps(payload, indent=2)
dests = [NANO, SPACE_NANO, KIT_NANO]
if Path("/workspace/src/lib/nano-weights.json").exists():
    dests.append(Path("/workspace/src/lib/nano-weights.json"))
    dests.append(Path("/workspace/public/space/nano-weights.json"))
    dests.append(Path("/workspace/public/kit/nano-weights.json"))
seen: set[str] = set()
for dest in dests:
    key = str(dest.resolve()) if dest.exists() or dest.parent.exists() else str(dest)
    if key in seen:
        continue
    seen.add(key)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text)
    print("wrote", dest)


def save_mlp(name: str, pack: dict, extra: dict | None = None):
    kw = dict(
        w1=np.asarray(pack["w1"], dtype=np.float64),
        b1=np.asarray(pack["b1"], dtype=np.float64),
        w2=np.asarray(pack["w2"], dtype=np.float64),
        b2=np.asarray(pack["b2"], dtype=np.float64),
        holdoutAcc=np.float64(pack["holdoutAcc"]),
        seed=np.int64(SEED),
    )
    if extra:
        kw.update(extra)
    path = WEIGHTS / name
    np.savez_compressed(path, **kw)
    print("wrote", path, path.stat().st_size)


if not KERNELS_ONLY:
    WEIGHTS.mkdir(parents=True, exist_ok=True)
    save_mlp("willay.npz", willay_pack)
    save_mlp("chaski.npz", chaski_pack)
    save_mlp("chaski_5050.npz", c5050_pack)
    save_mlp("chaski_r2.npz", cr2_pack)

summary = {
    "kernelsOnly": KERNELS_ONLY,
    "kernels": {
        "yarqaLeaked": kernel_measures["yarqaLeaked"],
        "maskmodCausalFutureMass": kernel_measures["maskmodCausalFutureMass"],
        "receiptAttnResidual": kernel_measures["receiptAttnResidual"],
        "blockKvWitnessChanged": kernel_measures["blockKvWitnessChanged"],
        "formulasNumericOk": kernel_measures["formulasNumericOk"],
        "formulasLocked8Ok": kernel_measures["formulasLocked8Ok"],
        "governedNormUnitRms": kernel_measures["governedNormUnitRms"],
        "lambdaA1": kernel_measures["lambdaA1"],
        "provenTrust": kernel_measures["provenTrust"],
        "ouroborosModelMs": kernel_measures["ouroborosModelMs"],
        "nemoR1": kernel_measures["nemoR1CatchesUnlabeled"],
        "nemoR4": kernel_measures["nemoR4CatchesTheorem"],
    },
}
if not KERNELS_ONLY:
    summary["willay"] = {"holdoutAcc": willay_pack["holdoutAcc"], "perClass": willay_pack["perClass"]}
    summary["chaski"] = {"holdoutAcc": chaski_pack["holdoutAcc"], "perClass": chaski_pack["perClass"], "mix": chaski_pack["mix"]}
    summary["chaski-5050"] = {"holdoutAcc": c5050_pack["holdoutAcc"], "perClass": c5050_pack["perClass"], "mix": c5050_pack["mix"]}
    summary["chaski-r2"] = {"holdoutAcc": cr2_pack["holdoutAcc"], "perClass": cr2_pack["perClass"], "mix": cr2_pack["mix"]}
metrics_dir = Path("/workspace/space-export")
if metrics_dir.exists() or Path("/workspace").exists():
    (Path("/workspace/space-export") / "cohort-metrics.json").parent.mkdir(exist_ok=True)
    (Path("/workspace/space-export") / "cohort-metrics.json").write_text(json.dumps(summary, indent=2))
print("SUMMARY", json.dumps(summary, indent=2))
print("did not retrain 1.5B. ROADMAP empty. STUB empty. Energy UNAVAILABLE.")
