# SPDX-License-Identifier: Apache-2.0
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/validate_kernel_card_review.py"
spec = importlib.util.spec_from_file_location("kernel_card_review", MODULE_PATH)
review_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review_module)
MANIFEST_PATH = ROOT / "cards/reviews/2026-09-30/review.json"


class KernelCardReviewTests(unittest.TestCase):
    def setUp(self):
        self.review = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.temp = tempfile.TemporaryDirectory(prefix="atelier-card-review-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for row in self.review["artifacts"]:
            for kind in ("card", "baseline_provenance", "proposed_provenance"):
                path = row[kind]["path"]
                destination = self.root / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / path, destination)
        self.manifest = self.root / "review.json"

    def validate(self, parents=None):
        self.manifest.write_text(json.dumps(self.review), encoding="utf-8")
        return review_module.validate_review(self.root, self.manifest, parents)

    def edit_proposal(self, change, artifact=0):
        row = self.review["artifacts"][artifact]
        binding = row["proposed_provenance"]
        path = self.root / binding["path"]
        proposal = json.loads(path.read_text(encoding="utf-8"))
        change(proposal)
        data = (json.dumps(proposal, indent=2) + "\n").encode()
        path.write_bytes(data)
        binding["sha256"] = hashlib.sha256(data).hexdigest()

    def parents(self):
        return {row["repo_id"]: {
            "github_source_revision": row["source"]["revision"],
            "hf_model_revision": row["model"]["revision"],
            "hf_kernel_revision": row["kernel"]["revision"],
        } for row in self.review["artifacts"]}

    def test_six_exact_proposals_validate_without_publication_claim(self):
        result = self.validate()
        self.assertEqual(result["status"], "OFFLINE_REVIEW_VALID")
        self.assertEqual(result["artifacts"], 6)
        self.assertFalse(result["hub_published"])
        self.assertFalse(result["remote_kernel_execution"])

    def test_corrupt_payload_fails_digest_check(self):
        row = self.review["artifacts"][0]
        (self.root / row["card"]["path"]).write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(review_module.ReviewError, "digest mismatch"):
            self.validate()

    def test_rehashed_payload_cannot_erase_historical_provenance(self):
        self.edit_proposal(lambda proposal: proposal["historical_provenance_before_correction"].clear())
        with self.assertRaisesRegex(review_module.ReviewError, "Historical provenance"):
            self.validate()

    def test_rehashed_payload_cannot_modify_surrogate_metrics(self):
        self.edit_proposal(lambda proposal: proposal["model"]["surrogate"].update({"sha256": "0" * 64}))
        with self.assertRaisesRegex(review_module.ReviewError, "Surrogate history"):
            self.validate()

    def test_rehashed_payload_cannot_rewrite_historical_test_results(self):
        self.edit_proposal(lambda proposal: proposal["verification"].update({"tests": "100%"}), artifact=4)
        with self.assertRaisesRegex(review_module.ReviewError, "Historical evidence"):
            self.validate()

    def test_weight_inventory_cannot_disagree_with_absence_claim(self):
        self.review["artifacts"][0]["model"]["listed_paths"].append("model.joblib")
        with self.assertRaisesRegex(review_module.ReviewError, "Weight absence"):
            self.validate()

    def test_model_mirror_sha_cannot_become_first_class_kernel_sha(self):
        row = self.review["artifacts"][0]
        row["kernel"]["revision"] = row["model"]["revision"]
        with self.assertRaisesRegex(review_module.ReviewError, "identities were conflated"):
            self.validate()

    def test_observed_kernel_cannot_be_promoted_to_qualified_release(self):
        self.review["artifacts"][0]["kernel"]["approved_publication"] = "APPROVED"
        with self.assertRaisesRegex(review_module.ReviewError, "qualified release"):
            self.validate()

    def test_offline_review_cannot_authorize_publication(self):
        self.review["publication_authorized"] = True
        with self.assertRaisesRegex(review_module.ReviewError, "publication authorization"):
            self.validate()

    def test_historical_receipt_cannot_become_a_write_target(self):
        self.review["allowed_hub_paths"].append("TRAINING_RECEIPT.json")
        with self.assertRaisesRegex(review_module.ReviewError, "scope broadened"):
            self.validate()

    def test_complete_separately_supplied_parent_snapshot_matches(self):
        self.assertEqual(self.validate(self.parents())["supplied_parent_comparison"], "MATCHED")

    def test_parent_drift_fails_closed(self):
        parents = self.parents()
        parents[self.review["artifacts"][0]["repo_id"]]["hf_model_revision"] = "f" * 40
        with self.assertRaisesRegex(review_module.ReviewError, "Observed parent drift"):
            self.validate(parents)

    def test_partial_parent_snapshot_is_rejected(self):
        parents = self.parents()
        parents.pop(next(iter(parents)))
        with self.assertRaisesRegex(review_module.ReviewError, "cover all six"):
            self.validate(parents)

    def test_all_python_examples_stop_before_loader_on_invalid_revision(self):
        def unexpected_load(*args, **kwargs):
            self.fail("An unqualified or malformed revision reached the remote loader")

        kernel_stub = types.ModuleType("kernels")
        kernel_stub.get_kernel = unexpected_load
        for row in self.review["artifacts"]:
            card = (ROOT / row["card"]["path"]).read_text(encoding="utf-8")
            for snippet in review_module.python_snippets(card):
                for value in ("", "main", "x" * 40, "a" * 39):
                    with self.subTest(repo=row["repo_id"], revision=value):
                        with patch.dict(sys.modules, {"kernels": kernel_stub}), patch.dict(os.environ, {"SZL_VERIFIED_KERNEL_REVISION": value}):
                            with self.assertRaises(ValueError):
                                exec(compile(snippet, row["card"]["path"], "exec"), {})

    def test_catalog_and_index_align_with_the_six_source_cards(self):
        catalog = json.loads((ROOT / "models.json").read_text(encoding="utf-8"))
        self.assertEqual(len(catalog["models"]), 40)
        index = (ROOT / "cards/INDEX.md").read_text(encoding="utf-8")
        for row in self.review["artifacts"]:
            slug = row["repo_id"].split("/")[-1]
            record = next(x for x in catalog["models"] if x["slug"] == slug)
            self.assertEqual(record["weights"], "none")
            self.assertFalse(record["trained"])
            self.assertIsNone(record["play"])
            self.assertEqual(record["github"]["repo"], row["source"]["repository"])
            self.assertTrue(all(record[key] == "" for key in ("anthropic", "nvidia", "unsloth")))
            self.assertIn(record["oneLiner"], index)
            self.assertTrue(any(row["source"]["revision"] in value for value in record["files"]))
            self.assertTrue(any("TRAINING_RECEIPT.json" in value and row["model"]["revision"] in value for value in record["files"]))


if __name__ == "__main__":
    unittest.main()
