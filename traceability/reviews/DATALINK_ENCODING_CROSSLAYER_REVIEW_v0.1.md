# Data Link ↔ Encoding Cross-Layer Review v0.1

Date: 2026-09-20  
Branch: `contracts/dl-encoding-cross-layer-v0.1`  
Base main: `eabd632b6e055758c371781fd10610e0c73e8d23`

## Scope

Close the cycle-level gaps between:
- `rtl_contract/5.4_encoding_rtl_contract.yaml`
- `rtl_contract/5.5_data_link_rtl_contract.yaml`

This review does not change the frozen Data Link semantic baseline. It clarifies implementation ownership, FIFO reservation/dequeue timing, and error/commit precedence.

Normative anchors:
- ECSS-E-ST-50-12C Rev.1 §5.5.4: N-Char/FCT credit accounting.
- §5.5.6: Broadcast > FCT > N-Char > Null, re-evaluated after the current character/control code.
- §5.5.8.4: on link recovery, discard the unsent remainder of the current packet through EOP/EEP.

## RTL-IF-X1 — Signal / item-kind canonicalization

Decision: CLOSED.

- Canonical TX payload signal: `enc_tx_item_data_7_0`.
- Data Link request kinds: DATA, EOP, EEP, FCT, NULL, BROADCAST_CODE.
- Raw ESC is not a Data Link request kind.
- ESC generation/consumption is Encoding-internal.
- Commit feedback kind must match the accepted external request kind.

## RTL-IF-X2 — FIFO reserve / pop / commit timing

Decision: CLOSED.

For FIFO-backed N-Chars:
1. Scheduler selects the current TX FIFO head.
2. `valid && ready` accepts the item.
3. If no same-edge commit occurs, the head becomes reserved but is not popped.
4. While reserved, that head is immutable and cannot be re-issued or skipped.
5. Matching commit pops exactly one TX FIFO entry.
6. `tx_credit--` and TX packet tracking update only on commit.
7. Same-edge accept+commit is allowed; it pops directly and never creates a persistent pending state.

Physical `tx_fifo_level` includes an accepted-but-uncommitted reserved head.

### Normal DATA example

| Event | FIFO head | Reserved | tx_credit | tx_packet_open |
|---|---|---:|---:|---:|
| before accept | DATA A | 0 | 8 | 0 |
| accept only | DATA A | 1 | 8 | 0 |
| commit DATA A | next entry | 0 | 7 | 1 |

## RTL-IF-X3 — Error vs commit + EOP flush precedence

Decision: CLOSED.

Rule: if a matching commit is asserted on the same edge as link-error entry, the commit is irrevocable and is accounted first. Recovery then uses the post-commit `tx_packet_open` state.

If no commit is asserted, the accepted-uncommitted item is flushed according to packet state:

- `tx_packet_open == 0`: cancel reservation and keep the FIFO head for retry after re-initialisation.
- `tx_packet_open == 1`: the reserved N-Char is part of the unsent current-packet remainder and is discarded exactly once.
- If the discarded reserved item is EOP/EEP, recovery spill stops at that item.
- If it is DATA, recovery continues through the first EOP/EEP.
- Pending FCT/NULL/BROADCAST_CODE is simply flushed with no FIFO or commit-side accounting.

`pending_is_terminator` is derived from pending kind == EOP/EEP; it is not an independent sticky state.

### EOP cases

| Case | Result |
|---|---|
| EOP accepted, not committed, then error while packet open | discard reserved EOP, stop spill, preserve next packet |
| EOP commit and error same edge | pop EOP, decrement credit, close packet, then enter Recovery with packet closed |
| first DATA accepted, not committed, then error while packet closed | cancel reservation; retain DATA for retry |
| DATA commit and error same edge | DATA is committed; packet becomes open; Recovery spills following remainder |

## Cross-layer invariants

- No FIFO head can be committed or popped twice.
- No committed item can be canceled by same-edge link error.
- No credit update occurs on accept alone.
- No next-packet item is consumed by current-packet recovery.
- Reserved EOP/EEP is sufficient to terminate recovery spill without an independent sticky terminator bit.
- Broadcast/FCT/N-Char/Null priority remains evaluated at each selection opportunity.

## Verification required before merge to main

- YAML parse / contract lint.
- Normal DATA: accept → reserve → commit → pop → credit decrement.
- Normal EOP: commit closes packet.
- Accepted EOP then pre-commit error: next packet preserved.
- Same-edge EOP commit + error: post-commit packet state used.
- First DATA accepted then pre-commit error while packet closed: DATA retained for retry.
- SVA candidates:
  - no duplicate pop
  - no phantom/duplicate commit
  - no old-epoch commit after flush
  - recovery never discards next packet

## Gate

Cross-layer design closure: COMPLETE on this draft branch.  
Main merge / implementation gate: HOLD until the verification items above pass and the branch is reviewed against the authoritative contracts.
