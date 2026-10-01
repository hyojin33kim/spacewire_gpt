# Network / Router Requirement Modality Normalization v0.1

Date: 2026-09-24  
Branch: `verify/network-router-closure-v0.1`  
Source: ECSS-E-ST-50-12C Rev.1

## Decision applied

The approved normalization policy separates normative strength from applicability, optionality and cardinality.

For all 53 audited rows:
- `level` contains only the source normative modality (`SHALL` or `SHOULD` for these clauses).
- `applicability` records the source condition / optional feature context.
- `modality_origin` records whether the modality appears directly in the clause or is inherited from a parent normative statement.
- `cardinality` is separate where the source enumerates “zero or one”.
- existing `selected` feature-profile choices are unchanged.

## Source cross-check

The normalization was checked clause-by-clause against the ECSS text for:
- 5.6.4 time-codes,
- 5.6.5 distributed interrupts,
- 5.6.6 nodes,
- 5.6.8 routing / group adaptive routing / multicast,
- 5.6.10 network.

Examples:
- 5.6.4.1.b uses **shall** with applicability “time-codes not supported”.
- 5.6.5.1.b uses **should** with applicability “distributed interrupts not supported”.
- 5.6.8.10.b uses **shall** and describes multicast as optional.
- 5.6.8.10.c.1-c.4 inherit **shall** from 5.6.8.10.c.
- 5.6.8.1.b.5-b.6 inherit **shall** from “A SpaceWire routing switch shall comprise” and carry cardinality `0..1`.

## Counts

- `SHALL_OPTIONAL` → exact `SHALL`: 5
- `SHOULD_CONDITIONAL` → exact `SHOULD`: 4
- `SHALL_CONDITIONAL` → exact `SHALL`: 32
- `OPTIONAL_CARDINALITY` → inherited `SHALL` + cardinality: 2
- `SHALL_IF_PRESENT` → exact `SHALL` + applicability: 2
- `SHALL_IF_SUPPORTED` → exact `SHALL` + applicability: 8

Total: **53**

## Behavioral impact

Intended semantic behavior change: **none**.

This is a requirement-representation normalization. Existing feature-profile selections, behavior contracts, Golden vectors and Golden models remain unchanged. CI/regression must confirm that claim before merge.

## Derived aggregate rows

`SPW-RTR-INT-RELAY` and `SPW-RTR-ACK-RELAY` are project helper summaries spanning multiple normative subclauses. Their level is normalized to `SHALL`, with `modality_origin: derived_from_multiple_SHALL_subclauses` so they are not misrepresented as a verbatim atomic source sentence.
