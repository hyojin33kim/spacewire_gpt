# Network / Router Contract Verification Evidence v0.1

Date: 2026-09-23  
Branch: `verify/network-router-closure-v0.1`  
Design source branch: `contracts/network-router-after-dl-closure-v0.1`  
Verification evidence commit before this report: `4c8724b11e9393565ebbb6b17161966a4e9ab395`  
GitHub Actions run: `35818139440`

## Scope

This report records verification that can be completed without changing the already-selected architecture or semantic baseline.

It does **not**:
- mark Network/Router contracts Reviewed,
- change Frozen/Reviewed engineering gates,
- authorize RTL implementation,
- change requirement ownership,
- merge any branch to `main`.

Those actions remain approval-gated.

## Automated verification result

All executable checks in run `35818139440` passed.

| Check | Result |
|---|---|
| Semantic-lint regex unit tests | PASS — 3 tests |
| Semantic structural lint | PASS — 0 errors / 0 warnings |
| Network/Router owner-map structural closure | PASS — 224/224 unique allocations |
| RTL contract directed executable checks | PASS — 25 tests |
| Golden regression | PASS — 34 tests |
| Golden vector closure | PASS — Encoding 45/45, Data Link 46/46, Network 29/29, Router 34/34 |
| Protocol invariant closure | PASS — 24/24 |

Semantic structural lint parsed 59 YAML files and retained the existing 470 atomic requirements / 9 behavior contracts baseline.

## Contract-directed evidence covered

### Data Link ↔ Encoding X1/X2/X3
- canonical TX boundary names and raw-ESC ownership,
- one accepted-but-uncommitted item maximum,
- FIFO head accept → reserve → commit → pop/account,
- pre-commit EOP + link error preserves following packet,
- same-edge EOP commit + error uses post-commit packet state,
- first DATA pre-commit error retains FIFO head for retry,
- duplicate/stale commit is rejected.

A naming-only consistency defect was corrected:
`enc_rx_data_7_0` → `enc_rx_item_data_7_0` in the Data Link contract, matching the already-selected Encoding boundary name.

### Router output ownership / timeout
Executable contract checks confirm the selected rules:
- terminal FIFO acceptance does not release output ownership,
- terminal Encoding commit does not release output ownership,
- local terminal serial completion releases ownership,
- timeout abort retains ownership until `net_tx_abort_done`,
- link-error termination still blocks a new packet until recovery/new-packet readiness,
- timeout expiry is strictly greater than the programmed period,
- same-edge DATA progress or terminal handoff suppresses timeout expiry.

### Port 0
Executable checks cover:
- path-only Port-0 access,
- logical access forbidden,
- malformed/EEP request has no side effect,
- one-entry response buffer contract,
- route-table shadow write is invisible until COMMIT,
- same-edge lookup sees the pre-edge active route entry.

### Broadcast
The selected capacity argument is executable and self-consistent:
- 100 MHz core,
- 200 Mbit/s maximum link,
- 14 serial bits per broadcast code,
- same-port minimum spacing = 70 ns = 7 core cycles,
- four simultaneous external-port captures drain in 4 cycles,
- egress priority = TIME_CODE > INTERRUPT_ACK > INTERRUPT,
- silent overflow is forbidden.

### Multicast
Executable checks cover:
- all-selected-output atomic allocation/handoff,
- no subset transfer,
- selected mask frozen for the active packet,
- fail-whole active multicast policy,
- group release waits for all selected output ownerships to terminate.

## Owner-map structural review

The allocation artifact contains exactly:

- Network: 123 requirements
  - `requirements/5.6_network.yaml`: 83
  - `requirements/6.1_network_service.yaml`: 40
- Router: 101 requirements
- Total: 224/224 unique rows

Primary-owner distribution:
- Endpoint: 107
- Router: 99
- SystemIntegration: 11
- ConfigurationManagement: 7

Group-level review is internally coherent for packet, host-service, time-code, interrupt, routing, timeout, management, relay, and system-obligation groups.

## Manual owner-map findings — approved dispositions applied

### OWN-RVW-001 — SPW-5.6.4.1-a

Approved disposition:
- primary owner remains **Router**,
- collaborators are **DataLink + Endpoint**,
- no split derived requirement is introduced in v0.1.

Rationale:
The source requirement spans nodes and routers. Router remains the single accountable primary owner in this owner map, while Endpoint now makes the node-side applicability explicit.

### OWN-RVW-002 — SPW-5.6.7-a

Approved disposition:
- primary owner remains **ConfigurationManagement**,
- collaborators are **DataLink + Encoding + Physical**.

The ownership taxonomy now includes an explicit **Physical** source-layer entry. This exposes the source of Physical-layer management parameters without implying that Network owns the physical implementation.

## Findings reviewed and not considered blockers

Heuristic review also flagged configuration-node wording in:
- `SPW-RTR-5.6.8.1-b4`
- `SPW-RTR-5.6.8.1-e`

These are Router-internal Port-0 configuration-node requirements and already include ConfigurationManagement collaboration; Endpoint ownership is not required by their current contract boundary.

## Remaining gate

OWN-RVW-001 and OWN-RVW-002 are resolved by user-approved ownership dispositions.

Remaining approval-gated items are:
1. complete/accept the full 224-row manual owner-map review,
2. mark Network/Router contracts Reviewed if accepted,
3. authorize merge sequence to `main`,
4. authorize RTL implementation.

The contract files intentionally retain:
- `status: design_closed_verification_pending`,
- `reviewed: false`,
- `RTL_implementation_allowed: false`.
