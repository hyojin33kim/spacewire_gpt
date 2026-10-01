# Network / Router Requirement Modality Audit v0.1 — Resolved

Date: 2026-09-23  
Scope: `requirements/5.6_network.yaml`, `requirements/6.1_network_service.yaml`, `requirements/5.6_router.yaml`

## Finding

Project policy requires exact source modalities in the requirement artifact:

`SHALL / SHOULD / MAY / CAN / NOTE`

The audited requirement files contain **53** rows whose `level` field encodes applicability/cardinality together with the modality.

Counts:

- `OPTIONAL_CARDINALITY`: 2
- `SHALL_CONDITIONAL`: 32
- `SHALL_IF_PRESENT`: 2
- `SHALL_IF_SUPPORTED`: 8
- `SHALL_OPTIONAL`: 5
- `SHOULD_CONDITIONAL`: 4

Examples:
- `SHALL_OPTIONAL` represents source wording such as “shall be optionally implemented”.
- `SHALL_CONDITIONAL` / `SHALL_IF_SUPPORTED` embed applicability in `level`.
- `SHOULD_CONDITIONAL` embeds a condition in `level`.
- `OPTIONAL_CARDINALITY` represents cardinality inherited under a parent SHALL.

## Why this matters

This does **not** by itself prove that the frozen behavior is wrong. The selected feature/profile fields often preserve the intended applicability. However, the representation violates the project's traceability rule because `level` is no longer an exact copy of the normative modality.

A robust normalization would separate:

```yaml
level: SHALL
applicability: <condition / optional feature>
cardinality: <if applicable>
selected: <profile decision>
```

instead of inventing a composite level.

## Gate impact

No semantic artifact was changed because normalizing frozen requirement rows can affect traceability, manifests and baseline hashes and therefore requires an explicit semantic-baseline decision plus regression.

Recommended treatment before final RTL sign-off:
1. approve normalization policy,
2. convert composite levels without changing behavior,
3. regenerate/recheck traceability,
4. re-run Semantic Lint and Golden regression,
5. record whether semantic baseline version changes or only representation metadata changes.

## Non-canonical rows

- `SPW-5.6.6-h` — clause 5.6.6.h — current level `SHALL_OPTIONAL`
- `SPW-5.6.5.1-b` — clause 5.6.5.1.b — current level `SHOULD_CONDITIONAL`
- `SPW-5.6.5.6-a` — clause 5.6.5.6.a — current level `SHALL_CONDITIONAL`
- `SPW-5.6.5.6-d` — clause 5.6.5.6.d — current level `SHOULD_CONDITIONAL`
- `SPW-5.6.5.6-h` — clause 5.6.5.6.h — current level `SHOULD_CONDITIONAL`
- `SPW-5.6.6-k` — clause 5.6.6.k — current level `SHALL_CONDITIONAL`
- `SPW-5.6.8.10-a` — clause 5.6.8.10.a — current level `SHALL_OPTIONAL`
- `SPW-5.6.10-e` — clause 5.6.10.e — current level `SHALL_OPTIONAL`
- `SPW-RTR-5.6.8.1-b5` — clause 5.6.8.1.b.5 — current level `OPTIONAL_CARDINALITY`
- `SPW-RTR-5.6.8.1-b6` — clause 5.6.8.1.b.6 — current level `OPTIONAL_CARDINALITY`
- `SPW-RTR-5.6.8.1-c` — clause 5.6.8.1.c — current level `SHALL_IF_PRESENT`
- `SPW-RTR-5.6.8.1-d` — clause 5.6.8.1.d — current level `SHALL_IF_PRESENT`
- `SPW-RTR-5.6.8.9-a` — clause 5.6.8.9.a — current level `SHALL_OPTIONAL`
- `SPW-RTR-5.6.8.9-b` — clause 5.6.8.9.b — current level `SHALL_IF_SUPPORTED`
- `SPW-RTR-5.6.8.9-c` — clause 5.6.8.9.c — current level `SHALL_IF_SUPPORTED`
- `SPW-RTR-5.6.8.10-b` — clause 5.6.8.10.b — current level `SHALL_OPTIONAL`
- `SPW-RTR-5.6.8.10-c1` — clause 5.6.8.10.c.1 — current level `SHALL_IF_SUPPORTED`
- `SPW-RTR-5.6.8.10-c2` — clause 5.6.8.10.c.2 — current level `SHALL_IF_SUPPORTED`
- `SPW-RTR-5.6.8.10-c3` — clause 5.6.8.10.c.3 — current level `SHALL_IF_SUPPORTED`
- `SPW-RTR-5.6.8.10-c4` — clause 5.6.8.10.c.4 — current level `SHALL_IF_SUPPORTED`
- `SPW-RTR-INT-RELAY` — clause 5.6.5.5 — current level `SHALL_IF_SUPPORTED`
- `SPW-RTR-ACK-RELAY` — clause 5.6.5.7 — current level `SHALL_IF_SUPPORTED`
- `SPW-RTR-5.6.4.6-a1` — clause 5.6.4.6.a.1 — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.4.6-a2` — clause 5.6.4.6.a.2 — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.5-a` — clause 5.6.5.5.a — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.5-b` — clause 5.6.5.5.b — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.5-c` — clause 5.6.5.5.c — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.5-d` — clause 5.6.5.5.d — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.5-f` — clause 5.6.5.5.f — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.5-g` — clause 5.6.5.5.g — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.5-h` — clause 5.6.5.5.h — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.5-i` — clause 5.6.5.5.i — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.5-j` — clause 5.6.5.5.j — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.5-k` — clause 5.6.5.5.k — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.5-l1` — clause 5.6.5.5.l.1 — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.5-l2` — clause 5.6.5.5.l.2 — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.5-l3a` — clause 5.6.5.5.l.3.a — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.5-l3b` — clause 5.6.5.5.l.3.b — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.5-l3c` — clause 5.6.5.5.l.3.c — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.5-l4` — clause 5.6.5.5.l.4 — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.5-m` — clause 5.6.5.5.m — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.7-a` — clause 5.6.5.7.a — current level `SHOULD_CONDITIONAL`
- `SPW-RTR-5.6.5.7-b` — clause 5.6.5.7.b — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.7-c` — clause 5.6.5.7.c — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.7-d` — clause 5.6.5.7.d — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.7-e` — clause 5.6.5.7.e — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.7-f` — clause 5.6.5.7.f — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.7-g1` — clause 5.6.5.7.g.1 — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.7-g2a` — clause 5.6.5.7.g.2.a — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.7-g2b` — clause 5.6.5.7.g.2.b — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.7-g2c` — clause 5.6.5.7.g.2.c — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.7-g3` — clause 5.6.5.7.g.3 — current level `SHALL_CONDITIONAL`
- `SPW-RTR-5.6.5.7-h` — clause 5.6.5.7.h — current level `SHALL_CONDITIONAL`


## Resolution

The normalization policy was approved and implemented on 2026-09-24. See `NETWORK_ROUTER_MODALITY_NORMALIZATION_v0.1.md`. This audit is retained as the pre-normalization finding record.
