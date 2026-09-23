#!/usr/bin/env python3
"""
Semantic structural linter for the SpaceWire Spec2RTL repository.

G1 checks:
- YAML parse
- unique requirement / contract / decision / issue / test / invariant IDs
- no dangling SPW / BC / DEC / CR references
- every contract has source requirement mappings
- every in-scope requirement is mapped to at least one contract
- Encoding §5.4 coverage count matches the requirement source file
- pre-Golden vectors reference valid contracts and have expected behavior
- uppercase ontology entity references used as subject/result are declared
- ontology relation subjects and plain-uppercase relation objects are declared
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    raise

ROOT = Path(__file__).resolve().parents[1]
YAML_DIRS = ("ontology", "requirements", "contracts", "verification", "traceability", "rtl_contract")
ID_PATTERNS = {
    "requirement": re.compile(r"(?<![A-Za-z0-9_-])SPW-[A-Za-z0-9_.-]+\b"),
    "contract": re.compile(r"(?<![A-Za-z0-9_-])BC-[A-Za-z0-9_.-]+\b"),
    "decision": re.compile(r"(?<![A-Za-z0-9_-])DEC-[A-Za-z0-9_.-]+\b"),
    "issue": re.compile(r"(?<![A-Za-z0-9_-])CR-[A-Za-z0-9_.-]+\b"),
}
ENTITY_RE = re.compile(r"^[A-Z][A-Z0-9_]+$")


def load_yaml(path: Path, errors: list[str]) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        errors.append(f"YAML_PARSE {path.relative_to(ROOT)}: {e}")
        return None


def iter_scalars(node: Any):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from iter_scalars(k)
            yield from iter_scalars(v)
    elif isinstance(node, list):
        for v in node:
            yield from iter_scalars(v)
    elif isinstance(node, (str, int, float, bool)):
        yield str(node)


def collect_prefixed_ids(node: Any, prefix: str) -> list[str]:
    out: list[str] = []
    if isinstance(node, dict):
        v = node.get("id")
        if isinstance(v, str) and v.startswith(prefix):
            out.append(v)
        for x in node.values():
            out.extend(collect_prefixed_ids(x, prefix))
    elif isinstance(node, list):
        for x in node:
            out.extend(collect_prefixed_ids(x, prefix))
    return out


def refs_in_doc(node: Any, pattern: re.Pattern[str]) -> set[str]:
    refs: set[str] = set()
    for s in iter_scalars(node):
        refs.update(pattern.findall(s))
    return refs


def flatten_entity_refs(value: Any) -> list[str]:
    vals = value if isinstance(value, list) else [value]
    return [x for x in vals if isinstance(x, str) and ENTITY_RE.fullmatch(x)]


def walk_dicts(node: Any):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk_dicts(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_dicts(v)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    yaml_files: list[Path] = []
    for d in YAML_DIRS:
        p = ROOT / d
        if p.exists():
            yaml_files.extend(sorted(p.rglob("*.yaml")))
            yaml_files.extend(sorted(p.rglob("*.yml")))

    docs: dict[Path, Any] = {p: load_yaml(p, errors) for p in yaml_files}

    req_docs = {p: d for p, d in docs.items() if p.parts[-2] == "requirements" and isinstance(d, dict)}
    contract_docs = {p: d for p, d in docs.items() if p.parts[-2] == "contracts" and isinstance(d, dict)}

    requirement_ids: list[str] = []
    for d in req_docs.values():
        for r in d.get("requirements", []) or []:
            if isinstance(r, dict) and isinstance(r.get("id"), str):
                requirement_ids.append(r["id"])

    contract_ids = [
        d["id"]
        for d in contract_docs.values()
        if isinstance(d.get("id"), str) and d["id"].startswith("BC-")
    ]

    decision_ids: list[str] = []
    issue_ids: list[str] = []
    test_ids: list[str] = []
    invariant_ids: list[str] = []
    for d in docs.values():
        if d is None:
            continue
        decision_ids.extend(collect_prefixed_ids(d, "DEC-"))
        issue_ids.extend(collect_prefixed_ids(d, "CR-"))
        test_ids.extend(collect_prefixed_ids(d, "TV-"))
        invariant_ids.extend(collect_prefixed_ids(d, "INV-"))

    for label, ids in [
        ("REQUIREMENT_ID", requirement_ids),
        ("CONTRACT_ID", contract_ids),
        ("DECISION_ID", decision_ids),
        ("ISSUE_ID", issue_ids),
        ("TEST_ID", test_ids),
        ("INVARIANT_ID", invariant_ids),
    ]:
        duplicates = sorted(k for k, n in Counter(ids).items() if n > 1)
        for x in duplicates:
            errors.append(f"DUPLICATE_{label}: {x}")

    declared = {
        "requirement": set(requirement_ids),
        "contract": set(contract_ids),
        "decision": set(decision_ids),
        "issue": set(issue_ids),
    }

    for p, d in docs.items():
        if d is None:
            continue
        for kind, pat in ID_PATTERNS.items():
            for ref in refs_in_doc(d, pat):
                if ref not in declared[kind]:
                    errors.append(f"DANGLING_{kind.upper()} {p.relative_to(ROOT)}: {ref}")

    # Every contract must explicitly map back to atomic requirements.
    req_to_contracts: dict[str, set[str]] = defaultdict(set)
    for p, d in contract_docs.items():
        cid = d.get("id")
        refs = d.get("requirements")
        if not isinstance(refs, list) or not refs:
            errors.append(f"CONTRACT_WITHOUT_REQUIREMENTS {p.relative_to(ROOT)}: {cid}")
            continue
        for rid in refs:
            if isinstance(rid, str):
                req_to_contracts[rid].add(str(cid))

    # Every requirement artifact currently committed to the semantic baseline
    # must map to at least one behavior contract.  This keeps new Data Link,
    # Network and Router slices from silently bypassing traceability.
    for p, d in req_docs.items():
        for r in d.get("requirements", []) or []:
            if not isinstance(r, dict):
                continue
            rid = r.get("id")
            if isinstance(rid, str) and not req_to_contracts.get(rid):
                errors.append(f"UNMAPPED_REQUIREMENT {p.relative_to(ROOT)}: {rid}")

    # Check §5.4 declared coverage count.
    req54_path = ROOT / "requirements" / "5.4_encoding.yaml"
    cov_path = ROOT / "traceability" / "5.4_encoding_coverage.yaml"
    req54 = docs.get(req54_path)
    cov = docs.get(cov_path)
    if isinstance(req54, dict) and isinstance(cov, dict):
        actual = len(req54.get("requirements", []) or [])
        expected = cov.get("atomic_requirement_count_5_4")
        if expected != actual:
            errors.append(f"COVERAGE_COUNT_MISMATCH 5.4: expected={expected} actual={actual}")

    # Pre-Golden vector shape and contract linkage.
    for p, d in docs.items():
        if "verification" not in p.parts or not isinstance(d, dict):
            continue
        for group in d.get("test_groups", []) or []:
            if not isinstance(group, dict):
                continue
            cids: list[str] = []
            if isinstance(group.get("contract"), str):
                cids.append(group["contract"])
            if isinstance(group.get("contracts"), list):
                cids.extend(x for x in group["contracts"] if isinstance(x, str))
            if not cids:
                errors.append(f"TEST_GROUP_WITHOUT_CONTRACT {p.relative_to(ROOT)}: {group.get('id')}")
            for cid in cids:
                if cid not in declared["contract"]:
                    errors.append(f"TEST_GROUP_BAD_CONTRACT {p.relative_to(ROOT)}: {group.get('id')} -> {cid}")
            for vector in group.get("vectors", []) or []:
                if not isinstance(vector, dict):
                    continue
                if "expect" not in vector:
                    errors.append(f"TEST_VECTOR_WITHOUT_EXPECT {p.relative_to(ROOT)}: {vector.get('id')}")
                if "stimulus" not in vector and "configuration_constraint" not in vector:
                    errors.append(f"TEST_VECTOR_WITHOUT_STIMULUS {p.relative_to(ROOT)}: {vector.get('id')}")

    # Ontology declarations.
    ent_path = ROOT / "ontology" / "entities.yaml"
    rel_path = ROOT / "ontology" / "relations.yaml"
    ent_doc = docs.get(ent_path)
    rel_doc = docs.get(rel_path)
    entity_ids: set[str] = set()
    if isinstance(ent_doc, dict):
        for e in ent_doc.get("entities", []) or []:
            if isinstance(e, dict) and isinstance(e.get("id"), str):
                entity_ids.add(e["id"])

    # Only ALL_CAPS values used as subject/result are treated as explicit entity references.
    for p, d in {**req_docs, **contract_docs}.items():
        for obj in walk_dicts(d):
            for key in ("subject", "result"):
                if key not in obj:
                    continue
                for ref in flatten_entity_refs(obj[key]):
                    if ref not in entity_ids:
                        errors.append(f"UNDECLARED_ENTITY {p.relative_to(ROOT)}: {key}={ref}")

    if isinstance(rel_doc, dict):
        for r in rel_doc.get("relations", []) or []:
            if not isinstance(r, dict):
                continue
            subject = r.get("subject")
            if isinstance(subject, str) and ENTITY_RE.fullmatch(subject) and subject not in entity_ids:
                errors.append(f"RELATION_UNDECLARED_SUBJECT: {subject}")
            obj = r.get("object")
            if isinstance(obj, str) and ENTITY_RE.fullmatch(obj) and obj not in entity_ids:
                errors.append(f"RELATION_UNDECLARED_OBJECT: {obj}")

    print("Semantic lint — SpaceWire semantic baselines")
    print(f"YAML files parsed        : {len(yaml_files)}")
    print(f"Atomic requirements      : {len(requirement_ids)}")
    print(f"  §5.4 requirements      : {len((req54 or {}).get('requirements', []) or []) if isinstance(req54, dict) else 0}")
    print(f"Behavior contracts       : {len(contract_ids)}")
    print(f"Pre-Golden test IDs      : {len(set(test_ids))}")
    print(f"Pre-Golden invariant IDs : {len(set(invariant_ids))}")
    print(f"Ontology entities        : {len(entity_ids)}")
    print(f"Errors                   : {len(errors)}")
    print(f"Warnings                 : {len(warnings)}")

    if errors:
        print("\nFAIL")
        for e in sorted(set(errors)):
            print(f"  - {e}")
        return 1

    print("\nPASS — G1 Structural Integrity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
