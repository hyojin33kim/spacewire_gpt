#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

BASELINES = [
    {
        "name": "Encoding",
        "vectors": "verification/pre_golden/5.4_encoding_vectors.yaml",
        "coverage": "verification/golden/5.4_encoding_validation_coverage.yaml",
        "tests": "verification/golden/test_encoding_golden.py",
        "id_re": r"TV-ENC-(?:CHAR|CTRL|CODE|PARITY|DS|NULL|ERR|DISC|RATE|IF)-\d{3}",
    },
    {
        "name": "Data Link",
        "vectors": "verification/pre_golden/5.5_data_link_vectors.yaml",
        "coverage": "verification/golden/5.5_data_link_validation_coverage.yaml",
        "tests": "verification/golden/test_data_link_golden.py",
        "id_re": r"TV-DL-\d{3}",
    },
    {
        "name": "Network",
        "vectors": "verification/pre_golden/5.6_network_vectors.yaml",
        "coverage": "verification/golden/5.6_network_validation_coverage.yaml",
        "tests": "verification/golden/test_network_golden.py",
        "id_re": r"TV-NET-\d{3}",
    },
    {
        "name": "Router",
        "vectors": "verification/pre_golden/5.6_router_vectors.yaml",
        "coverage": "verification/golden/5.6_router_validation_coverage.yaml",
        "tests": "verification/golden/test_router_golden.py",
        "id_re": r"TV-RTR-\d{3}",
    },
]


def check_baseline(cfg: dict[str, str]) -> list[str]:
    vectors = (ROOT / cfg["vectors"]).read_text(encoding="utf-8")
    coverage = (ROOT / cfg["coverage"]).read_text(encoding="utf-8")
    tests = (ROOT / cfg["tests"]).read_text(encoding="utf-8")
    pattern = re.compile(rf"\b(?:{cfg['id_re']})\b")

    all_ids = set(pattern.findall(vectors))
    mapped = set(pattern.findall(coverage))
    methods = set(re.findall(r"^\s+def (test_[A-Za-z0-9_]+)\(", tests, flags=re.M))
    coverage_methods = set(
        re.findall(r"^  (test_[A-Za-z0-9_]+):$", coverage, flags=re.M)
    )

    errors: list[str] = []
    missing = sorted(all_ids - mapped)
    extra = sorted(mapped - all_ids)
    bad_methods = sorted(coverage_methods - methods)

    print(
        f"{cfg['name']:<10} vectors={len(all_ids):>3} "
        f"mapped={len(mapped):>3} methods={len(methods):>2}"
    )
    for x in missing:
        errors.append(f"{cfg['name']}: missing mapping {x}")
    for x in extra:
        errors.append(f"{cfg['name']}: unknown vector {x}")
    for x in bad_methods:
        errors.append(f"{cfg['name']}: missing test method {x}")
    if not all_ids:
        errors.append(f"{cfg['name']}: no pre-Golden vectors found")
    return errors


def main() -> int:
    errors: list[str] = []
    print("Golden validation coverage closure")
    for cfg in BASELINES:
        errors.extend(check_baseline(cfg))

    if errors:
        print("FAIL")
        for error in errors:
            print("  -", error)
        return 1

    print("PASS — all semantic baselines have complete pre-Golden vector mappings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
