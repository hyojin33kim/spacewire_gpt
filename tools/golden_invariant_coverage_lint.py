#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ROOT / "verification/pre_golden/5.5_data_link_invariants.yaml",
    ROOT / "verification/pre_golden/5.6_network_invariants.yaml",
    ROOT / "verification/pre_golden/5.6_router_invariants.yaml",
]
COVERAGE = ROOT / "verification/golden/protocol_invariant_validation_coverage.yaml"
TESTS = ROOT / "verification/golden/test_protocol_invariants.py"

source_text = "\n".join(p.read_text(encoding="utf-8") for p in SOURCES)
coverage = COVERAGE.read_text(encoding="utf-8")
tests = TESTS.read_text(encoding="utf-8")

all_ids = set(re.findall(r"\bINV-(?:DL|NET|RTR)-\d{3}\b", source_text))
mapped = set(re.findall(r"\bINV-(?:DL|NET|RTR)-\d{3}\b", coverage))
methods = set(re.findall(r"^\s+def (test_[A-Za-z0-9_]+)\(", tests, flags=re.M))
coverage_methods = set(re.findall(r"^  (test_[A-Za-z0-9_]+):$", coverage, flags=re.M))

errors = []
for x in sorted(all_ids - mapped):
    errors.append(f"missing invariant mapping: {x}")
for x in sorted(mapped - all_ids):
    errors.append(f"unknown invariant: {x}")
for x in sorted(coverage_methods - methods):
    errors.append(f"missing invariant test method: {x}")

print(f"Protocol invariants : {len(all_ids)}")
print(f"Mapped invariants   : {len(mapped)}")
print(f"Validation methods  : {len(methods)}")
if errors:
    print("FAIL")
    for e in errors:
        print("  -", e)
    raise SystemExit(1)
print("PASS — protocol invariant validation coverage closure")
