#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "traceability" / "network_router_owner_map_v0.1.json"
NETWORK_REQ = ROOT / "requirements" / "5.6_network.yaml"
ROUTER_REQ = ROOT / "requirements" / "5.6_router.yaml"

ALLOWED_OWNERS = {
    "Endpoint",
    "DataLink",
    "Router",
    "ConfigurationManagement",
    "SystemIntegration",
    "Encoding",
}


def req_ids(path: Path) -> set[str]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {
        row["id"]
        for row in doc.get("requirements", [])
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }


def main() -> int:
    data = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    rows = data.get("requirements", [])
    errors: list[str] = []

    network_ids = req_ids(NETWORK_REQ)
    router_ids = req_ids(ROUTER_REQ)
    expected = network_ids | router_ids
    mapped = [r.get("requirement_id") for r in rows if isinstance(r, dict)]
    mapped_set = {x for x in mapped if isinstance(x, str)}

    declared = data.get("counts", {})
    if declared.get("network") != len(network_ids):
        errors.append(f"declared network count {declared.get('network')} != {len(network_ids)}")
    if declared.get("router") != len(router_ids):
        errors.append(f"declared router count {declared.get('router')} != {len(router_ids)}")
    if declared.get("allocated") != len(rows):
        errors.append(f"declared allocated count {declared.get('allocated')} != {len(rows)}")
    if len(rows) != len(expected):
        errors.append(f"row count {len(rows)} != expected requirements {len(expected)}")

    duplicates = sorted(k for k, n in Counter(mapped).items() if k and n > 1)
    for rid in duplicates:
        errors.append(f"duplicate allocation: {rid}")

    for rid in sorted(expected - mapped_set):
        errors.append(f"missing allocation: {rid}")
    for rid in sorted(mapped_set - expected):
        errors.append(f"unknown allocation: {rid}")

    source_counts = Counter()
    primary_counts = Counter()
    group_counts = Counter()

    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"row {i}: not an object")
            continue
        rid = row.get("requirement_id")
        src = row.get("source_file")
        source_counts[src] += 1

        expected_src = (
            "requirements/5.6_network.yaml"
            if rid in network_ids
            else "requirements/5.6_router.yaml"
            if rid in router_ids
            else None
        )
        if src != expected_src:
            errors.append(f"{rid}: source_file={src!r}, expected={expected_src!r}")

        owner = row.get("primary_owner")
        primary_counts[owner] += 1
        if owner not in ALLOWED_OWNERS:
            errors.append(f"{rid}: invalid primary_owner {owner!r}")

        collaborators = row.get("collaborating_owners", [])
        if not isinstance(collaborators, list):
            errors.append(f"{rid}: collaborating_owners is not a list")
        else:
            if len(collaborators) != len(set(collaborators)):
                errors.append(f"{rid}: duplicate collaborating owner")
            for x in collaborators:
                if x not in ALLOWED_OWNERS:
                    errors.append(f"{rid}: invalid collaborating owner {x!r}")

        group = row.get("contract_group")
        group_counts[group] += 1
        if not isinstance(group, str) or not group:
            errors.append(f"{rid}: missing contract_group")
        if not row.get("source_behavior"):
            errors.append(f"{rid}: missing source_behavior")
        if not row.get("allocation_status"):
            errors.append(f"{rid}: missing allocation_status")
        if not row.get("verification_status"):
            errors.append(f"{rid}: missing verification_status")
        if not row.get("evidence_status"):
            errors.append(f"{rid}: missing evidence_status")

    print("Network/Router owner-map structural closure")
    print(f"Network requirements : {len(network_ids)}")
    print(f"Router requirements  : {len(router_ids)}")
    print(f"Mapped rows          : {len(rows)}")
    print(f"Unique mapped IDs    : {len(mapped_set)}")
    print("Primary owners       :", dict(sorted(primary_counts.items(), key=lambda x: str(x[0]))))
    print("Contract groups      :", len(group_counts))
    print(f"Errors               : {len(errors)}")

    if errors:
        print("FAIL")
        for e in errors:
            print("  -", e)
        return 1

    print("PASS — 224/224 structural allocation closure; semantic/manual disposition remains a review gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
