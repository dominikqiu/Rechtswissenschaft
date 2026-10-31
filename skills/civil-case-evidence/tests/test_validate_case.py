"""Synthetic record tests only: no asserted legal rules or real case data."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validator", ROOT / "scripts/validate_case.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture():
    excerpt = "SYNTHETIC TEST CONTENT, NOT LAW"
    return {
        "schema_version": "1.0", "case_id": "synthetic", "status": "reviewed",
        "jurisdiction": "synthetic", "relevant_time": "2020-01-01", "question": "Test only",
        "facts": [{"id": "F1", "text": "Synthetic fact", "status": "stated", "locator": "test:1"}],
        "sources": [{"id": "S1", "kind": "norm", "title": "Synthetic norm", "locator": "test:1",
                     "version": "historical-2020", "verification": "verified", "applicability": "applicable",
                     "applicability_reason": "Synthetic transition rule for test",
                     "url_or_path": "test:fixture", "accessed_at": "2026-10-31", "excerpt": excerpt,
                     "excerpt_sha256": hashlib.sha256(excerpt.encode()).hexdigest()}],
        "claims": [{"id": "C1", "direction": "A to B", "remedy": "synthetic", "nature": "claim",
                    "decision": "included", "decision_reason": "test", "relationship": "standalone", "issue_ids": ["I1"]}],
        "issues": [{"id": "I1", "question": "test", "proposition": "test", "application": "test",
                    "counterargument": "test", "conclusion": "test", "result": "supported",
                    "fact_ids": ["F1"], "source_ids": ["S1"]}],
        "retrievals": [{"id": "R1", "query": "test", "tool": "synthetic", "at": "2026-10-31",
                        "scope": "test", "outcome": "fixture", "source_ids": ["S1"]}],
        "review": {"open_items": [], **{k: "Synthetic review I1" for k in
                   ("source_support", "temporal_scope", "fact_fidelity", "alternatives", "remedy_consistency")}}
    }


class ValidatorTest(unittest.TestCase):
    def test_historical_applicable_version_allowed(self):
        self.assertEqual(m.validate(fixture(), True), [])

    def test_unknown_fact_requires_branch(self):
        d = fixture()
        d["facts"][0]["status"] = "unknown"
        self.assertTrue(m.validate(d))
        d["issues"][0].update(result="conditional", conditions="If fact is established")
        self.assertEqual(m.validate(d), [])

    def test_unverified_source_cannot_be_reviewed(self):
        d = fixture()
        d["sources"][0]["verification"] = "unverified"
        self.assertTrue(m.validate(d))
        d["status"] = "provisional"
        self.assertEqual(m.validate(d), [])
        self.assertTrue(m.validate(d, True))

    def test_bad_applicability_and_hash(self):
        for field, value in (("applicability", "uncertain"), ("excerpt_sha256", "incorrect"), ("kind", "method")):
            with self.subTest(field=field):
                d = fixture()
                d["sources"][0][field] = value
                self.assertTrue(m.validate(d))

    def test_broken_links_and_duplicates(self):
        d = fixture()
        d["issues"][0]["source_ids"] = ["missing"]
        self.assertTrue(m.validate(d))
        d = fixture()
        d["facts"].append(copy.deepcopy(d["facts"][0]))
        self.assertTrue(m.validate(d))

    def test_pending_or_unresolved_blocks_review(self):
        d = fixture()
        d["claims"][0]["decision"] = "pending"
        self.assertTrue(m.validate(d))
        d = fixture()
        d["issues"][0].update(result="unresolved", conditions="not known")
        self.assertTrue(m.validate(d))
        d = fixture()
        d["review"]["open_items"] = ["missing evidence"]
        self.assertTrue(m.validate(d))

    def test_malformed_records_fail_cleanly(self):
        for d in (None, [], {}, {"facts": [None]}, {"status": []}):
            with self.subTest(data=d):
                self.assertTrue(m.validate(d))

    def test_empty_template_rejected(self):
        d = json.loads((ROOT / "examples/case-template.json").read_text())
        self.assertTrue(m.validate(d))

    def test_cli_exit_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "case.json"
            for content, expected in ((json.dumps(fixture()), 0), ("{}", 1), ("{", 2)):
                p.write_text(content)
                result = subprocess.run([sys.executable, str(ROOT / "scripts/validate_case.py"), str(p)], capture_output=True)
                self.assertEqual(result.returncode, expected)


if __name__ == "__main__":
    unittest.main()
