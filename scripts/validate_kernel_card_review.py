# SPDX-License-Identifier: Apache-2.0
"""Validate the offline kernel-card review without loading code or publishing.

This review format belongs to Atelier. It does not expand a kernel's release
contract. A caller may compare separately captured current parents, but the
validator makes no network request and grants no publication authorization.
"""
import argparse
import ast
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW = ROOT / "cards/reviews/2026-09-30/review.json"
EXPECTED_SLUGS = {"szl-blocked", "szl-provctl", "szl-govsign", "szl-invariants", "szl-ouroboros", "szl-formulas"}
SHA = re.compile(r"[0-9a-f]{40}")
WEIGHT = re.compile(r"(?:^|/)model\.joblib$|\.(?:safetensors|gguf|onnx|pt|pth|bin)$", re.I)


class ReviewError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ReviewError(message)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_bound(root, binding, expected_path):
    require(binding.get("path") == expected_path, "Unexpected review target path")
    root = Path(root).resolve()
    path = (root / expected_path).resolve()
    require(path.is_relative_to(root), "Review path escapes publisher source")
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == binding.get("sha256"), f"Content digest mismatch: {expected_path}")
    return data


def validate_proposal(baseline, proposal, row):
    require(proposal.get("schema") == baseline.get("schema"), "Existing provenance schema was changed")
    history_keys = ("model", "claims", "source_of_record", "public_github")
    historical = {key: baseline.get(key, {}) for key in history_keys}
    require(proposal.get("historical_provenance_before_correction") == historical, "Historical provenance was changed or lost")
    allowed = set(history_keys) | {"historical_provenance_before_correction", "current_review"}
    require(set(proposal) - allowed == set(baseline) - allowed, "Unrelated provenance fields added or removed")
    for key in set(baseline) - allowed:
        require(proposal.get(key) == baseline[key], f"Historical evidence changed: {key}")
    old_model = copy.deepcopy(baseline["model"])
    new_model = copy.deepcopy(proposal["model"])
    require(new_model.get("id") == row["repo_id"], "Model identity mismatch")
    require(new_model.get("trained_weights_present") is False, "Current weights must be absent")
    require(new_model.get("artifact_kind") == "kernel-code-and-configuration", "Current artifact class is not code-only")
    for key in ("trained_weights_present", "artifact_kind"):
        old_model.pop(key, None)
        new_model.pop(key, None)
    old_surrogate = old_model.pop("surrogate")
    new_surrogate = new_model.pop("surrogate")
    require(old_model == new_model, "Unrelated model properties changed")
    additions = {
        "artifact_present_at_reviewed_revision": False,
        "availability": "ABSENT_AT_REVIEWED_REVISION",
        "replay_status": "BLOCKED_MISSING_ARTIFACT",
        "metrics_scope": "HISTORICAL_RECEIPT_ONLY_NOT_RERUN",
    }
    require(new_surrogate == {**old_surrogate, **additions}, "Surrogate history or absence scope changed")
    old_claims = baseline.get("claims", {})
    new_claims = proposal.get("claims", {})
    require(set(new_claims) == set(old_claims) | {"trained_model", "weights_present", "github_repository_parity"}, "Unreviewed claim fields added or removed")
    require(new_claims.get("trained_model") == "NOT_CLAIMED_CURRENT_REVISION", "Trained model claim was promoted")
    require(new_claims.get("weights_present") == "NONE_AT_REVIEWED_REVISION", "Weight absence is not revision scoped")
    require(new_claims.get("github_repository_parity") == "NOT_VERIFIED_THIS_REVIEW", "Source parity must not be asserted")
    for key in set(old_claims) - {"trained_model", "weights_present", "github_repository_parity"}:
        require(new_claims.get(key) == old_claims[key], f"Unrelated historical claim changed: {key}")
    review = proposal["current_review"]
    for key, expected in {
        "hf_model_revision": row["model"]["revision"],
        "hf_kernel_revision": row["kernel"]["revision"],
        "github_source_revision": row["source"]["revision"],
        "source_mirror_parity": "UNVERIFIED",
        "historical_records_retained": True,
        "weights_downloaded": False,
        "code_executed": False,
        "signatures_verified": False,
    }.items():
        require(review.get(key) == expected, f"Current observation mismatch: {key}")
    source = proposal["source_of_record"]
    require(source.get("platform") == "github" and source.get("repository") == row["source"]["repository"], "Current canonical source mismatch")
    require(source.get("observed_revision") == row["source"]["revision"], "Current GitHub source is unbound")
    require(source.get("source_to_hub_release_binding") == "NOT_VERIFIED_THIS_REVIEW", "Observed source was promoted to a release")
    require(proposal["public_github"].get("state") == "PUBLIC_REPOSITORY_REACHABLE_AT_REVIEW", "Historical repository absence was retained as current")


def python_snippets(card):
    return re.findall(r"```python\n(.*?)```", card, flags=re.S)


def validate_card(card, row):
    require(card.startswith("---\n"), "Card front matter missing")
    require("license: apache-2.0" in card and "library_name: kernels" in card, "Card artifact metadata mismatch")
    require("maturity: SOFTWARE_LIMITED" in card and "trained_weights_present: false" in card, "Card maturity or weights promoted")
    require("source_mirror_parity: NOT_VERIFIED_THIS_REVIEW" in card, "Card source parity promoted")
    for kind in ("source", "model", "kernel"):
        require(row[kind]["revision"] in card, f"Missing {kind} identity in card")
    require("./card/holo-banner.svg" not in card, "Hub-only relative banner breaks publisher card")
    require("Nobody else ships" not in card and "| Leader |" not in card, "Unsupported comparison retained")
    require("verified publication evidence" in card and "qualified by the relevant release" in card, "Release/client qualification limit omitted")
    snippets = python_snippets(card)
    require(bool(snippets), "Source-informed Python example missing")
    for snippet in snippets:
        tree = ast.parse(snippet)
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "get_kernel"]
        require(len(calls) == 1, "Example has an unexpected kernel loader")
        call = calls[0]
        require(call.args and isinstance(call.args[0], ast.Constant) and call.args[0].value == row["repo_id"], "Python example loads a different repository")
        revision = next((kw.value for kw in call.keywords if kw.arg == "revision"), None)
        require(isinstance(revision, ast.Name) and revision.id == "revision", "Python example uses a mutable or unqualified revision")
        require("SZL_VERIFIED_KERNEL_REVISION" in snippet and 'r"[0-9a-f]{40}"' in snippet, "Python revision input gate missing")
        used = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "kernel"}
        require(used == set(row["api_review"]["documented_names"]), "Python API differs from immutable static source review")


def validate_review(root=ROOT, manifest_path=DEFAULT_REVIEW, observed_parents=None):
    review = load_json(manifest_path)
    require(review.get("schema") == "szl.kernel-card-review/v1", "Unsupported offline review schema")
    require(review.get("publication_authorized") is False and review.get("state") == "SOURCE_REVIEW_ONLY_NOT_PUBLISHED", "Offline review was promoted to publication authorization")
    require(review.get("allowed_hub_paths") == ["README.md", "MODEL_PROVENANCE.json"], "Hub target scope broadened")
    require(review.get("protected_hub_paths") == ["TRAINING_RECEIPT.json"], "Training receipt protection removed")
    artifacts = review.get("artifacts", [])
    require(len(artifacts) == 6 and {r["repo_id"].split("/")[-1] for r in artifacts} == EXPECTED_SLUGS, "Expected six distinct review artifacts")
    if observed_parents is not None:
        require(set(observed_parents) == {r["repo_id"] for r in artifacts}, "Parent comparison must cover all six artifacts")
    for row in artifacts:
        slug = row["repo_id"].split("/")[-1]
        require(row["repo_id"] == "SZLHOLDINGS/" + slug, "Unexpected artifact owner")
        for kind in ("source", "model", "kernel"):
            require(SHA.fullmatch(row[kind]["revision"]) is not None, "Expected immutable revision")
        require(len({row[k]["revision"] for k in ("source", "model", "kernel")}) == 3, "Source, model mirror and kernel identities were conflated")
        require(row["source"]["repository"] == "szl-holdings/" + slug, "Unexpected canonical source")
        require(row["model"]["repo_type"] == "model" and row["kernel"]["repo_type"] == "kernel", "Model/kernel repository type mismatch")
        paths = row["model"]["listed_paths"]
        require(len(paths) == len(set(paths)) and "MODEL_PROVENANCE.json" in paths and "TRAINING_RECEIPT.json" in paths, "Incomplete reviewed path inventory")
        require(not any(WEIGHT.search(path) for path in paths), "Weight absence contradicted by reviewed inventory")
        require(row["kernel"].get("client_qualification") == "NOT_PERFORMED" and row["kernel"].get("approved_publication") == "NOT_ESTABLISHED", "Observed kernel promoted to qualified release")
        require(row["api_review"]["method"] == "AST_ONLY_NO_IMPORT_OR_EXECUTION", "Static API review promoted to runtime evidence")
        receipt = row["protected_receipt"]
        require(receipt["path_in_repo"] == "TRAINING_RECEIPT.json" and receipt["revision"] == row["model"]["revision"], "Receipt identity drift")
        require(receipt["action"] == "PRESERVE_BYTES_NOT_A_PUBLICATION_TARGET", "Historical receipt became a write target")
        require(re.fullmatch(r"[0-9a-f]{64}", receipt["sha256"]) is not None, "Receipt digest missing")
        base = "cards/reviews/2026-09-30/" + slug
        baseline = json.loads(read_bound(root, row["baseline_provenance"], base + ".MODEL_PROVENANCE.baseline.json"))
        proposal = json.loads(read_bound(root, row["proposed_provenance"], base + ".MODEL_PROVENANCE.proposed.json"))
        card = read_bound(root, row["card"], "cards/" + slug + ".md").decode("utf-8")
        validate_proposal(baseline, proposal, row)
        validate_card(card, row)
        if observed_parents is not None:
            require(observed_parents[row["repo_id"]] == {
                "github_source_revision": row["source"]["revision"],
                "hf_model_revision": row["model"]["revision"],
                "hf_kernel_revision": row["kernel"]["revision"],
            }, f"Observed parent drift: {row['repo_id']}")
    return {
        "status": "OFFLINE_REVIEW_VALID",
        "artifacts": len(artifacts),
        "supplied_parent_comparison": "MATCHED" if observed_parents is not None else "NOT_REQUESTED",
        "remote_mutations": 0,
        "remote_kernel_execution": False,
        "hub_published": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--observed-parents", type=Path, help="Separately captured parent JSON; does not authorize publication")
    args = parser.parse_args()
    try:
        result = validate_review(manifest_path=args.manifest, observed_parents=load_json(args.observed_parents) if args.observed_parents else None)
    except (ReviewError, OSError, KeyError, TypeError, json.JSONDecodeError, SyntaxError) as exc:
        parser.exit(1, f"REVIEW_BLOCKED: {exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
