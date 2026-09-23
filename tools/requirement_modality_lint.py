#!/usr/bin/env python3
from pathlib import Path
import sys
import yaml

ROOT=Path(__file__).resolve().parents[1]
ALLOWED={"SHALL","SHOULD","MAY","CAN","NOTE"}
errors=[]
rows=0
for path in sorted((ROOT/"requirements").glob("*.yaml")):
    doc=yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for req in doc.get("requirements",[]) or []:
        if not isinstance(req,dict):
            continue
        rows+=1
        level=req.get("level")
        if level not in ALLOWED:
            errors.append(f"{path.relative_to(ROOT)} {req.get('id')}: non-canonical level={level!r}")

print(f"Requirement rows checked : {rows}")
print(f"Non-canonical levels     : {len(errors)}")
if errors:
    print("FAIL")
    for e in errors:
        print("  -",e)
    raise SystemExit(1)
print("PASS — requirement levels use exact canonical modalities only")
