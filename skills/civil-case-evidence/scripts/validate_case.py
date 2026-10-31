"""Validate traceability records, never legal truth. Python 3.10+, stdlib only."""
import argparse
import hashlib
import json
import sys
from datetime import datetime


def validate(data, require_reviewed=False):
    errors = []
    def check(ok, message):
        if not ok:
            errors.append(message)
    def text(value):
        return isinstance(value, str) and bool(value.strip())
    if not isinstance(data, dict):
        return ["root must be an object"]
    check(data.get("schema_version") == "1.0", "schema_version must be 1.0")
    check(data.get("status") in ("provisional", "reviewed"), "invalid status")
    check(not require_reviewed or data.get("status") == "reviewed", "reviewed required")
    for field in ("case_id", "jurisdiction", "relevant_time", "question"):
        check(text(data.get(field)), field + " required")
    tables = {}
    for name in ("facts", "sources", "claims", "issues", "retrievals"):
        rows = data.get(name)
        if not isinstance(rows, list):
            errors.append(name + " must be an array")
            rows = []
        tables[name] = {}
        for row in rows:
            if not isinstance(row, dict) or not text(row.get("id")):
                errors.append(name + " record needs an id")
                continue
            rid = row["id"]
            check(rid not in tables[name], name + ": duplicate " + rid)
            tables[name][rid] = row
    for name in ("facts", "claims", "issues"):
        check(bool(tables[name]), name + " must not be empty")
    def refs(row, key, table, nonempty=False):
        value = row.get(key)
        if not isinstance(value, list) or not all(text(v) for v in value):
            errors.append(row["id"] + ": " + key + " must be an ID array")
            return []
        check(not nonempty or bool(value), row["id"] + ": " + key + " empty")
        for ref in value:
            check(ref in tables[table], row["id"] + ": unknown " + key + " " + ref)
        return [tables[table][v] for v in value if v in tables[table]]
    for f in tables["facts"].values():
        check(f.get("status") in ("stated", "disputed", "unknown"), f["id"] + ": invalid fact status")
        check(text(f.get("text")), f["id"] + ": fact text required")
        check(text(f.get("locator")), f["id"] + ": material locator or explicit gap required")
    for s in tables["sources"].values():
        sid = s["id"]
        check(s.get("kind") in ("norm", "case", "literature", "method"), sid + ": invalid kind")
        check(s.get("verification") in ("verified", "unverified", "failed"), sid + ": invalid verification")
        check(s.get("applicability") in ("applicable", "inapplicable", "uncertain"), sid + ": invalid applicability")
        for key in ("title", "locator", "version", "applicability_reason"):
            check(text(s.get(key)), sid + ": " + key + " required")
        if s.get("verification") == "verified":
            for key in ("url_or_path", "accessed_at", "excerpt", "excerpt_sha256"):
                check(text(s.get(key)), sid + ": " + key + " required for verified source")
            try:
                datetime.fromisoformat(s.get("accessed_at", "").replace("Z", "+00:00"))
            except (ValueError, TypeError, AttributeError):
                errors.append(sid + ": accessed_at must be ISO date/time")
            excerpt = s.get("excerpt")
            if isinstance(excerpt, str):
                check(hashlib.sha256(excerpt.encode("utf-8")).hexdigest() == s.get("excerpt_sha256"), sid + ": excerpt hash mismatch")
    for q in tables["retrievals"].values():
        for key in ("query", "tool", "at", "scope", "outcome"):
            check(text(q.get(key)), q["id"] + ": " + key + " required")
        refs(q, "source_ids", "sources")
    covered = set()
    for c in tables["claims"].values():
        for key in ("direction", "remedy", "nature", "decision_reason", "relationship"):
            check(text(c.get(key)), c["id"] + ": " + key + " required")
        check(c.get("decision") in ("included", "excluded", "pending"), c["id"] + ": invalid decision")
        if data.get("status") == "reviewed":
            check(c.get("decision") != "pending", c["id"] + ": pending claim cannot be reviewed")
        issues = refs(c, "issue_ids", "issues", nonempty=True)
        covered.update(i["id"] for i in issues)
    for i in tables["issues"].values():
        iid = i["id"]
        check(iid in covered, iid + ": issue has no claim")
        for key in ("question", "proposition", "application", "counterargument", "conclusion"):
            check(text(i.get(key)), iid + ": " + key + " required")
        facts = refs(i, "fact_ids", "facts")
        sources = refs(i, "source_ids", "sources")
        result = i.get("result")
        check(result in ("supported", "not_supported", "conditional", "unresolved"), iid + ": invalid result")
        if result in ("conditional", "unresolved") or any(f.get("status") != "stated" for f in facts):
            check(text(i.get("conditions")), iid + ": conditions required")
        if any(f.get("status") in ("unknown", "disputed") for f in facts):
            check(result in ("conditional", "unresolved"), iid + ": uncertain material facts require conditional result")
        if data.get("status") == "reviewed":
            check(result != "unresolved", iid + ": unresolved issue cannot be reviewed")
            check(bool(sources), iid + ": reviewed issue needs sources")
            check(any(s.get("kind") != "method" for s in sources), iid + ": methodology alone is not legal authority")
            check(all(s.get("verification") == "verified" and s.get("applicability") == "applicable" for s in sources), iid + ": reviewed issue needs verified applicable sources")
    review = data.get("review")
    if not isinstance(review, dict):
        errors.append("review must be an object")
    else:
        check(isinstance(review.get("open_items"), list), "review.open_items must be an array")
        if data.get("status") == "reviewed":
            check(review.get("open_items") == [], "reviewed cannot have open items")
            for key in ("source_support", "temporal_scope", "fact_fidelity", "alternatives", "remedy_consistency"):
                check(text(review.get(key)), "review evidence required: " + key)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_file")
    parser.add_argument("--require-reviewed", action="store_true")
    args = parser.parse_args()
    try:
        with open(args.case_file, encoding="utf-8") as f:
            errors = validate(json.load(f), args.require_reviewed)
    except (OSError, ValueError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2
    if errors:
        print("\n".join("ERROR: " + e for e in errors), file=sys.stderr)
        return 1
    print("Record checks passed; external source authenticity and legal correctness NOT verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
