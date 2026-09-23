# CURRENT_HANDOVER — SpaceWire Spec2RTL

**Date:** 2026-09-24  
**Repository:** `hyojin33kim/spacewire_gpt`  
**Engineering Source of Truth:** GitHub `main` for approved baseline; active integration evidence is on the working branch below.  
**Approved baseline HEAD:** `main@4a1465b085d204b115bf5b1ea8cb99fad675db70`  
**Current working branch:** `verify/network-router-closure-v0.1`  
**State verified through branch commit:** `bce8ce71ba6efab2cab758b838999009f9c5a53e`  
**Integration PR:** #3 — *Verify Network Router RTL contract design closure* — Draft  
**Current next gate:** formal acceptance of the complete Network/Router review package.

> This file is the compact restart point for a new Chat. If this file, Notion, and Git artifacts disagree, verify the current Git branch/PR first. Do not infer approval from a design or verification PASS.

---

## 1. Project objective

Build a trustworthy SpaceWire implementation flow from ECSS evidence to FPGA RTL:

```text
Spec Evidence
→ Ontology
→ Atomic Requirement
→ Behavior Contract
→ Pre-Golden vectors / invariants
→ Semantic Freeze
→ Golden Model
→ Golden Validation
→ RTL Contract
→ RTL
→ RTL-vs-Golden differential verification + SVA
```

Authoritative specification:

```text
ECSS-E-ST-50-12C Rev.1
15 May 2019
```

Golden Model must remain implementation-independent. AI must not silently resolve normative ambiguity.

---

## 2. Current approved / working state

| Layer | Semantic / Golden | RTL Contract / Gate | RTL |
|---|---|---|---|
| Encoding §5.4 | Frozen / Golden PASS | `draft_blocked`; PHY feasibility blockers remain | Not authorized |
| Data Link §5.5 | `semantic-datalink-v0.1.1` / Golden PASS | reviewed baseline; X1/X2/X3 closure verified on integration branch | Not started |
| Network §5.6 | Frozen / Golden PASS | design closure + verification candidate complete; not yet `Reviewed` | Not started |
| Router | Frozen / Golden PASS | design closure + verification candidate complete; not yet `Reviewed` | Not started |

Important governance distinction:

```text
main
= approved engineering baseline

verify/network-router-closure-v0.1
= latest integration / review candidate
= NOT approved baseline until review gate + merge
```

---

## 3. Decisions already approved

### Data Link / Encoding boundary

- Option B: Encoding **accept != commit**.
- FIFO-backed N-Char: accept reserves current FIFO head; commit pops exactly one and performs credit/packet accounting.
- Max accepted-but-uncommitted item: 1.
- Same-edge commit + link error: matching commit wins irrevocably; recovery uses post-commit packet state.
- Raw ESC is Encoding-internal only.
- Canonical RX payload signal: `enc_rx_item_data_7_0`.
- Data Link owns recovery direct-drain.
- TX/RX FIFO = 128; MAX_CREDIT = 56.

### Network / Router architecture

- 4 external ports + Port 0.
- Reuse existing Data Link FIFOs.
- Packet-level rotating arbitration; fairness is normative, round-robin only deterministic reference trace.
- Output ownership held until local terminal serial completion.
- Router timeout → Data Link abort → synthetic EEP via normal credited path; no link reset.
- Port 0 project-local `SPCFG-v0.1`; path access only; shadow + COMMIT route table.
- Broadcast: per-port capture, one semantic event/core-cycle, priority TC > ACK > INT, non-silent overflow.
- Multicast: all-output atomic allocation / handoff; selected mask frozen; fail-whole on member failure.

### Owner-map decisions

Applied approved ownership dispositions:
- `SPW-5.6.4.1-a`: Router primary; DataLink + Endpoint collaborators.
- `SPW-5.6.7-a`: ConfigurationManagement primary; DataLink + Encoding + Physical collaborators.
- 18 shared Time-code / Distributed Interrupt requirements: existing primary owner retained; Router collaborator added.
- `SPW-RTR-5.6.9-b`: ConfigurationManagement primary retained; Physical collaborator added.

Full owner-map result:
- Network: 123 requirements
- Router: 101 requirements
- Total: **224/224**
- Technical review: complete
- Approved dispositions applied: **21**
- Unresolved owner findings: **0**

### Requirement modality policy

Approved and applied to 53 audited Network/Router rows:
- `level` stores exact normative modality only: `SHALL / SHOULD / MAY / CAN / NOTE`.
- Applicability / optionality is separate in `applicability`.
- Parent normative inheritance is explicit via `modality_origin`.
- Cardinality is separate, e.g. `cardinality: "0..1"`.
- Existing feature-profile `selected` choices are preserved.
- No intentional Golden behavior change.

---

## 4. Verification evidence at current candidate

Latest verified integration evidence before this handover:

```text
Semantic structural lint             PASS — 0 errors / 0 warnings
Exact requirement modality lint      PASS — 0 non-canonical levels
Owner-map structural closure         PASS — 224/224
Cross-layer + Network/Router tests   PASS — 31 tests
Golden regression                    PASS — 34 tests
Golden vectors                       ENC 45/45
                                     DL  46/46
                                     NET 29/29
                                     RTR 34/34
Protocol invariant mapping           PASS — 24/24
```

PR #3 consolidates the needed current evidence from draft PR #1 and #2. If PR #3 is selected for final integration, PR #1/#2 should not be merged independently; close them as superseded after integration.

---

## 5. Key evidence artifacts to read first

```text
traceability/CURRENT_HANDOVER.md
traceability/NETWORK_ROUTER_MERGE_READY_CANDIDATE_v0.1.md
traceability/NETWORK_ROUTER_OWNER_MAP_TECHNICAL_REVIEW_v0.1.md
traceability/NETWORK_ROUTER_MODALITY_NORMALIZATION_v0.1.md
traceability/NETWORK_ROUTER_VERIFICATION_EVIDENCE_v0.1.md
traceability/RTL_CONTRACT_FREEZE_CANDIDATE_v0.1.md
```

RTL contracts:

```text
rtl_contract/5.4_encoding_rtl_contract.yaml
rtl_contract/5.5_data_link_rtl_contract.yaml
rtl_contract/5.6_network_ownership_contract.yaml
rtl_contract/5.6_router_rtl_contract.yaml
rtl_contract/5.6_port0_configuration_rtl_contract.yaml
rtl_contract/5.6_broadcast_multicast_rtl_contract.yaml
```

Notion:
- `업무 → Spacewire 개념 → 00. Decision Log` — rationale / decisions
- `업무 → Spacewire 개념 → 01. Current State & Handover` — current operational state

---

## 6. Remaining explicit gates

Current sequence from here:

```text
CURRENT
  ↓
1. Formal acceptance of complete Network/Router review package
  ↓
2. Gate-only commit: Network/Router status → REVIEWED
  ↓
3. Sync current main history into integration branch
  ↓
4. Full final CI
  ↓
5. PR #3 → main using merge commit
  ↓
6. main post-merge clean regression
  ↓
7. Close PR #1/#2 as superseded
  ↓
8. Explicit RTL implementation authorization
  ↓
9. RTL implementation + RTL-vs-Golden + SVA
```

### Requires explicit user approval

Do **not** perform these merely because CI is green:
- formal acceptance / `Reviewed` gate transition,
- merge to `main`,
- change `RTL_implementation_allowed` to true,
- start new RTL implementation / architecture changes,
- silently resolve a new semantic ambiguity.

### May proceed without approval

- read/compare repo artifacts,
- run regression, lint, structural checks,
- add verification that does not change semantics,
- prepare review/evidence reports,
- fix tooling false positives without changing engineering rules,
- prepare candidate diffs without applying approval-gated status changes.

---

## 7. Independent Encoding PHY blockers

Network/Router review closure does **not** close Encoding PHY feasibility.

Still separate:
- Zynq-7020 recovered-edge implementation feasibility,
- programmable sampling delay / delay taps,
- 200 Mbps timing closure,
- Data/Strobe skew/jitter handling,
- CDC/reset when recovered edge stops,
- AXI4-Lite/register CDC boundary.

Do not claim the entire protocol RTL gate is open merely because Network/Router review passes.

---

## 8. Next Chat bootstrap

Use this as the first message in a new Chat:

> Continue the SpaceWire Spec2RTL project from GitHub `hyojin33kim/spacewire_gpt`. First read `traceability/CURRENT_HANDOVER.md` on branch `verify/network-router-closure-v0.1`, then verify the current branch HEAD, PR #3, and the evidence artifacts it references. Also check Notion `업무 → Spacewire 개념 → 00. Decision Log` and `01. Current State & Handover`. GitHub artifacts take precedence over conversational summaries. The next task is the **formal Network/Router review-package gate review**: check only for remaining contradictions, blockers, missing evidence, or stale gate fields and return a PASS/HOLD evidence assessment. Do not set `Reviewed`, merge to `main`, or start RTL without explicit approval.

---

## 9. One-line state

> **Network/Router design, owner map, modality normalization, directed contract verification, Golden regression, and trace checks are complete as an integration candidate; the next step is formal review acceptance, not RTL implementation.**
