#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
vectors = (ROOT / "verification/pre_golden/5.4_encoding_vectors.yaml").read_text(encoding="utf-8")
coverage = (ROOT / "verification/golden/5.4_encoding_validation_coverage.yaml").read_text(encoding="utf-8")
tests = (ROOT / "verification/golden/test_encoding_golden.py").read_text(encoding="utf-8")

all_ids = set(re.findall(r"\bTV-ENC-(?:CHAR|CTRL|CODE|PARITY|DS|NULL|ERR|DISC|RATE|IF)-\d{3}\b", vectors))
mapped = set(re.findall(r"\bTV-ENC-(?:CHAR|CTRL|CODE|PARITY|DS|NULL|ERR|DISC|RATE|IF)-\d{3}\b", coverage))
methods = set(re.findall(r"^\s+def (test_[A-Za-z0-9_]+)\(", tests, flags=re.M))
coverage_methods = set(re.findall(r"^  (test_[A-Za-z0-9_]+):$", coverage, flags=re.M))

missing = sorted(all_ids - mapped)
extra = sorted(mapped - all_ids)
bad_methods = sorted(coverage_methods - methods)

print(f"Pre-Golden vectors : {len(all_ids)}")
print(f"Mapped vectors     : {len(mapped)}")
print(f"Validation methods : {len(methods)}")
if missing or extra or bad_methods:
    print("FAIL")
    for x in missing: print("  missing mapping:", x)
    for x in extra: print("  unknown vector:", x)
    for x in bad_methods: print("  missing test method:", x)
    raise SystemExit(1)
print("PASS — Golden validation coverage closure")
