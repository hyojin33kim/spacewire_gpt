# Encoding semantic baseline v0.1 — Gate Review

Review basis: ECSS-E-ST-50-12C Rev.1 source plus current repository artifacts.
Result is intentionally limited to PASS/FAIL and freeze-blocking issues.

| Gate | Result | Blocking issue |
|---|---|---|
| G1 Structural Integrity | PASS | None. GitHub Actions semantic_lint: 17 YAML, 106 requirements, 56 §5.4 requirements, 6 contracts, 44 test IDs, 11 invariants, 33 ontology entities; 0 errors / 0 warnings. |
| G2 Spec Fidelity | FAIL | **B1:** §5.4.4.e reset-delay range is encoded backwards in current contract/vector (min=500 ns, max=fastest-period). Source only says delay is *between* those endpoints; for >2 Mbps the fastest bit period is <500 ns. **B2:** Normal Data-Strobe RX decoding behavior required by §5.2.4.a.2 is not explicitly represented in the behavior contract. |
| G3 Executability / Pre-Golden Verification | FAIL | **B3:** BC-ENC-RATE-001 has no pre-Golden test group. **B4:** key bit-level oracle vectors are still symbolic/property-only (parity example, First Null/Null detection) rather than concrete expected bit sequences, so they are not yet an independent executable oracle. **B5:** normal DS decode path has no pre-Golden vector. |
| G4 Boundary / Ownership | FAIL | **B6:** §5.4.4.e timing endpoint ownership cannot be frozen until B1 is resolved; normal DS decode must be classified and specified as protocol semantic/derived semantic before RTL choices are introduced. |
| G5 Independent Challenge | FAIL | The independent source-vs-artifact challenge found B1–B6; therefore semantic-encoding-v0.1 must not be frozen yet. |

## Freeze decision

**NO-FREEZE** until B1–B6 are closed and G1 is rerun after corrections.

## Mandatory downstream order

semantic-encoding-v0.1 freeze
→ Golden Model
→ Golden Model validation against pre-Golden vectors/invariants
→ reviewed RTL Contract
→ RTL
→ RTL-vs-Golden differential verification + assertions
